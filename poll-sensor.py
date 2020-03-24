#!/usr/bin/env python
# # -*- coding: utf-8 -*-

""" Smogdance

    An open-source collection of scripts to collect, store and graph air quality data
    from publicly available sources.

    This polls SQL for the latest values of sensor data to be used by mrtg.

    gnd, 2017 - 2018
"""

import os
import sys
import MySQLdb
import ConfigParser

### load config
settings_file = os.path.join(sys.path[0], 'settings_python')
config = ConfigParser.ConfigParser()
config.readfp(open(settings_file))

args = 3 # $0, sensor_id, substance
substances = ["co","no2","o3","pm10","pm25","so2"]

### check if proper arguments
if (len(sys.argv) < args):
    sys.exit("Not enough arguments.\nUsage: poll-sensor.py <id> <substance>")
else:
    try:
        sensor_id = int(sys.argv[1])
    except:
        sys.exit("Bad id parameter: %s\nUsage: poll-sensor.py <id> <substance>" % (sys.argv[1]))
    substance = sys.argv[2]
    if (substance not in substances):
        sys.exit("Unknown substance: %s\nUsage: poll-sensor.py <id> <substance>" % (substance))


### connect to the db
DB_HOST = config.get('database', 'DB_HOST')
DB_USER = config.get('database', 'DB_USER')
DB_PASS = config.get('database', 'DB_PASS')
DB_NAME = config.get('database', 'DB_NAME')
DB_TABLE = config.get('database', 'DB_TABLE')
DATA_TABLE = config.get('database', 'DATA_TABLE')
db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME, use_unicode=True, charset="utf8")
cur = db.cursor()

### get last data for the sensor
query = "SELECT %s from %s_temp WHERE sensor_id = %d" % (substance, DATA_TABLE, sensor_id)
try:
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)

data = cur.fetchone()
db.close()

### print for mrtg
if (data):
    if (data[0] is not None):
        data = data[0]
        print "%d\n%d\n%d\n%d" % (int(data), int(data), int(data), int(data))
    else:
        sys.exit("No data")
else:
    sys.exit("No data")
