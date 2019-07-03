import csv
import shutil
import json, requests
import time
from datetime import datetime
from config import _FILTER_TIME, NETWORK_ID, MERAKI_API_KEY, _SESSION_TIME, timeWindow, rssiThreshold

# opens cmxdata and formats to show only relevant information
# if time difference is within session time, the times are considered within the same session, if they are out, they are considered 2 different sessions
def getCMXHours(data):
    arrayCount = 0
    newData = []
    for x in data:
        timeEntries = len(x['timestamps'])
        if timeEntries > 1:
            firstSeen =0
            time2=timeEntries-1
            time1=timeEntries-2
            startFlag=0
            timeCount=0
            while time1 >= 0:
                if (int(x['timestamps'][time1]) - int(x['timestamps'][time2])) < _SESSION_TIME and startFlag == 0 and firstSeen == 0:
                    # print(str(x['timestamps'][time1]) + ' - ' + str(x['timestamps'][time2]) + ' = ' + str(int(x['timestamps'][time1]) - int(x['timestamps'][time2])) + ' - less than 300, firstseen = 0')
                    newData.append({'MAC':x['MAC'],'timeData':[{'firstSeen':x['timestamps'][time2]}],'visits':1, 'totalTime':(int(x['timestamps'][time1]) - int(x['timestamps'][time2]))})
                    if time1 == 0:
                        newData[arrayCount]['timeData'][timeCount]['lastSeen']=x['timestamps'][time1]
                        timeCount=timeCount+1
                    startFlag=1
                    # startTimeTemp=time2
                    firstSeen=1
                    time2 = time1
                    time1 = time1-1
                elif int(x['timestamps'][time1]) - int(x['timestamps'][time2]) < _SESSION_TIME and startFlag == 0 and firstSeen == 1:
                    # print(str(x['timestamps'][time1]) + ' - ' + str(x['timestamps'][time2]) + ' = ' + str(int(x['timestamps'][time1]) - int(x['timestamps'][time2])) + ' - less than 300, startflag=0')
                    if time1 != 0:
                        newData[arrayCount]['timeData'].append({'firstSeen':x['timestamps'][time2]})
                        newData[arrayCount]['visits']=int(newData[arrayCount]['visits'])+1
                        newData[arrayCount]['totalTime']=int(newData[arrayCount]['totalTime']) + (int(x['timestamps'][time1]) - int(x['timestamps'][time2]))
                        startFlag=1
                    time2 = time1
                    time1 = time1-1
                elif int(x['timestamps'][time1]) - int(x['timestamps'][time2]) < _SESSION_TIME and startFlag == 1 :
                    # print(newData[arrayCount]['totalTime'])
                    # print(str(x['timestamps'][time1]) + ' - ' + str(x['timestamps'][time2]) + ' = ' + str(int(x['timestamps'][time1]) - int(x['timestamps'][time2])) + ' less than 300, startflag=1')
                    newData[arrayCount]['totalTime']=int(newData[arrayCount]['totalTime']) + (int(x['timestamps'][time1]) - int(x['timestamps'][time2]))
                    if time1 == 0:
                        newData[arrayCount]['timeData'][timeCount]['lastSeen']=x['timestamps'][time1]
                        timeCount=timeCount+1
                    time2 = time1
                    time1 = time1-1
                elif int(x['timestamps'][time1]) - int(x['timestamps'][time2]) >= _SESSION_TIME and startFlag == 1:
                    # print(str(x['timestamps'][time1]) + ' - ' + str(x['timestamps'][time2]) + ' = ' + str(int(x['timestamps'][time1]) - int(x['timestamps'][time2])) +' greater than 300, startflag reset')
                    newData[arrayCount]['timeData'][timeCount]['lastSeen']=x['timestamps'][time2]
                    startFlag=0
                    timeCount=timeCount+1
                    time2 = time1
                    time1 = time1-1
                elif int(x['timestamps'][time1]) - int(x['timestamps'][time2]) >= _SESSION_TIME and startFlag == 0:
                    # print(str(x['timestamps'][time1]) + ' - ' + str(x['timestamps'][time2]) + ' = ' + str(int(x['timestamps'][time1]) - int(x['timestamps'][time2])) + ' greater than 300, startflag=0')
                    time2 = time1
                    time1 = time1-1
            if timeCount > 0:
                arrayCount=arrayCount+1
    return(newData)

# filters out cmx data seen over a certain period of time
def cmxFilterHours(data):
    newData=getCMXHours(data)
    returnData=[]
    for x in newData:
        if x['totalTime'] < _FILTER_TIME:
            returnData.append(x)
    return(returnData)

# gets meraki MV video link
def getMVLink(serial_number,timestamp):
    # Get video link
    url = "https://api.meraki.com/api/v0/networks/"+NETWORK_ID+"/cameras/"+str(serial_number)+"/videoLink?timestamp="+str(timestamp)

    headers = {
        'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
        "Content-Type": "application/json"
    }
    resp = requests.request("GET", url, headers=headers)
    # print(resp)
    if int(resp.status_code / 100) == 2:
        return(resp.text)
    return('link error')

# Aggregates amount of activity per hour throughout the day
def computeCMXActivity(data):
    newData = getCMXHours(data)
    timesArray=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    for x in newData:
        for y in x['timeData']:
            inTime = int(datetime.utcfromtimestamp(float(y['firstSeen'])).strftime('%H'))
            outTime = int(datetime.utcfromtimestamp(float(y['lastSeen'])).strftime('%H'))
            # print('---'+inTime+'---'+outTime+'---'+count)
            # count = count + 1
            while inTime <= outTime:
                timesArray[inTime] = timesArray[inTime] + 1
                inTime = inTime+1
    return(timesArray)

# returns array of activity throughout the day of Mv activity
def computeMVActivity(data):
    timesArray=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    for x in data:
        inTime = int(datetime.utcfromtimestamp(float(x['timeIn'])/1000).strftime('%H'))
        outTime = int(datetime.utcfromtimestamp(float(x['timeOut'])/1000).strftime('%H'))
        #
        while inTime <= outTime:
            timesArray[inTime] = timesArray[inTime] + int(x['count'])
            inTime = inTime+1
    return(timesArray)

# correlate MV sense data with cmx data
# when MV sense is triggered, check what MAC addresses have been found within certain time window and RSSI threshold
# Time window for devices to be considered is slightly larger than the inTime and outTime of mv data
def getCorrelation(cmxData,mvData):
    data=[]
    count=0
    for x in mvData:
        inTime = int(x['timeIn'])/1000
        outTime = int(x['timeOut'])/1000
        people = x['count']
        flag=0

        for y in cmxData:
            for z in y['timestamps']:
                if int(z['ts']) >= (inTime-timeWindow) and int(z['ts']) <= (outTime+timeWindow) and int(z['rssi']) > rssiThreshold and flag == 0:
                    data.append({'inTime':datetime.utcfromtimestamp(float(inTime)).strftime('%H:%M'),'outTime':datetime.utcfromtimestamp(float(outTime)).strftime('%H:%M'), 'count':people, 'devices':[{'MAC':y['MAC'],'time':datetime.utcfromtimestamp(float(z['ts'])).strftime('%H:%M'),'rssi':z['rssi']}]})
                    flag=1
                if int(z['ts']) >= (inTime-timeWindow) and int(z['ts']) <= (outTime+timeWindow) and int(z['rssi']) > rssiThreshold and flag == 1:
                    update=1
                    for d in data[count]['devices']:
                        if y['MAC'] in d.values():
                            update=0
                    if update==1:
                        data[count]['devices'].append({'MAC':y['MAC'],'time':datetime.utcfromtimestamp(float(outTime)).strftime('%H:%M'),'rssi':z['rssi']})
        if flag==1:
            count=count+1
    return(data)
