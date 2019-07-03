# web application GUI

from flask import Flask, render_template, request
import csv
import shutil
from datetime import datetime
from compute import *

app = Flask(__name__)

@app.route('/', methods=['GET','POST'])
def index():
    if request.method == 'POST':
        select = flask.request.form.get('select')
        if select == 'cmxTimes':
            return cmxTimes()
    # open cmx data
    data = []
    with open('cmxData.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        count = 0
        arrayCount=0
        flag=0
        for row in reader:
            if row['MAC'] != '' and flag==0:
                count = 0
                flag = 1
                data.append({'MAC':row['MAC'],'timestamps':[{'ts':datetime.utcfromtimestamp(float(row['time'])).strftime('%m-%d,%H:%M'),'rssi':row['rssi']}]})
            elif row['MAC'] != '' and flag==1:
                arrayCount = arrayCount+1
                count = 0
                data.append({'MAC':row['MAC'],'timestamps':[{'ts':datetime.utcfromtimestamp(float(row['time'])).strftime('%m-%d,%H:%M'),'rssi':row['rssi']}]})
            elif row['MAC'] == '':
                count = count+1
                data[arrayCount]['timestamps'].append({'ts':datetime.utcfromtimestamp(float(row['time'])).strftime('%m-%d,%H:%M'),'rssi':row['rssi']})
    return render_template("index.html",data=data)

@app.route('/cmxTimes', methods=['GET','POST'])
def cmxTimes():

    # open cmx data
    data = []
    with open('cmxData.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        count = 0
        arrayCount=0
        flag=0
        for row in reader:
            if row['MAC'] != '' and flag==0:
                count = 0
                flag = 1
                data.append({'MAC':row['MAC'],'timestamps':{count:row['time']}})
            elif row['MAC'] != '' and flag==1:
                arrayCount = arrayCount+1
                count = 0
                data.append({'MAC':row['MAC'],'timestamps':{count:row['time']}})
            elif row['MAC'] == '':
                count = count+1
                data[arrayCount]['timestamps'][count]=row['time']
    # print(len(data[0]['timestamps']))
    cmxData=getCMXHours(data)
    for x in cmxData:
        for y in range(len(x['timeData'])):
            x['timeData'][y]['firstSeen'] = datetime.utcfromtimestamp(float(x['timeData'][y]['firstSeen'])).strftime('%m-%d,%H:%M')
            x['timeData'][y]['lastSeen'] = datetime.utcfromtimestamp(float(x['timeData'][y]['lastSeen'])).strftime('%m-%d,%H:%M')
    return render_template("cmxTimes.html",cmxData=cmxData)

@app.route('/hourFilter', methods=['GET','POST'])
def hourFilter():
    # open cmx data
    data = []
    with open('cmxData.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        count = 0
        arrayCount=0
        flag=0
        for row in reader:
            if row['MAC'] != '' and flag==0:
                count = 0
                flag = 1
                data.append({'MAC':row['MAC'],'timestamps':{count:row['time']}})
            elif row['MAC'] != '' and flag==1:
                arrayCount = arrayCount+1
                count = 0
                data.append({'MAC':row['MAC'],'timestamps':{count:row['time']}})
            elif row['MAC'] == '':
                count = count+1
                data[arrayCount]['timestamps'][count]=row['time']
    # print(len(data[0]['timestamps']))
    cmxData=cmxFilterHours(data)
    for x in cmxData:
        for y in range(len(x['timeData'])):
            x['timeData'][y]['firstSeen'] = datetime.utcfromtimestamp(float(x['timeData'][y]['firstSeen'])).strftime('%m-%d,%H:%M')
            x['timeData'][y]['lastSeen'] = datetime.utcfromtimestamp(float(x['timeData'][y]['lastSeen'])).strftime('%m-%d,%H:%M')
    print(cmxData)
    return render_template("filterTimes.html",cmxData=cmxData)



@app.route('/mvSense',methods=['GET','POST'])
def mvSense():
    # open mv sense data
    data = []
    with open('mvData.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        count = 0
        arrayCount=0
        flag=0
        for row in reader:
            print(row['Time In'])
            link = getMVLink('Q2EV-2QFS-YRYE',row['Time In'])
            link = link.replace('{"url":"',"")
            link = link.replace('"}',"")
            data.append({'timeIn':datetime.utcfromtimestamp(float(row['Time In'])/1000).strftime('%m-%d,%H:%M'),'timeOut':datetime.utcfromtimestamp(float(row['Time Out'])/1000).strftime('%m-%d,%H:%M'),'count':row['Count'],'link':link})
    # print(len(data[0]['timestamps']))
    return render_template("mvSense.html",data=data)

@app.route('/cmxActivity',methods=['GET','POST'])
def cmxActivity():
    # open cmx data
    data = []
    with open('cmxData.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        count = 0
        arrayCount=0
        flag=0
        for row in reader:
            if row['MAC'] != '' and flag==0:
                count = 0
                flag = 1
                data.append({'MAC':row['MAC'],'timestamps':{count:row['time']}})
            elif row['MAC'] != '' and flag==1:
                arrayCount = arrayCount+1
                count = 0
                data.append({'MAC':row['MAC'],'timestamps':{count:row['time']}})
            elif row['MAC'] == '':
                count = count+1
                data[arrayCount]['timestamps'][count]=row['time']
    newData = computeCMXActivity(data)
    print(newData)
    return render_template("cmxActivity.html",x=newData)


@app.route('/mvActivity',methods=['GET','POST'])
def mvActivity():
    # open mv sense data
    data = []
    with open('mvData.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        count = 0
        arrayCount=0
        flag=0
        for row in reader:
            data.append({'timeIn':row['Time In'],'timeOut':row['Time Out'],'count':row['Count']})
    newData = computeMVActivity(data)
    # print(len(data[0]['timestamps']))
    return render_template("mvActivity.html",x=newData)

@app.route('/correlation',methods=['GET','POST'])
def correlation():
    # open cmx data
    data = []
    with open('cmxData.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        count = 0
        arrayCount=0
        flag=0
        for row in reader:
            if row['MAC'] != '' and flag==0:
                count = 0
                flag = 1
                data.append({'MAC':row['MAC'],'timestamps':[{'ts':row['time'],'rssi':row['rssi']}]})
            elif row['MAC'] != '' and flag==1:
                arrayCount = arrayCount+1
                count = 0
                data.append({'MAC':row['MAC'],'timestamps':[{'ts':row['time'],'rssi':row['rssi']}]})
            elif row['MAC'] == '':
                count = count+1
                data[arrayCount]['timestamps'].append({'ts':row['time'],'rssi':row['rssi']})
    # open mv sense data
    mvData = []
    with open('mvData.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        count = 0
        arrayCount=0
        flag=0
        for row in reader:
            mvData.append({'timeIn':row['Time In'],'timeOut':row['Time Out'],'count':row['Count']})
    newData = getCorrelation(data,mvData)
    return render_template("correlation.html",correlation=newData)



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)
    # app.debug=True
    # app.run()
