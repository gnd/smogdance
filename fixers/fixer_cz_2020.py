#!/usr/bin/env python
# # -*- coding: utf-8 -*-

""" Smogdance

    An open-source collection of scripts to collect, store and graph air quality data
    from publicly available sources.

    This does some fixing of SK spiders (March, 2020)

    gnd, 2020
"""

import os
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import shlex
import MySQLdb
import subprocess
import ConfigParser

### Import smog functions
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from smog_functions import *

### load config
settings_file = os.path.join(sys.path[0], '../settings_python')
config = ConfigParser.ConfigParser()
config.readfp(open(settings_file))
DATA_DIR = config.get('globals', 'DATA_DIR')
TEMP_DIR = config.get('globals', 'TEMP_DIR')
STATS_DIR = config.get('globals', 'STATS_DIR')
SPIDER_DIR = config.get('globals', 'SPIDER_DIR')
MRTG_TEMPLATE = config.get('globals', 'MRTG_TEMPLATE')
SPIDER_TEMPLATE = config.get('globals', 'SPIDER_TEMPLATE')
SPIDER_COMMAND = config.get('globals', 'SPIDER_COMMAND')

all_substances = ["co","no2","o3","pm10","pm25","so2"]

### connect to the db
DB_HOST = config.get('database', 'DB_HOST')
DB_USER = config.get('database', 'DB_USER')
DB_PASS = config.get('database', 'DB_PASS')
DB_NAME = config.get('database', 'DB_NAME')
DB_TABLE = config.get('database', 'DB_TABLE')
DATA_TABLE = config.get('database', 'DATA_TABLE')
db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
cur = db.cursor()

# 0. replace - :6- > :5- :7- > :6- :8- > :7- :9- > :8- :10- > :9- :11- > :10-
query = "SELECT id, link_xpaths from %s WHERE country = 'cz' and type = 'hourly'" % (DB_TABLE)
try:
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)

for line in cur.fetchall():
    id = line[0]
    xpaths = line[1]
    #xpaths = xpaths.replace(':6-',':5-')
    #xpaths = xpaths.replace(':7-',':6-')
    #xpaths = xpaths.replace(':8-',':7-')
    xpaths_arr = xpaths.split(';')
    xpaths_new_arr = []
    for xpath in xpaths_arr:
        if 'pm10' in xpath:
            xpath = xpath.replace(':9-',':8-')
        xpaths_new_arr.append(xpath)
    xpaths = ';'.join(xpaths_new_arr)
    #xpaths = xpaths.replace(':11-',':9-')
    #xpaths = xpaths.replace(':13-',':11-')
    query = "UPDATE %s set link_xpaths = '%s' WHERE id = %d" % (DB_TABLE, xpaths, id)
    try:
        cur.execute(query)
    except:
        sys.exit("Something went wrong: " + query)
    db.commit()

# 2. Recreate spider files on disk
query = "SELECT local_id, name, country, city, link_src, link_xpaths FROM %s WHERE country = 'cz' and type = 'hourly' ORDER BY id" % (DB_TABLE)
try:
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)

### create new sensor spider on disk
for line in cur.fetchall():
    spider_name = line[0]
    name = line[1]
    country = line[2]
    city_dir = line[3].replace(" ", "_")
    link_src = line[4]
    link_xpaths = line[5]

    ### check if the directories are created
    if (not os.path.isdir("%s/%s" % (SPIDER_DIR, country))):
        os.makedirs("%s/%s" % (SPIDER_DIR, country))
    if (not os.path.isdir("%s/%s/%s" % (SPIDER_DIR, country, city_dir))):
        os.makedirs("%s/%s/%s" % (SPIDER_DIR, country, city_dir))

    ### create the new spider file
    spider_file = "%s/%s/%s/%s.py" % (SPIDER_DIR, country, city_dir, spider_name)
    template = fill_spider_template(TEMP_DIR, SPIDER_TEMPLATE, name, link_src, link_xpaths)
    write_template(spider_file, template)
