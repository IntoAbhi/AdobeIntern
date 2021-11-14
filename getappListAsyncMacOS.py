#!/usr/local/bin/python3.7
import requests,json, csv, ast
import asyncio
from aiohttp import ClientSession
import aiohttp

url = "https://as177.awmdm.com/api/mdm/devices/extensivesearch"
url_bulk = "https://as177.awmdm.com/api/mdm/devices"
appurl = "https://as177.awmdm.com/api/mdm/devices/apps"
querystringOsx = {"platform":"AppleOSx", "pagesize":"6000"}
querystring_bulk = {"searchby":"Udid"}

machinelist = list()
machinelistDict = {}
headers = {
    'aw-tenant-code': "####",
    'accept': "application/json",
    'Content-Type': "application/json",
    'Authorization': "Basic ####",
    'Cache-Control': "no-cache",
    'Postman-Token': "####"
    }

responseOsx = requests.request("GET", url, headers=headers, params=querystringOsx)
#devices = responseOsx.json()['Devices'];
#print(responseOsx)
devices = json.loads(responseOsx.text)
serial_number_list = []
for i in range(len(devices['Devices'])):
	serialNo = devices['Devices'][i]['Udid']
	serial_number_list.append(serialNo)

print("Got all the serial numbers, Number of devices:" + str(len(serial_number_list)))


#serial_number_list1=serial_number_list.encode("ascii","replace")

body = "{'BulkValues': {'value': %s }}" % (serial_number_list)
responseBulkOsx = requests.request("POST", url_bulk, data=body, headers=headers, params=querystring_bulk)
devices = json.loads(responseBulkOsx.text)

for i in range(len(devices['Devices'])):
	serialNo = devices['Devices'][i]['SerialNumber']
	udid = devices['Devices'][i]['Udid']
	username = devices['Devices'][i]['UserName']
	OSType = devices['Devices'][i]['Platform']
	macOSVersion = devices['Devices'][i]['OperatingSystem']
	EnrollmentStatus = devices['Devices'][i]['EnrollmentStatus']
	Platform = devices['Devices'][i]['Platform']
	LocationGroupId = devices['Devices'][i]['LocationGroupId']['Id']['Value']
	OrganizationGroup = devices['Devices'][i]['LocationGroupId']['Name']
	DeviceFriendlyName = devices['Devices'][i]['DeviceFriendlyName']

	Ownership = devices['Devices'][i]['Ownership']
	LastSeen = devices['Devices'][i]['LastSeen'].split('T', 1 )[0]
	LastEnrolledOn = devices['Devices'][i]['LastEnrolledOn'].split('T', 1 )[0]
	machinelistDict.update({'Serial Number':serialNo, 'DeviceFriendlyName': DeviceFriendlyName, 'OSType': OSType, 'macOS Version': macOSVersion, 'UserName': username, 'UDID': udid, 'Enrollment Status': EnrollmentStatus, 'LocationGroupId': LocationGroupId, 'Organization Group': OrganizationGroup, 'Ownership': Ownership, 'LastSeen': LastSeen, 'LastEnrolledOn': LastEnrolledOn })
	machinelist.append(machinelistDict.copy())


print("Recieved OS details for all devices: " + str(len(devices['Devices'])))


async def fetch(url, session, index):
	async with session.get(url, headers=headers, params={"searchby":"Udid","id":machinelist[index].get('UDID')}) as response:
		return await response.read()
		
async def bound_fetch(sem, url, session, index):
    # Getter function with semaphore.
    async with sem:
        return await fetch(url, session, index)

async def run(r):
	url = "https://as177.awmdm.com/api/mdm/devices/apps"
	tasks = []
	sem = asyncio.Semaphore(2500)
    # Fetch all responses within one Client session,
    # keep connection alive for all requests.
	async with ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
		for i in range(r):
			task = asyncio.ensure_future(bound_fetch(sem, url.format(i), session, i))
			tasks.append(task)
		responses = await asyncio.gather(*tasks)
        # you now have all response bodies in this variable
		csvlist = []
		for listvalue in range(len(machinelist)):
			responses[listvalue] = json.loads(responses[listvalue].decode('utf-8'))
			machinelist[listvalue].update({'App Name' : ''})
			machinelist[listvalue].update({'App Identifier' : ''})
			machinelist[listvalue].update({'App Version' : ''})
			machinelist[listvalue].update({'Install Status' : ''})
			for i in range(len(responses[listvalue]['DeviceApps'])):
				appBundleID = responses[listvalue]['DeviceApps'][i]['ApplicationIdentifier']
				appName = responses[listvalue]['DeviceApps'][i]['ApplicationName']
				if appBundleID == "com.adobe.reader":
					machinelist[listvalue]['App Name'] = str(responses[listvalue]['DeviceApps'][i]['ApplicationName'])
					machinelist[listvalue]['App Identifier'] = str(responses[listvalue]['DeviceApps'][i]['ApplicationIdentifier'])
					machinelist[listvalue]['App Version'] = str(responses[listvalue]['DeviceApps'][i]['Version'])
					installStatus = str(responses[listvalue]['DeviceApps'][i]['Status'])
					if installStatus == "1":
						machinelist[listvalue]['Install Status'] = "Pending Install"
					elif installStatus == "2":
						machinelist[listvalue]['Install Status'] = "Installed"
					elif installStatus == "3":
						machinelist[listvalue]['Install Status'] = "Pending Removal"
					elif installStatus == "4":
						machinelist[listvalue]['Install Status'] = "Removed"
					elif installStatus == "5":
						machinelist[listvalue]['Install Status'] = "Unknown"
					csvlist.append(machinelist[listvalue].copy())
					#print(machinelist[listvalue])	
		with open('AndroidAcrobat.csv', 'w') as csvfile:
			fieldnames = ['App Name', 'App Version', 'Install Status', 'App Identifier', 'Serial Number', 'DeviceFriendlyName', 'UserName', 'macOS Version', 'OSType', 'UDID', 'Enrollment Status', 'Ownership', 'LocationGroupId', 'Organization Group', 'LastSeen', 'LastEnrolledOn']
			writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
			writer.writeheader()
			for i in range(len(csvlist)):
				 writer.writerow(csvlist[i])

def print_responses(result):
	print(result)

loop = asyncio.get_event_loop()
future = asyncio.ensure_future(run(len(devices['Devices'])))
loop.run_until_complete(future)
