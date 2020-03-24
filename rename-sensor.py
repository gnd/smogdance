#!/usr/bin/env python
# # -*- coding: utf-8 -*-

""" Smogdance

    An open-source collection of scripts to collect, store and graph air quality data
    from publicly available sources.

    This renames a sensor on disk and in the database:
        - renames sensor in the database
        - recreates sensor spiderfile
        - deletes & regenerates mrtg config files
        - recreates the city's mrtg index files

    gnd, 2017 - 2020
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
DATA_DIR = config.get('globals', 'DATA_DIR')
TEMP_DIR = config.get('globals', 'TEMP_DIR')
STATS_DIR = config.get('globals', 'STATS_DIR')
STATS_DIR_DEL = config.get('globals', 'STATS_DIR_DEL')
SPIDER_DIR = config.get('globals', 'SPIDER_DIR')
MRTG_TEMPLATE = config.get('globals', 'MRTG_TEMPLATE')
SPIDER_TEMPLATE = config.get('globals', 'SPIDER_TEMPLATE')
SPIDER_COMMAND = config.get('globals', 'SPIDER_COMMAND')

### connect to the db
DB_HOST = config.get('database', 'DB_HOST')
DB_USER = config.get('database', 'DB_USER')
DB_PASS = config.get('database', 'DB_PASS')
DB_NAME = config.get('database', 'DB_NAME')
DB_TABLE = config.get('database', 'DB_TABLE')
DB_TABLE_DEL = config.get('database', 'DB_TABLE_DEL')
DATA_TABLE = config.get('database', 'DATA_TABLE')
DATA_TABLE_DEL = config.get('database', 'DATA_TABLE_DEL')
db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME, use_unicode=True, charset="utf8")
cur = db.cursor()

### Import Smog functions
from smog_functions import *

def usage():
    print "Usage: rename-sensor.py <sensor_id> <new_name>"

### check input
sensor_id = ""
if (len(sys.argv) > 2):
    if (sys.argv[1].isdigit()):
        sensor_id = int(sys.argv[1])
    else:
        sys.exit("Sensor id must be an integer")
        usage()
        sys.exit()
    # escape new sensor name
    new_name = db.escape_string(sys.argv[2])
else:
    print("Not enough parameters")
    usage()
    sys.exit()


#####
##### Get sensor params
#####
query = "SELECT local_id, name, city, country, substances, link_src, link_xpaths FROM %s where id = '%d'" % (DB_TABLE, sensor_id)
cur.execute(query)
for line in cur.fetchall():
    local_id = line[0]
    name = line[1]
    city = line[2]
    country = line[3]
    substances = line[4]
    link_src = line[5]
    link_xpaths = line[6]
    city_dir = city.replace(" ", "_")


#####
##### Update sensor name in the database
#####
query = "UPDATE %s set name = '%s' WHERE id = '%d'" % (DB_TABLE, new_name, sensor_id)
try:
    print "Updating sensor name in the database"
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)
db.commit()


#####
##### Recreate spider file
#####
spider_file = "%s/%s/%s/%s.py" % (SPIDER_DIR, country, city_dir, local_id)
template = fill_spider_template(TEMP_DIR, SPIDER_TEMPLATE, new_name, link_src, link_xpaths)
write_template(spider_file, template)


#####
##### Regenerate mrtg config files
#####
# Create a list of all city substances
city_substances = []
query = "SELECT substances FROM %s WHERE city = '%s' ORDER BY local_id" % (DB_TABLE, city)
try:
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)
for line in cur.fetchall():
    temp_substances = line[0].split()
    for temp_substance in temp_substances:
        if temp_substance not in city_substances:
            city_substances.append(temp_substance)

# Delete old mrtg config files
for substance in city_substances:
    mrtg_name = "%s.cfg" % (substance)
    mrtg_file = "%s/%s/%s/%s" % (SPIDER_DIR, country, city_dir, mrtg_name)
    if os.path.isfile(mrtg_file):
        os.remove(mrtg_file)

# Now create new mrtg config files
query = "SELECT id, local_id, name, substances FROM %s WHERE city = '%s' ORDER BY id" % (DB_TABLE, city)
try:
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)
### create new sensor spider on disk
for line in cur.fetchall():
    temp_sensor_id = line[0]
    temp_local_id = line[1]
    temp_name = line[2]
    temp_substances = line[3]
    for temp_substance in temp_substances.split():
        mrtg_name = "%s.cfg" % (temp_substance)
        print "Recreating %s" % (mrtg_name)
        mrtg_workdir = "%s/%s/%s/" %(STATS_DIR, country, city_dir)
        mrtg_file = "%s/%s/%s/%s" % (SPIDER_DIR, country, city_dir, mrtg_name)
        template = fill_mrtg_template(DATA_DIR, SPIDER_COMMAND, MRTG_TEMPLATE, temp_sensor_id, temp_local_id, temp_name, city, country, temp_substance)
        write_mrtg_template(mrtg_file, mrtg_workdir, template)


#####
##### Done
#####
print "Sensor %s from %s with local_id %d and id %d renamed to %s." % (name, city, local_id, sensor_id, new_name)
