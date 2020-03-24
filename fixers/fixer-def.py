#!/usr/bin/env python
# # -*- coding: utf-8 -*-

""" Smogdance

    An open-source collection of scripts to collect, store and graph air quality data
    from publicly available sources.

    This outputs current sensor definitions from the database to the console.

    gnd, 2018
"""

import os
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import MySQLdb
import ConfigParser

### load config
settings_file = os.path.join(sys.path[0], '../settings_python')
config = ConfigParser.ConfigParser()
config.readfp(open(settings_file))

all_substances = ["co","no2","o3","pm10","pm25","so2"]

### connect to the db
DB_HOST = config.get('database', 'DB_HOST')
DB_USER = config.get('database', 'DB_USER')
DB_PASS = config.get('database', 'DB_PASS')
DB_NAME = config.get('database', 'DB_NAME')
DB_TABLE = config.get('database', 'DB_TABLE')
DATA_TABLE = config.get('database', 'DATA_TABLE')
db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME, use_unicode=True, charset="utf8")
cur = db.cursor()

countries = ['at','cz','pl']
for country in countries:
    query = "SELECT name, link_src, link_web, link_stat, link_xpaths, country, city, gps, type, substances FROM %s WHERE country = '%s' ORDER BY id" % (DB_TABLE, country)
    try:
        cur.execute(query)
    except:
        sys.exit("Something went wrong: " + query)

    for l in cur.fetchall():
        print "'%s' '%s' '%s' '%s' '%s' '%s' '%s' '%s' '%s' '%s'" % (l[0],l[1].replace('/data/www/smog.dance/smogdance/temp','TEMP_DIR'),l[2],l[3].replace('stats.smog.dance','STATS_URL'),l[4],l[5],l[6],l[7],l[8],l[9])
