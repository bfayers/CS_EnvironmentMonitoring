# API Documentation

## Uploading Data
POST to `/api/data/sensor/<sensorName>` with JSON of the following structure:
```
{
    "temperature": 21,
    "humidity": 40
}
```

## Retrieving Data
GET on `/api/data/sensor/<sensorName>` and receive:
```
{
    "sensorName": "TestSensor",
    "data": [
        {"time": 1565001255, "temperature": 30, "humidity": 65},
        {"time": 1565001840, "temperature": 31.4, "humidity": 64},
        {"time": 1565002440, "temperature": 33, "humidity": 62},
        {"time": 1565003040, "temperature": 35, "humidity": 57},
        {"time": 1565003640, "temperature": 35, "humidity": 57}
    ]
}
```

You can request more data by using parameters on the URL such as `?amount=10`