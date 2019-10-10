from flask import Blueprint, request, make_response

from db import get_db

import time

import string, random

from argon2 import PasswordHasher
import argon2

api = Blueprint('api', __name__)

def checkAccess(cookieOrKey):
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT userID FROM APIKeys WHERE apiKey=?', (cookieOrKey,))
    row = cur.fetchone()
    if row == None:
        #It might be a cookie not an apiKey
        cur.execute('SELECT userID, cookieExpiry FROM Users WHERE userCookie=?', (cookieOrKey,))
        cookieRow = cur.fetchone()
        if cookieRow == None:
            #No auth
            return -1, 'invalidCookieOrKey'
        else:
            #It's a valid cookie
            #Check expiry
            if cookieRow[1] >= int(time.time()):
                #Valid cookie
                return cookieRow[0], 'validCookie'
            else:
                #Expired cookie
                return -1, 'expiredCookie'
    else:
        #Valid apiKey
        return row[0], 'validApi'


@api.route('/')
def apiMain():
    print(get_db())
    return 'Web docs soon, read code or md file for now.'


@api.route('/create/user', methods=["POST"])
def createUser():
    data = request.json
    username = data['username']
    password = data['password']
    #Initialise password hasher
    password_hasher = PasswordHasher()
    #Hash the password and get a string of hash.
    password_hash = password_hasher.hash(password)
    #Get database connection
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
        #Store username and password hash in database
        cur.execute('INSERT INTO Users(userName, userPassword) VALUES (?, ?)', (username, password_hash))
        db.commit()
        userId = cur.lastrowid
        #Return userID and userName in response
        out['status'] = 'success'
        out['userId'] = userId
        out['userName'] = username
        return out

@api.route('/delete/user', methods=["DELETE"])
def deleteUser():
    #data = request.json
    #username = data['username']
    username = request.args.get('username')
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
    password_hasher = PasswordHasher()
    #Check if password matches
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT userPassword FROM Users WHERE userName=?', (username,))
    row = cur.fetchone()
    out = {}
    if row == None:
        out['status'] = 'fail'
        out['reason'] = 'Username or Password Wrong'
        return out, 403
    try: 
        password_hasher.verify(row[0], password)
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
        return reply, 200
    except argon2.exceptions.VerifyMismatchError:
        out['status'] = 'fail'
        out['reason'] = 'Username or Password Wrong'
        return out, 403
    
@api.route('/create/key', methods=["POST"])
def createApiKey():
    userCookie = request.cookies.get('userCookie')
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT userID, cookieExpiry FROM Users WHERE userCookie=?', (userCookie,))
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
    #data = request.json
    #apiKey = data['apiKey']
    apiKey = request.args.get('key')
    userCookie = request.cookies.get('userCookie')
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT userID, cookieExpiry FROM Users WHERE userCookie=?', (userCookie,))
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

@api.route('/create/sensor', methods=["POST"])
def createSensor():
    data = request.json
    sensorName = data['name']
    sensorLat = data['sensorLat']
    sensorLon = data['sensorLon']
    try:
        apiKey = request.headers['apiKey']
    except KeyError:
        apiKey = None
    db = get_db()
    cur = db.cursor()
    out = {}
    if apiKey != None:
        userID, valid = checkAccess(apiKey)
    else:
        #Get cookie
        userCookie = request.cookies.get('userCookie')
        userID, valid = checkAccess(userCookie)
    if valid == 'validCookie' or valid == 'validApi':
        #Keep going
        pass
    else:
        out['status'] = 'fail'
        out['reason'] = valid
        return out, 403
    cur.execute('INSERT INTO Sensors(sensorName, sensorLat, sensorLon, userID) VALUES (?, ?, ?, ?)', (sensorName, sensorLat, sensorLon, userID,))
    db.commit()
    out['status'] = 'success'
    return out

@api.route('/delete/sensor', methods=["DELETE"])
def deleteSensor():
    #data = request.json
    #sensorName = data['name']
    sensorName = request.args.get('name')
    try:
        apiKey = request.headers['apiKey']
    except KeyError:
        apiKey = None
    db = get_db()
    cur = db.cursor()
    #cur.execute('SELECT userID FROM APIKeys WHERE apiKey=?', (apiKey,))
    #row = cur.fetchone()
    out = {}
    if apiKey != None:
        userID, valid = checkAccess(apiKey)
    else:
        #Get cookie
        userCookie = request.cookies.get('userCookie')
        userID, valid = checkAccess(userCookie)
    if valid == 'validCookie' or valid == 'validApi':
        #Keep going
        pass
    else:
        out['status'] = 'fail'
        out['reason'] = valid
        return out, 403

    cur.execute('DELETE FROM Sensors WHERE sensorName=? AND userID=?', (sensorName, userID,))
    db.commit()
    out['status'] = 'success'
    return out

@api.route('/info/sensor', methods=["GET"])
def getSensorInfo():
    sensorName = request.args.get('sensorName')
    try:
        apiKey = request.headers['apiKey']
    except KeyError:
        apiKey = None
    db = get_db()
    cur = db.cursor()

    out = {}
    if apiKey != None:
        userID, valid = checkAccess(apiKey)
    else:
        #Get cookie
        userCookie = request.cookies.get('userCookie')
        userID, valid = checkAccess(userCookie)
    if valid == 'validCookie' or valid == 'validApi':
        #Keep going
        pass
    else:
        out['status'] = 'fail'
        out['reason'] = valid
        return out
    cur.execute('SELECT * FROM Sensors WHERE sensorName=? AND userID=?', (sensorName, userID,))
    row = cur.fetchone()
    if row == None:
        out['status'] = 'fail'
        out['reason'] = 'Sensor Does Not Exist'
        return out
    out['status'] = 'success'
    out['sensorID'] = row[0]
    out['sensorName'] = row[1]
    out['sensorLat'] = row[2]
    out['sensorLon'] = row[3]
    return out

@api.route('/info/sensors', methods=["GET"])
def listSensors():
    try:
        apiKey = request.headers['apiKey']
    except KeyError:
        apiKey = None
    db = get_db()
    cur = db.cursor()

    out = {}
    if apiKey != None:
        userID, valid = checkAccess(apiKey)
    else:
        #Get cookie
        userCookie = request.cookies.get('userCookie')
        userID, valid = checkAccess(userCookie)
    if valid == 'validCookie' or valid == 'validApi':
        #Keep going
        pass
    else:
        out['status'] = 'fail'
        out['reason'] = valid
        return out
    cur.execute('SELECT sensorID,sensorName FROM Sensors WHERE userID=?', (userID,))
    rows = cur.fetchall()
    out['sensorIDs'] = []
    out['sensorNames'] = []
    for row in rows:
        out['sensorIDs'].append(row[0])
        out['sensorNames'].append(row[1])
    out['status'] = 'success'
    return out

@api.route('/info/keys', methods=["GET"])
def getKeys():
    out = {}
    #Auth
    try:
        apiKey = request.headers['apiKey']
    except KeyError:
        apiKey = None
    if apiKey != None:
        userID, valid = checkAccess(apiKey)
    else:
        #Get cookie
        userCookie = request.cookies.get('userCookie')
        userID, valid = checkAccess(userCookie)
    if valid == 'validCookie' or valid == 'validApi':
        #Keep going
        pass
    else:
        out['status'] = 'fail'
        out['reason'] = valid
        return out, 403
    #DB
    db = get_db()
    cur = db.cursor()
    #Get keys
    cur.execute('SELECT apiKey FROM APIKeys WHERE userID=?', (userID,))
    rows = cur.fetchall()
    out['apiKeys'] = []
    for row in rows:
        out['apiKeys'].append(row[0])
        out['status'] = 'success'
    return out

@api.route('/data/sensor', methods=["GET", "POST"])
def dataInput():
    out = {}
    if request.method == "POST":
        #Auth
        try:
            apiKey = request.headers['apiKey']
        except KeyError:
            apiKey = None
        if apiKey != None:
            userID, valid = checkAccess(apiKey)
        else:
        #Get cookie
            userCookie = request.cookies.get('userCookie')
            userID, valid = checkAccess(userCookie)
        if valid == 'validCookie' or valid == 'validApi':
            #Keep going
            pass
        else:
            out['status'] = 'fail'
            out['reason'] = valid
            return out, 403
        #Incoming data, add to database
        data = request.json
        sensorID = data['sensorID']
        temperature = data['temperature']
        humidity = data['humidity']
        #DB
        db = get_db()
        cur = db.cursor()
        #Is sensor owned by authenticated user
        cur.execute('SELECT userID FROM Sensors WHERE sensorID=?', (sensorID,))
        row = cur.fetchone()
        if row[0] != userID:
            #Not the right user
            out['status'] = 'fail'
            out['reason'] = 'Incorrect Authentication'
            return out, 403
        #Insert to database.
        cur.execute('INSERT INTO SensorData(sensorID, time, temperature, humidity) VALUES (?, ?, ?, ?)', (sensorID, int(time.time()), temperature, humidity))
        db.commit()
        out['status'] = 'success'
        return out
    elif request.method == "GET":
        #Auth
        try:
            apiKey = request.headers['apiKey']
        except KeyError:
            apiKey = None
        if apiKey != None:
            userID, valid = checkAccess(apiKey)
        else:
        #Get cookie
            userCookie = request.cookies.get('userCookie')
            userID, valid = checkAccess(userCookie)
        if valid == 'validCookie' or valid == 'validApi':
            #Keep going
            pass
        else:
            out['status'] = 'fail'
            out['reason'] = valid
            return out, 403
        #DB
        db = get_db()
        cur = db.cursor()
        #Is sensor owned by authenticated user
        sensorID = request.args.get('sensorID')
        cur.execute('SELECT userID FROM Sensors WHERE sensorID=?', (sensorID,))
        row = cur.fetchone()
        if row[0] != userID:
            #Not the right user
            out['status'] = 'fail'
            out['reason'] = 'Incorrect Authentication'
            return out, 403
        #Get sensor details
        sensorDetails = cur.execute('SELECT * FROM Sensors WHERE sensorID = ?', (sensorID,))
        sensorDetails = cur.fetchone()
        #Retrieve last 5 data points from database, make it into a json structure and hand it back.
        rows = cur.execute('SELECT * FROM SensorData WHERE sensorID = ? LIMIT 5', (sensorID,))
        out['sensorID'] = sensorID
        out['sensorLat'] = sensorDetails[2]
        out['sensorLon'] = sensorDetails[3]
        out['sensorName'] = sensorDetails[1]
        out['data'] = []
        for row in rows:
            this = {}
            this['time'] = row[2]
            this['temperature'] = row[3]
            this['humidity'] = row[4]
            out['data'].append(this)
        return out