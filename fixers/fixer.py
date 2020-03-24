#!/usr/bin/env python
# # -*- coding: utf-8 -*-

""" Smogdance

    An open-source collection of scripts to collect, store and graph air quality data
    from publicly available sources.

    This does some early - now useless fixing

    gnd, 2018
"""

import os
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import MySQLdb
import ConfigParser

### load config
settings_file = os.path.join(sys.path[0], 'settings_python')
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

# 1. all having x>0 get x+17 - fixing AT - 26.2.2018
query = "SELECT id, link_xpaths from %s WHERE link_xpaths like '%%table[3]%%'" % (DB_TABLE)
try:
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)

for line in cur.fetchall():
    id = line[0]
    xpath = line[1]
    xx = xpath.split('odd"][')[1].split(']')[0]
    if (int(xx) > 0):
        xpath = xpath.replace('odd"]['+xx,'odd"]['+str(int(xx)+17))
        query = "UPDATE %s set link_xpaths = '%s' WHERE id = %d" % (DB_TABLE, xpath, id)
    try:
        cur.execute(query)
    except:
        sys.exit("Something went wrong: " + query)
    db.commit()
