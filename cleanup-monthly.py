#!/usr/bin/env python
# # -*- coding: utf-8 -*-

""" Smogdance

    An open-source collection of scripts to collect, store and graph air quality data
    from publicly available sources.

    This runs once daily to remove records older than 30 days
    from the DATA_TABLE_MONTH table

    gnd, 2017 - 2018
"""

import os
import sys
import time
import shlex
import MySQLdb
import subprocess
import ConfigParser

### load config
settings_file = os.path.join(sys.path[0], 'settings_python')
config = ConfigParser.ConfigParser()
config.readfp(open(settings_file))

### connect to the db
DB_HOST = config.get('database', 'DB_HOST')
DB_USER = config.get('database', 'DB_USER')
DB_PASS = config.get('database', 'DB_PASS')
DB_NAME = config.get('database', 'DB_NAME')
DATA_TABLE_MONTH = config.get('database', 'DATA_TABLE_MONTH')
db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME, use_unicode=True, charset="utf8")
cur = db.cursor()

#####
##### Remove records older than 30 days
#####
query = "DELETE FROM %s where timestamp < DATA_SUB(now() - INTERVAL 30 day)" % (DATA_TABLE_MONTH)
cur.execute(query)
db.commit()
db.close()
