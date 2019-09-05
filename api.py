from flask import Blueprint, request

api = Blueprint('api', __name__)

@api.route('/')
def apiMain():
    return 'Web docs soon, read code or md file for now.'

#Uses <path:path> allows it to catch any, so that when data is GET or POST-ed it can go to a specific sensor's data.
@api.route('/data/sensor/<sensorName>', methods=["GET", "POST"])
def dataInput(sensorName):
    if request.method == "POST":
        #Incoming data, add to database
        data = request.json
        temperature = data['temperature']
        humidity = data['humidity']
        #Insert to database.
    elif request.method == "GET":
        #Retrieve last 5 data points from database, make it into a json structure and hand it back.
    return sensorName