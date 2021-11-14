# -*- coding: utf-8 -*-
"""
Created on Thu Jul 15 16:05:51 2021
@author: abhigshr, product development intern 2021
Title: asynchronus compliance certificate handler
Build : V1
"""

from datetime import date, timedelta
import requests
import asyncio
import aiohttp
import datetime
from aiohttp import ClientTimeout
import time
import csv
import os

"""
Platform codes :
    AppleOSx, WinRT
    
app_iden = com.apple.calculator
    
"""

platform = "AppleOSx"
filter_last_seen = False
last_seen_days_ago = 30                     # Required if (filter_last_seen is True)
enrolled_only = True                       # FALSE if all devices required
issuer_auth = "CN=Adobe Private CA 2, O=Adobe Systems Incorporated, C=US"
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
            
            url_dev = "https://as177.awmdm.com/api/mdm/devices/" + str(i["Id"]["Value"]) + "/certificates?pagesize=10000"
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

dt1 = str(date.today())
d1 = date(int(dt1[0:4]), int(dt1[5:7]), int(dt1[8:10]))

def fill_array(i, j, mutex):
    temp_list = list()
    
    if mutex:
        temp_list.append(full_list[i]["DeviceCertificates"][j]["Name"])
        
        dt0 = full_list[i]["DeviceCertificates"][j]["ExpiresOn"].split(" ")[0].split("/")
        d0 = date(int(dt0[2]), int(dt0[0]), int(dt0[1]))
        temp_list.append(d0)
        timedelta = d0 - d1
        temp_list.append(timedelta.days)
        
        temp_list.append(full_list[i]["DeviceCertificates"][j]["IssuedBy"])
        temp_list.append(full_list[i]["DeviceCertificates"][j]["Status"])
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
       
file_name_p = str(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H-%M-%S')) + "_cert_comp" + ".csv"
file_name_a = str(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H-%M-%S')) + "_cert_noncomp" + ".csv"
with open(file_name_p, mode='w', newline = '', encoding="utf-8") as app_stats_p:
    write_obj_p = csv.writer(app_stats_p, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    write_obj_p.writerow(['Name', 'ExpiresOn', 'RemainingDays', 'IssuedBy', 'Status', 'Serial Number', 'Device ID', 'DeviceFriendlyName', 'UserName', 'OS Version', 'OSType', 'UDID', 'Enrollment Status', 'Ownership', 'LocationGroupId', 'Organization Group', 'LastSeen', 'LastEnrolledOn'])
    
    with open(file_name_a, mode='w', newline = '', encoding="utf-8") as app_stats_a:
        write_obj_a = csv.writer(app_stats_a, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        write_obj_a.writerow(['Serial Number', 'Device ID', 'DeviceFriendlyName', 'UserName', 'OS Version', 'OSType', 'UDID', 'Enrollment Status', 'Ownership', 'LocationGroupId', 'Organization Group', 'LastSeen', 'LastEnrolledOn'])

        print("CSV created, populating it now...")
        for i in range(len(full_list)):
            flag = False
            res = -1
            if full_list[i] != -1:
                for j in range(len(full_list[i]["DeviceCertificates"])):
                    if full_list[i]["DeviceCertificates"][j]["Name"] == resj["Devices"][i]["UserId"]["Name"] and full_list[i]["DeviceCertificates"][j]["Status"] == 2 and full_list[i]["DeviceCertificates"][j]["IssuedBy"] == issuer_auth:
                        dt0 = full_list[i]["DeviceCertificates"][j]["ExpiresOn"].split(" ")[0].split("/")
                        d0 = date(int(dt0[2]), int(dt0[0]), int(dt0[1]))
                        timedelta = d0 - d1
                        
                        if timedelta.days >= 0:
                            flag = True
                            res = j
                fill_array(i, res, flag)
            else:
                pass
        
print("CSV population successfull!")
print("Total time taken : " + str(total_time))