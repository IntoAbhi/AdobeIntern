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
from datetime import date

"""
Platform codes :
    AppleOSx, WinRT
"""
platform = "AppleOSx"
dev_count = 1

print("Querying all devices..")
start_time = time.time()
url1 = "https://as251.awmdm.com/api/mdm/devices/search?platform=" + platform + "&pagesize=" + str(dev_count)

headers = {
'aw-tenant-code': '####',
'accept': 'application/json',
'Content-Type': 'application/json',
'Authorization': 'Basic ####'
}
response = requests.request("GET", url1, headers=headers)

req_j = response.json()
print("Total devices queried: " + str(len(req_j["Devices"])))
print("Manipulating dates and computing lastseen duration..")

final_list = list()

for j in range(len(req_j["Devices"])):
    dev_id = req_j["Devices"][j]["Id"]["Value"]
    
    dt1 = req_j["Devices"][j]["LastSeen"][0:10]
    dt2 = str(date.today())
    
    d0 = date(int(dt1[0:4]), int(dt1[5:7]), int(dt1[8:10]))
    d1 = date(int(dt2[0:4]), int(dt2[5:7]), int(dt2[8:10]))
    delta = d1 - d0
    if delta.days <= 30:
        final_list.append(str(dev_id))
            
print("Total devices lastseen within 30 days: " + str(len(final_list)))
print("Making second API call, tagging all devices..")
url2 = "https://as251.awmdm.com/api/mdm/tags/10047/adddevices"

payload = json.dumps({
    "BulkValues": {
    "Value": final_list
    }
})
headers = {
'aw-tenant-code': '####',
'accept': 'application/json',
'Content-Type': 'application/json',
'Authorization': 'Basic ####'
}

response = requests.request("POST", url2, headers=headers, data=payload)
resp_j = response.json()
print(resp_j)

print("Devices tagged successfully, developing the CSV report..")

with open('tagged_data.csv', mode='w', newline = '', encoding="utf-8") as app_stats:
    write_obj = csv.writer(app_stats, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    write_obj.writerow(['Item Value', 'Message'])
    
    for i in resp_j["Faults"]["Fault"]:
        write_obj.writerow([i["ItemValue"], i["Message"]])
    app_stats.close()
    if(len(resp_j["Faults"]["Fault"]) == 0):
        os.remove("tagged_data.csv")

print("total Items: " + str(resp_j["TotalItems"]))
print("Accepted Items: " + str(resp_j["AcceptedItems"]))
print("Failed Items: " + str(resp_j["FailedItems"]))
print("Total time taken: " + str(time.time() - start_time))