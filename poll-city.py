#!/usr/bin/env python
# # -*- coding: utf-8 -*-

""" Smogdance

    An open-source collection of scripts to collect, store and graph air quality data
    from publicly available sources.

    This polls SQL for the latest values of all sensors from a given city.

    gnd, 2017 - 2018
"""

import os
import sys
import MySQLdb
import ConfigParser
#//TODO - add tabulate into dependencies
from tabulate import tabulate

### load config
settings_file = os.path.join(sys.path[0], 'settings_python')
config = ConfigParser.ConfigParser()
config.readfp(open(settings_file))

args = 2 # $0, sensor_id
#//TODO - allow for single substance selection (like in poll-sensor)
#substances = ["co","no2","o3","pm10","pm25","so2", "all"]

### check if proper arguments
if (len(sys.argv) < args):
    sys.exit("Not enough arguments.\nUsage: poll-city.py <city>")
else:
    #//TODO - sanitize input in poll-city
    city = sys.argv[1]
    #substance = sys.argv[2]
    #if (substance not in substances):
    #    sys.exit("Unknown substance: %s\nUsage: poll-city.py <city> <substance | all>" % (substance))

### connect to the db
DB_HOST = config.get('database', 'DB_HOST')
DB_USER = config.get('database', 'DB_USER')
DB_PASS = config.get('database', 'DB_PASS')
DB_NAME = config.get('database', 'DB_NAME')
DB_TABLE = config.get('database', 'DB_TABLE')
DATA_TABLE = config.get('database', 'DATA_TABLE')
db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
cur = db.cursor()

### get list of sensors for the city
query = "SELECT id, name from %s WHERE city = \"%s\"" % (DB_TABLE, city)
try:
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)

table = []
table.append(["city","name","co","no2","o3","pm10","pm25","so2"])
### get last data for the sensors
for line in cur.fetchall():
    print line
    row = []
    sensor_id = line[0]
    name = line[1]
    row.append(city)
    row.append(name)
    query = "SELECT co, no2, o3, pm10, pm25, so2 from %s_temp WHERE sensor_id = %d" % (DATA_TABLE, sensor_id)
    print query
    try:
        cur.execute(query)
    except:
        sys.exit("Something went wrong: " + query)
    data = cur.fetchone()
    for substance in data:
        row.append(substance)
    table.append(row)

db.close()

### print output
print tabulate(table)
