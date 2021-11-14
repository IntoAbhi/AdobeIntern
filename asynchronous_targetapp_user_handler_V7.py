"""
Created on Fri May 28 14:11:50 2021
@author: abhigshr, product development intern 2021
Title: asynchronus targetapp user handler
Build : V7
"""
from datetime import date, timedelta
import requests
import asyncio
import aiohttp
import datetime
from aiohttp import ClientTimeout
import time
import csv
import re
import os

"""
Platform codes :
    AppleOSx, WinRT
    
app_iden = com.apple.calculator
    
"""

platform = "AppleOSx"
app_name_list = ["WinZip 20.0"]                        # Required for Windows
app_iden_list = ["com.apple.calculator"]         # Required for Apple
filter_last_seen = False
last_seen_days_ago = 30                     # Required if (filter_last_seen is True)
enrolled_only = False                       # FALSE if all devices required
dev_count = 10


start_time = time.time()
url = "https://as177.awmdm.com/api/mdm/devices/search?platform=" + platform + "&pagesize=" + str(dev_count)
if filter_last_seen:
    past_date = date.today() - timedelta(last_seen_days_ago)
    url = url + "&seensince=" + str(past_date)
headers = {
  'aw-tenant-code': '####',
  'accept': 'application/json',
  'Content-Type': 'application/json',
  'Authorization': 'Basic ####'
}
response = requests.request("GET", url, headers=headers)    

if response.status_code != 200:
    print("ERROR : Please check the initials!")
    print(str(response.status_code) + response.reason)
    os._exit(1)
resj = response.json()

async def get_api(session, url):
    async with session.get(url, headers = headers) as resp:
        result = await resp.json()
        time.sleep(0.05)
        return result

async def filler():
    return -1

total_time = 0
full_list = []
timeout = ClientTimeout(total = 5000)
async def main():
    tasks = []
    async with aiohttp.ClientSession(timeout = timeout) as session:
        print("Creating future for all devices, count: " + str(len(resj["Devices"])))
        
        counter = 0
        for i in resj["Devices"]:
            
            url_dev = "https://as177.awmdm.com/api/mdm/devices/" + str(i["Id"]["Value"]) + "/apps?pagesize=10000"
            if enrolled_only:
                if i["EnrollmentStatus"] == "Enrolled":
                    tasks.append(asyncio.create_task(get_api(session, url_dev)))
                    counter+=1
                else:
                    tasks.append(asyncio.create_task(filler()))
            else:
                if i["EnrollmentStatus"] != "Unenrolled":
                    tasks.append(asyncio.create_task(get_api(session, url_dev)))
                    counter+=1
                else:
                    tasks.append(asyncio.create_task(filler()))
            

        print("Gathering all futures, total size: " + str(counter) + ", this will take a while...")
        global full_list
        full_list = await asyncio.gather(*tasks)
        print("All coroutines gathered successfully!")

        global total_time
        total_time = (time.time() - start_time)
        
        error_api = 0
        for i in full_list:
            if i != -1:
                try:
                    i['DeviceApps']
                except:
                    error_api += 1
        print("Number of api calls failed : " + str(error_api))

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())

def fill_array(i, j, mutex):
        temp_list = list()
        
        if mutex:
            temp_list.append(full_list[i]["DeviceApps"][j]["ApplicationName"])
            temp_list.append(full_list[i]["DeviceApps"][j]["Version"])
            temp_list.append(full_list[i]["DeviceApps"][j]["Status"])
            temp_list.append(full_list[i]["DeviceApps"][j]["ApplicationIdentifier"])
        temp_list.append(resj["Devices"][i]["SerialNumber"])
        temp_list.append(resj["Devices"][i]["Id"]["Value"])
        temp_list.append(resj["Devices"][i]["DeviceFriendlyName"])
        temp_list.append(resj["Devices"][i]["UserName"])
        temp_list.append(resj["Devices"][i]["OSBuildVersion"])
        temp_list.append(resj["Devices"][i]["Platform"])
        temp_list.append(resj["Devices"][i]["Udid"])
        temp_list.append(resj["Devices"][i]["EnrollmentStatus"])
        temp_list.append(resj["Devices"][i]["Ownership"])
        temp_list.append(resj["Devices"][i]["LocationGroupId"]["Id"]["Value"])
        temp_list.append(resj["Devices"][i]["LocationGroupName"])
        temp_list.append(resj["Devices"][i]["LastSeen"][0:10])
        temp_list.append(resj["Devices"][i]["LastEnrolledOn"][0:10])
        
        if mutex:
            write_obj_p.writerow(temp_list)
        else:
            write_obj_a.writerow(temp_list)
       
file_name_p = str(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H-%M-%S')) + "_app_report_present" + ".csv"
file_name_a = str(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H-%M-%S')) + "_app_report_absent" + ".csv"
with open(file_name_p, mode='w', newline = '', encoding="utf-8") as app_stats_p:
    write_obj_p = csv.writer(app_stats_p, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    write_obj_p.writerow(['App Name', 'App Version', 'Install Status', 'App Identifier', 'Serial Number', 'Device ID', 'DeviceFriendlyName', 'UserName', 'OS Version', 'OSType', 'UDID', 'Enrollment Status', 'Ownership', 'LocationGroupId', 'Organization Group', 'LastSeen', 'LastEnrolledOn'])
    
    with open(file_name_a, mode='w', newline = '', encoding="utf-8") as app_stats_a:
        write_obj_a = csv.writer(app_stats_a, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        write_obj_a.writerow(['Serial Number', 'Device ID', 'DeviceFriendlyName', 'UserName', 'OS Version', 'OSType', 'UDID', 'Enrollment Status', 'Ownership', 'LocationGroupId', 'Organization Group', 'LastSeen', 'LastEnrolledOn'])

        print("CSV created, populating it now...")
        for i in range(len(full_list)):
            flag = False
            if platform == "AppleOSx" and full_list[i] != -1:
                for j in range(len(full_list[i]["DeviceApps"])):
                    if full_list[i]["DeviceApps"][j]["ApplicationIdentifier"] in app_iden_list:
                        flag = True
                        fill_array(i, j, flag)
                        break
                if flag == False:
                    # Not found
                    fill_array(i, -1, flag)
    
            elif platform == "WinRT" and full_list[i] != -1:
                for j in range(len(full_list[i]["DeviceApps"])):
                    # if re.search(app_name, full_list[i]["DeviceApps"][j]["ApplicationName"]):
                    if full_list[i]["DeviceApps"][j]["ApplicationName"] in app_name_list:
                        if full_list[i]["DeviceApps"][j]["Status"] == 2:
                            flag = True
                            fill_array(i, j, flag)
                            break
                if flag == False:
                    # Not found
                    fill_array(i, -1, flag)
                            
            else:
                pass
        
print("CSV population successfull!")
print("Total time taken : " + str(total_time))

