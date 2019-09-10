from flask import Blueprint, request

from db import get_db

import time

api = Blueprint('api', __name__)

@api.route('/')
def apiMain():
    print(get_db())
    return 'Web docs soon, read code or md file for now.'

#Uses <sensorName> allows it to catch any, so that when data is GET or POST-ed it can go to a specific sensor's data.
@api.route('/data/sensor/<sensorName>', methods=["GET", "POST"])
def dataInput(sensorName):
    if request.method == "POST":
        #Incoming data, add to database
        data = request.json
        sensorID = data['sensorID']
        temperature = data['temperature']
        humidity = data['humidity']
        #Insert to database.
        db = get_db()
        cur = db.cursor()
        cur.execute('INSERT INTO SensorData(sensorID, time, temperature, humidity) VALUES (?, ?, ?, ?)', (sensorID, int(time.time()), temperature, humidity))
        db.commit()
    elif request.method == "GET":
        #Retrieve last 5 data points from database, make it into a json structure and hand it back.
        db = get_db()
        cur = db.cursor()
        rows = cur.execute('SELECT * FROM SensorData WHERE sensorID == 0 LIMIT 5')
        out = {}
        out['sensorName'] = 'test'
        out['data'] = []
        for row in rows:
            this = {}
            this['time'] = row[2]
            this['temperature'] = row[3]
            this['humidity'] = row[4]
            out['data'].append(this)
        return out

    return sensorName