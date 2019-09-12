from flask import Blueprint, request

from db import get_db

import time

import hashlib

api = Blueprint('api', __name__)

@api.route('/')
def apiMain():
    print(get_db())
    return 'Web docs soon, read code or md file for now.'


@api.route('/create/user', methods=["POST"])
def createUser():
    data = request.json
    username = data['username']
    password = data['password']
    password_hash = hashlib.sha256()
    password_hash.update(password.encode('utf=8'))
    password_hash = password_hash.hexdigest()
    db = get_db()
    cur = db.cursor()
    #Check if the username is taken
    cur.execute('SELECT * FROM Users WHERE userName=?', (username,))
    out = {}
    rows = cur.fetchall()
    if len(rows) != 0:
        out['status'] = 'fail'
        out['reason'] = 'Username already taken'
        return out
    else:
        cur.execute('INSERT INTO Users(userName, userPassword) VALUES (?, ?)', (username, password_hash))
        db.commit()
        userId = cur.lastrowid
        out['status'] = 'success'
        out['userId'] = userId
        out['userName'] = username
        return out


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