"""
Automatic intelligence hub API data generation, extraction, dumping and logging
author: Abhigyan Shrivastava, product development intern 2021
builld : Final
Creation date : May2021
"""

import requests
import json
import time
import os
import smtplib
import socket
import traceback
from sqlalchemy import create_engine
import pandas
import datetime
from datetime import date


#Specify data corresponding to the required report
target_id_list = ['e33e4c4c-f5c3-4203-8fbf-5e1796a2c14', '4c9db076-63eb-4cd5-b5ad-72c4512a7e9', '8f8b741f-b943-465e-9190-4f2e708d8a2']
tab_list = ['table1', 'table2', 'table3']
server_user = 'WS1REPORT'
server_pass = '####'
server_address = '####.corp.adobe.com'
server_port = '3323'
server_database = 'WS1REPORT'


#Confirmation log credentials
sender_email = "rlyws1@adobe.com"
password = '####'
rec_email = "abhigshr@adobe.com"


def notify_and_kill():
    
    if is_error == True:
        message = "subject: Failed - Report dumping\n TLDR : One or more reports failed :( please check logs for more information\n"
        
    else:
        log_file.write("Operation was completed successfully\nHave a great day ahead!/n")
        message = "subject: Success - Report dumping\n"
    
    log_file.write("\n\n\nThis python script is executed from " + socket.getfqdn() + " and appends the report to " + server_user + " MySQL Database.")
    log_file.close()
    with open(log_name, "r") as a_file:
          for line in a_file:
            message = message + line
    server = smtplib.SMTP('authrelay.corp.adobe.com', 587)
    server.starttls()
    server.login(sender_email, password)
    print("SMTP login success")
    server.sendmail(sender_email, rec_email, message)
    print("Email report has been sent to ", rec_email)
    os._exit(1)
    


#Initializing necessary files and variables
log_name = "log_" + str(date.today().strftime("%Y-%m-%d")) + ".log"
log_file = open(log_name, "w")
is_error = False
df_list = []
if len(target_id_list) != len(tab_list):
    is_error = True
    log_file.write("Inadequate/excess table names present for the corresponding report ids\n")
    notify_and_kill()
    
    

try:
    
    #API request to generate access token
    requests.Session().cookies.clear()
    print("Obtaining access token")
    url_server = "https://auth.na1.data.vmwservices.com/oauth/token?grant_type=client_credentials"
    response1 = requests.request("POST", url_server, headers={}, data={}, auth = ('####', '####'))
    try:
        access_t = response1.json()['access_token']
    except Exception:
        is_error = True
        log_file = open(log_name, "w")
        log_file.write(str(datetime.datetime.now()) + " Failed with a response: " + str(response1.status_code) + " " + response1.reason)
        log_file.write(" Unable to fetch access token")
        notify_and_kill()
    print("Access token obtained successfully")
    auth_text = 'Bearer ' + access_t
    print("Please wait.. \n\n")
    time.sleep(10)
    
    
    
    for i in range(len(target_id_list)):
    
        target_id = target_id_list[i]
        
        #API request to generate the report
        requests.Session().cookies.clear()
        print("Sending report generation request")
        url_report = "https://api.na1.data.vmwservices.com/v1/reports/" + target_id + "/run"
        headers = {
          'authorization': auth_text,
          'Content-Type': 'application/json'
        }
        response2 = requests.request("POST", url_report, headers=headers, data={})
        if response2.status_code != 201:
            is_error = True
            print(response2.status_code)
            log_file.write(str(datetime.datetime.now()) + ": Report ID " + target_id_list[i] + " failed with an Error: " + str(response2.status_code) + " " + response2.reason)
            notify_and_kill()
            
        print("Report generated successfully")
        print("Please wait..")
        time.sleep(60)
        
        
        #API request to download the report
        requests.Session().cookies.clear()
        print("Pulling newly generated report ID")
        url_repoid = "https://api.na1.data.vmwservices.com/v1/reports/" + target_id + "/downloads/search"
        payload = json.dumps({
          "offset": 0,
          "page_size": 3
        })
        headers = {
          'authorization': auth_text,
          'Content-Type': 'application/json',
        }
        response3 = requests.request("POST", url_repoid, headers=headers, data=payload)
        final_repoid = response3.json()["data"]["results"][0]["id"]
        print("Report ID pulled successfully: " + final_repoid)
        
        
        #Downloading the report via cURL
        file_name = "itre_report_" + str(i) + '_' + str(date.today().strftime("%Y-%m-%d")) + ".csv"
        print("Report being downloaded, please wait...")
        curl_com = "curl -X GET https://api.na1.data.vmwservices.com/v1/reports/tracking/" + final_repoid +"/download -H " + '"' + "Authorization: " + auth_text + '"' +" -L -o " + file_name
        os.system(curl_com)
        time.sleep(10)
        
        
        #Manipulation of dates to last_seen and adding a new column
        print("Manipulating the report now..")
        data_frame = pandas.read_csv(file_name)
        try:
            data_frame['device_last_seen_utc'] = data_frame['device_last_seen_utc'].str.slice(0, 10)
            data_frame['device_last_seen_utc'] = pandas.to_datetime(data_frame['device_last_seen_utc']).dt.date
        except:
            pass
        
        try:
            data_frame.drop(columns = ['device_friendly_name'])
        except:
            pass
        
        data_frame['report_date'] = date.today().strftime("%Y-%m-%d")
        print("Report manipulated successfully" + '\n\n')
        
        df_list.append(data_frame)
except Exception:
    is_error = True
    log_file = open(log_name, "w")
    log_file.write(str(datetime.datetime.now()))
    traceback.print_exc(file = log_file)
    notify_and_kill()


#Export pandas dataframe to a relational database server
try:
    print("Dumping the downloaded reports into RDBMS server one by one...")
    engine = create_engine('mysql+pymysql://' + server_user + ':' + server_pass + '@' + server_address + ':' + server_port + '/' + server_database)
    
    for i in range(len(target_id_list)):
        df_list[i].to_sql(tab_list[i], engine, if_exists='replace', index = False)
        print("Dump " + str(i+1) + " successful!")
except Exception:
    is_error = True
    log_file.write(str(datetime.datetime.now()))
    traceback.print_exc(file = log_file)

notify_and_kill()

    










