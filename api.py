from flask import Blueprint, request, make_response

from db import get_db

import time

import hashlib, string, random

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

@api.route('/delete/user', methods=["DELETE"])
def deleteUser():
    data = request.json
    username = data['username']
    userCookie = request.cookies.get('userCookie')
    #Check if cookie matches stored cookie
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT userCookie, cookieExpiry FROM Users WHERE userName=?', (username,))
    row = cur.fetchone()
    out = {}
    try:
        if row[0] == userCookie:
            #Checks if used cookie is expired or not
            if row[1] >= int(time.time()):
                cur.execute('DELETE FROM Users WHERE userName=?', (username,))
                db.commit()
                out['status'] = 'success'
            else:
                out['status'] = 'fail'
                out['reason'] = 'Expired Cookie'
        else:
            out['status'] = 'fail'
            out['reason'] = 'Invalid Cookie'
        return out
    except Exception as e:
        print(e)
        out['status'] = 'fail'
        out['reason'] = 'Unknown Error'
        return out

@api.route('/user/login', methods=["POST"])
def userLogin():
    data = request.json
    username = data['username']
    password = data['password']
    password_hash = hashlib.sha256()
    password_hash.update(password.encode('utf=8'))
    password_hash = password_hash.hexdigest()
    #Check if password matches
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT userPassword FROM Users WHERE userName=?', (username,))
    row = cur.fetchone()
    out = {}
    if row[0] == password_hash:
        #Password Matches!
        cookie = ''
        for i in range(0,128):
            cookie += random.choice(random.choice([string.ascii_letters, string.ascii_lowercase, string.digits]))
        out['status'] = 'success'
        out['cookie'] = cookie
        reply = make_response(out)
        reply.set_cookie('userCookie', cookie, max_age=60*60*24)
        cur.execute('UPDATE Users SET userCookie=?, cookieExpiry=? WHERE userName=?', (cookie, int(time.time())+60*60*24, username,))
        db.commit()
    else:
        out['status'] = 'fail'
        out['reason'] = 'Incorrect Password'
        reply = make_response(out)
    return reply
    
@api.route('/create/key', methods=["POST"])
def createApiKey():
    data = request.json
    username = data['username']
    userCookie = request.cookies.get('userCookie')
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT userID, cookieExpiry FROM Users WHERE userCookie=? AND userName=?', (userCookie,username,))
    row = cur.fetchone()
    out = {}
    if row == None:
        out['status'] = 'fail'
        out['reason'] = 'Invalid Cookie or Username'
        return out
    else:
        #Check if the cookie is still valid
        if row[1] >= int(time.time()):
            #Cookie is still valid!
            #Create the api key
            newKey = ""
            for i in range(0,16):
                newKey += random.choice(random.choice([string.ascii_letters, string.ascii_lowercase, string.digits]))
            cur.execute('INSERT INTO APIKeys(apiKey, userID) VALUES (?, ?)', (newKey, row[0]))
            db.commit()
            out['status'] = 'success'
            out['key'] = newKey
        else:
            out['status'] = 'fail'
            out['reason'] = 'Expired Cookie'
        return out

@api.route('/delete/key', methods=["DELETE"])
def deleteApiKey():
    data = request.json
    username = data['username']
    apiKey = data['apiKey']
    userCookie = request.cookies.get('userCookie')
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT userID, cookieExpiry FROM Users WHERE userCookie=? AND userName=?', (userCookie,username,))
    row = cur.fetchone()
    out = {}
    if row == None:
        out['status'] = 'fail'
        out['reason'] = 'Invalid Cookie or Username'
        return out
    else:
        #Check if the cookie is still valid
        if row[1] >= int(time.time()):
            #Cookie is still valid!
            #Delete the api key
            cur.execute('DELETE FROM APIKeys WHERE apiKey=?', (apiKey,))
            db.commit()
            out['status'] = 'success'
        else:
            out['status'] = 'fail'
            out['reason'] = 'Expired Cookie'
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