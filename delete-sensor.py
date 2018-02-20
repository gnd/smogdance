#!/usr/bin/env python
# # -*- coding: utf-8 -*-

""" Smogdance

    An open-source collection of scripts to collect, store and graph air quality data
    from publicly available sources.

    (Skeleton) This removes a sensor from disk and database:
        - moves the sensor record from sensors to sensors_removed in the db TODO
        - moves all historical data associated with the sensor from sensors_data to sensors_data_deleted TODO
        - deletes sensor spiderfile from the disk TODO
        - recreates the city's sensor local id's (or deletes the city spider dir if only sensor) TODO
        - recreates the city's mrtg directory (or deletes it if only sensor) TODO

    gnd, 2017 - 2018
"""

import os
import sys
import time
import shlex
import MySQLdb
import datetime
import subprocess
import ConfigParser

### load config
settings_file = os.path.join(sys.path[0], 'settings_python')
config = ConfigParser.ConfigParser()
config.readfp(open(settings_file))
STATS_DIR = config.get('globals', 'STATS_DIR')

### connect to the db
DB_HOST = config.get('database', 'DB_HOST')
DB_USER = config.get('database', 'DB_USER')
DB_PASS = config.get('database', 'DB_PASS')
DB_NAME = config.get('database', 'DB_NAME')
DB_TABLE = config.get('database', 'DB_TABLE')
DATA_TABLE = config.get('database', 'DATA_TABLE')
db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
cur = db.cursor()

### check input TODO (sanitize like in poll-city)
sensor_id = ""
if (len(sys.argv) > 1):
    sensor_id = int(sys.argv[1])
else:
    sys.exit("Not enough parameters")

#####
##### Get sensor params
#####
query = "SELECT local_id, name, city, country, substances FROM %s where id = '%d'" % (DB_TABLE, sensor_id)
cur.execute(query)
for line in cur.fetchall():
    local_id = line[0]
    name = line[1]
    city = line[2]
    country = line[3]
    substances = line[4]

#####
##### Move the db data TODO
#####

#####
##### Delete spider file from disk TODO
#####

#####
##### Recreate local ids, spider files and mrtg TODO
#####

#####
##### Recreate mrtg stats for city TODO
#####



    sensor_id = row[0]
    sensor_local_id = row[1]
    sensor_country = row[2]
    sensor_city = row[3]
    sensor_substances = row[4].split()
    print "Repopulating %s-%d: " % (sensor_city, sensor_local_id)
