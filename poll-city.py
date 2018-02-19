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
from tabulate import tabulate

### load config
settings_file = os.path.join(sys.path[0], 'settings_python')
config = ConfigParser.ConfigParser()
config.readfp(open(settings_file))

args = 2 # $0, sensor_id
all_substances = ["co","no2","o3","pm10","pm25","so2"]
#//TODO - allow for single substance selection (like in poll-sensor)

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
query = "SELECT id, name, substances from %s WHERE city = \"%s\"" % (DB_TABLE, city)
try:
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)

table = []
table.append(["city","name"] + all_substances)
### get last data for the sensors
for line in cur.fetchall():
    row = []
    sensor_id = line[0]
    name = line[1]
    sensor_substances = line[2]
    row.append(city)
    row.append(name)
    query_substances = ', '.join([str(x) for x in all_substances])
    query = "SELECT %s from %s_temp WHERE sensor_id = %d" % (query_substances, DATA_TABLE, sensor_id)
    try:
        cur.execute(query)
    except:
        sys.exit("Something went wrong: " + query)
    data = cur.fetchone()
    i = 0
    for substance in all_substances:
        if substance in sensor_substances:
            row.append(data[i])
        else:
            row.append('-')
        i+=1
    table.append(row)

db.close()

### print output
print tabulate(table)
