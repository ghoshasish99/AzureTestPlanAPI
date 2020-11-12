import requests
import json
import jsonpath
from datetime import datetime

organization = "YourOrganizationName"
project = "YourProjectName"
pat = "YourPAT"
planName = "YourPlanName"
suitename = "YourSuiteName"
testcaseName = "YourTestCaseName"
status = "passed"

def get_testplan_details ():
    try:
        url = "https://dev.azure.com/" + organization + "/"+ project + "/_apis/test/plans?api-version=5.0"
        response = requests.get(url=url, auth = ('', pat))
        reponsejson = json.loads(response.text)
        planID = jsonpath.jsonpath(reponsejson,"$.value.[?(@.name == '" + planName + "')].id")[0]
        suiteID = jsonpath.jsonpath(reponsejson,"$.value.[?(@.name == '" + planName + "')].rootSuite.id")[0]
        return str(planID), suiteID
    except Exception as e :
        print('Something went wrong in fetching Test Plan ID :'+str(e))

def get_testsuite_details ():
    try:
        plandetails = get_testplan_details()
        url = "https://dev.azure.com/" + organization + "/"+ project + "/_apis/test/plans/"+ plandetails[0] + "/suites?api-version=5.0"
        response = requests.get(url=url, auth = ('', pat))
        reponsejson = json.loads(response.text)
        suiteID = jsonpath.jsonpath(reponsejson,"$.value.[?(@.name == '" + suitename + "')].id")[0]
        return str(suiteID) 
    except Exception as e :
        print('Something went wrong in fetching Test Suite ID :'+str(e))

def get_testcase_ID ():
    try:
        planID = get_testplan_details()[0]
        suiteID = get_testsuite_details()
        url = "https://dev.azure.com/" + organization + "/"+ project + "/_apis/test/plans/" + planID + "/suites/" + suiteID+ "/points?api-version=5.0"
        response = requests.get(url=url, auth = ('', pat))
        reponsejson = json.loads(response.text)
        testcaseID = jsonpath.jsonpath(reponsejson,"$..[?(@.name == '" + testcaseName + "')].id")[0]
        return testcaseID
    except Exception as e :
        print('Something went wrong in fetching Test Case ID :'+str(e))

def get_testpoint_ID ():
    try:
        planID = get_testplan_details()[0]
        suiteID = get_testsuite_details()
        tcID = get_testcase_ID()
        url = "https://dev.azure.com/" + organization + "/"+ project + "/_apis/test/plans/" + planID + "/suites/" + suiteID+ "/points?testCaseId=" + tcID + "&api-version=5.0"
        response = requests.get(url=url, auth = ('', pat))
        reponsejson = json.loads(response.text)
        testpointID = jsonpath.jsonpath(reponsejson,"$.value.[0].id")[0]
        return str(testpointID)
    except Exception as e :
        print('Something went wrong in fetching Test Point ID :'+str(e))

def create_run ():
    try:
        runName = planName +"-"+ str(datetime.now().strftime("%d-%m-%Y-%H-%M-%S"))
        planID = get_testplan_details()[0]
        pointID = get_testpoint_ID()
        url = "https://dev.azure.com/" + organization + "/"+ project + "/_apis/test/runs?api-version=5.0"
        payload = '{"name":"'+runName+'","plan":{"id":'+planID+'},"pointIds":['+pointID+']}'
        payloadJson  = json.loads(payload)
        response = requests.post(url=url, json=payloadJson, auth = ('', pat), headers={'Content-Type': 'application/json'})
        reponsejson = json.loads(response.text)
        runID = jsonpath.jsonpath(reponsejson,"$.id")[0]   
        return str(runID)
    except Exception as e :
        print('Something went wrong in fetching Run ID :'+str(e))

def get_testResult_ID ():
    try:
        runID = create_run()
        url = "https://dev.azure.com/" + organization + "/"+ project + "/_apis/test/runs/" + runID+ "/results?api-version=6.0-preview.6"
        response = requests.get(url=url, auth = ('', pat))
        reponsejson = json.loads(response.text)
        resultID = jsonpath.jsonpath(reponsejson,"$.value.[0].id")[0]
        return str(resultID),runID
    except Exception as e :
        print('Something went wrong in fetching Result ID :'+str(e))

def create_bug ():
    try:
        title = testcaseName + " - Failed" 
        url = "https://dev.azure.com/" + organization + "/"+ project + "/_apis/wit/workitems/$bug?api-version=5.0"
        payload = '[{"op": "add","path": "/fields/System.Title","from": null,"value": "'+ title +'"}]'
        payloadJson  = json.loads(payload)
        response=requests.post(url=url, json=payloadJson, auth = ('', pat), headers={'Content-Type': 'application/json-patch+json'})
        responsejson = json.loads(response.text)
        bugId = jsonpath.jsonpath(responsejson,"$.id")[0]
        print(bugId)
        return str(bugId)  
    except Exception as e :
        print('Something went wrong in updating Test Results :'+str(e))

def close_bug ():
    try:
        title = testcaseName + " - Failed"
        queryURL = "https://dev.azure.com/" + organization + "/"+ project + "/_apis/wit/wiql?api-version=6.0"
        payload = '{"query": "Select [System.Id] From WorkItems Where [System.WorkItemType] = \'Bug\' AND [State] = \'New\' AND [System.Title] = \''+ title + '\' AND [Area Path] = \'' + project + '\'"}'
        payloadJson  = json.loads(payload)
        response=requests.post(url=queryURL, json=payloadJson, auth = ('', pat), headers={'Content-Type': 'application/json'})
        responsejson = json.loads(response.text)
        if(str(jsonpath.jsonpath(responsejson,"$.workItems")[0])!='[]'):
            bugId = str(jsonpath.jsonpath(responsejson,"$.workItems[0].id")[0])
            print('Bug ID to be closed :'+bugId)
            updateURL = "https://dev.azure.com/" + organization + "/"+ project + "/_apis/wit/workitems/" + bugId + "?api-version=6.0"
            updatepayload = '[{"op":"test","path":"/rev","value":2},{"op":"add","path":"/fields/System.State","value":"Done"}]'
            updatepayloadJson = json.loads(updatepayload)
            requests.patch(url=updateURL, json=updatepayloadJson, auth = ('', pat), headers={'Content-Type': 'application/json-patch+json'})
    except Exception as e :
        print('Something went wrong in updating Test Results :'+str(e))                

def update_result (status):
    try:
        resultdata = get_testResult_ID()
        resultID = resultdata[0]
        runID = resultdata[1]
        url = "https://dev.azure.com/" + organization + "/"+ project + "/_apis/test/runs/" + runID+ "/results?api-version=6.0-preview.6"
        if (status == 'PASSED'):
            close_bug()
            payload = '[{ "id": ' + resultID + ',  "outcome": "' + status + '" ,    "state": "Completed",    "comment": "Execution Successful"  }]'
        else:
            bugid = create_bug()
            payload = '[{ "id": ' + resultID + ',  "outcome": "' + status + '",     "state": "Completed",    "comment": "Execution Failed", "associatedBugs": [{"id":' + bugid + '}]}]'
       
        payloadJson  = json.loads(payload)
        resp = requests.patch(url=url, json=payloadJson, auth = ('', pat), headers={'Content-Type': 'application/json'})  
        print(resp.text)
    except Exception as e :
        print('Something went wrong in updating Test Results :'+str(e))

update_result (status.upper())

