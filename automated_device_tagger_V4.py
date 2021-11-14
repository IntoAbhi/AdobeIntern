# -*- coding: utf-8 -*-
"""
Created on Wed Jun 16 13:53:51 2021
title : automated device tagger
@author: abhigshr, product development intern
Build : final
"""

import requests
import csv
import json
import time
import os
import datetime
from datetime import date

"""
Platform codes :
    AppleOSx, WinRT
"""
platform = "AppleOSx"
tag_id = 10042
last_seen_days = 30
dev_count = 10

print("Querying all devices..")
start_time = time.time()

"""
177 is production, DO NOT USE
10041 is production tag, DO NOT USE

Use 251 and 10042
"""



# Finding all devices last seen more than 30 days
url1 = "https://as251.awmdm.com/api/mdm/devices/search?platform=" + platform + "&pagesize=" + str(dev_count)
header1 = {
'aw-tenant-code': '####',
'accept': 'application/json',
'Content-Type': 'application/json',
'Authorization': 'Basic ####'
}
response = requests.request("GET", url1, headers=header1)
print("Response status : " + response.reason)

req_j = response.json()
print(response.reason)
print("Total devices queried: " + str(len(req_j["Devices"])))
print("Manipulating dates and computing lastseen duration..")

tag_list_1 = list()

for j in range(len(req_j["Devices"])):
    dev_id = req_j["Devices"][j]["Id"]["Value"]
    
    dt1 = req_j["Devices"][j]["LastSeen"][0:10]
    dt2 = str(date.today())
    
    d0 = date(int(dt1[0:4]), int(dt1[5:7]), int(dt1[8:10]))
    d1 = date(int(dt2[0:4]), int(dt2[5:7]), int(dt2[8:10]))
    delta = d1 - d0
    if delta.days < last_seen_days:
        tag_list_1.append(str(dev_id))
            
print("Total devices with lastseen beyond 30 days: " + str(len(tag_list_1)))




# Finding all devices tagged under tag 10042
print("Populating the tag list for tag 10042")
tag_list_2 = list()
url2 = "https://as251.awmdm.com/api/mdm/tags/" + tag_id + "/devices"
response = requests.request("GET", url2, headers=header1)
print("Response status : " + response.reason)
resp2_j = response.json()
for i in resp2_j["Device"]:
    tag_list_2.append(i["DeviceId"])



# Building removal list
removal_list = [x for x in tag_list_1 if x not in tag_list_2]
name1 = str(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H-%M-%S')) + "_deletion" + ".csv"
with open(name1, mode='w', newline = '', encoding="utf-8") as app_stats:
    write_obj = csv.writer(app_stats, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    write_obj.writerow(['Device ID'])
    for i in removal_list:
        write_obj.writerow([i])

# Building addition list
addition_list = [x for x in tag_list_2 if x not in tag_list_1]
name2 = str(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H-%M-%S')) + "_addition" + ".csv"
with open(name2, mode='w', newline = '', encoding="utf-8") as app_stats:
    write_obj = csv.writer(app_stats, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    write_obj.writerow(['Device ID'])
    for i in addition_list:
        write_obj.writerow([i])


# My beautiful algorithm which was later replaced by python syntax:
# for i in range(len(tag_list_1)):
#     for j in range(len(tag_list_2)):
#         if tag_list_1[i] == tag_list_2[j]:
#             tag_list_1[i] = -1;
#             tag_list_2[j] = -1;
# print("Cleaning both lists by removing negatives and slicing")
# ref = 0
# for i in range(len(tag_list_1)):
#     if int(tag_list_1[i]) < 0:
#         temp = tag_list_1[i]
#         tag_list_1[i] = tag_list_1[ref]
#         tag_list_1[ref] = temp
#         ref += 1
# tag_list_1 = tag_list_1[ref:]

# ref = 0
# for i in range(len(tag_list_2)):
#     if int(tag_list_2[i]) < 0:
#         temp = tag_list_2[i]
#         tag_list_2[i] = tag_list_2[ref]
#         tag_list_2[ref] = temp
#         ref += 1
# tag_list_2 = tag_list_2[ref:]
# Both lists are clean and ready
# List1 : addition list
# List2 : removal list
# print(tag_list_1)
# print(tag_list_2)




# Removing 'removal_list' devices
print("Removing all non-required devices: " + str(len(tag_list_2)))
url3 = "https://as251.awmdm.com/api/mdm/tags/"+ tag_id +"/removedevices"
payload = json.dumps({
    "BulkValues": {
    "Value": tag_list_2
    }
})
response = requests.request("POST", url3, headers=header1, data=payload)
print("Response status : " + response.reason)
resp3_j = response.json()
name3 = str(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H-%M-%S')) + "_removed_data" + ".csv"
with open(name3, mode='w', newline = '', encoding="utf-8") as app_stats:
    write_obj = csv.writer(app_stats, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    write_obj.writerow(['Item Value', 'Message'])
    
    for i in resp3_j["Faults"]["Fault"]:
        write_obj.writerow([i["ItemValue"], i["Message"]])
    app_stats.close()
    if(len(resp3_j["Faults"]["Fault"]) == 0):
        os.remove("removed_data.csv")

print("total Items: " + str(resp3_j["TotalItems"]))
print("Accepted Items: " + str(resp3_j["AcceptedItems"]))
print("Failed Items: " + str(resp3_j["FailedItems"]))




# Adding 'addition_list' devices
print("Tagging all the new eligible devices: " + str(len(tag_list_1)))
url4 = "https://as251.awmdm.com/api/mdm/tags/" + tag_id + "/adddevices"
payload = json.dumps({
    "BulkValues": {
    "Value": tag_list_1
    }
})
response = requests.request("POST", url4, headers=header1, data=payload)
print("Response status : " + response.reason)
resp4_j = response.json()
print("Devices tagged successfully, developing the CSV report..")
name4 = str(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H-%M-%S')) + "_added_data" + ".csv"
with open(name4, mode='w', newline = '', encoding="utf-8") as app_stats:
    write_obj = csv.writer(app_stats, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    write_obj.writerow(['Item Value', 'Message'])
    
    for i in resp4_j["Faults"]["Fault"]:
        write_obj.writerow([i["ItemValue"], i["Message"]])
    app_stats.close()
    if(len(resp4_j["Faults"]["Fault"]) == 0):
        os.remove("added_data.csv")

print("total Items: " + str(resp4_j["TotalItems"]))
print("Accepted Items: " + str(resp4_j["AcceptedItems"]))
print("Failed Items: " + str(resp4_j["FailedItems"]))
print("Total time taken: " + str(time.time() - start_time))