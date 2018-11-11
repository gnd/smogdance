#!/usr/bin/env python
# # -*- coding: utf-8 -*-

""" Smogdance

    An open-source collection of scripts to collect, store and graph air quality data
    from publicly available sources.

    This fixes old versions of CHMI spider files to not search sensor values according to the number of the table row
    but according to the unique name each sensor has in the CHMI system (eg. AKALA for Karlin, Prague).
    This is much better as it doesnt break when a new sensor is introduced or an old one removed from the CHMI website.

   gnd, 2018
"""

import os
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import shlex
import MySQLdb
import subprocess
import unicodedata
import ConfigParser

### Import smog functions
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from smog_functions import *

### load config
settings_file = os.path.join(sys.path[0], '../settings_python')
config = ConfigParser.ConfigParser()
config.readfp(open(settings_file))
DATA_DIR = config.get('globals', 'DATA_DIR')
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
db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME, charset='utf8')
cur = db.cursor()

### First fix xpath in the database
country = 'cz'
query = "SELECT id, local_id, city, link_web, link_src, link_xpaths FROM %s WHERE country = '%s' and type ='hourly' ORDER BY id" % (DB_TABLE, country)
try:
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)

### Get spider UID (eg. AKALA) and use it to rwrite the xpath queries
for line in cur.fetchall():
    spider_id = line[0]
    spider_local_id = line[1]
    city = line[2]
    spider_uid = line[3].split("mp_")[1].split("_CZ")[0]
    link_src = line[4]
    spider_xpaths = line[5]
    new_xpath = ""
    for xpath in spider_xpaths.split(";"):
        subname = xpath.split("--")[0]
        subrow = xpath.split("--")[1].split("td[")[1].split("]")[0]     # this is the number of the <td> element of the given <tr> in the CHMI table
        newpath = "%s--%s:%s--%s" % (subname, spider_uid, subrow, "cz_chmi")
        new_xpath = new_xpath + ";" + newpath

    ### Now store the new xpath in the table
    query = "UPDATE %s SET link_xpaths = '%s' WHERE id = %s" % (DB_TABLE, new_xpath[1:], spider_id)
    try:
        cur.execute(query)
    except:
        sys.exit("Something went wrong: " + query)

    ### Check if the directories are created
    city_dir = city.replace(" ", "_")
    if (not os.path.isdir("%s/%s" % (SPIDER_DIR, country))):
        os.makedirs("%s/%s" % (SPIDER_DIR, country))
    if (not os.path.isdir("%s/%s/%s" % (SPIDER_DIR, country, city_dir))):
        os.makedirs("%s/%s/%s" % (SPIDER_DIR, country, city_dir))

    ### Create the new spider file
    spider_name = str(spider_local_id)
    print spider_name
    spider_file = "%s/%s/%s/%s.py" % (SPIDER_DIR, country, city_dir, spider_name)
    template = fill_spider_template("../"+SPIDER_TEMPLATE, spider_name, link_src, new_xpath[1:])
    write_template(spider_file, template)

db.commit()
db.close()
