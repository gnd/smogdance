#!/usr/bin/env python
# # -*- coding: utf-8 -*-

""" Smogdance

    An open-source collection of scripts to collect, store and graph air quality data
    from publicly available sources.

    This creates a new special sensor. In particular it:
    - adds a special sensor defition to the database
    - adds spiderfile to disk

    Note:
    A special sensor is eg. a sensor that just downloads a bigger
    chunk of data for later processing by 'normal' sensors,
    such as chmi or shmu pages, thus saving total requests sent

    gnd, 2017 - 2020
"""

import os
import sys
import shlex
import MySQLdb
import subprocess
import ConfigParser

### load config
settings_file = os.path.join(sys.path[0], 'settings_python')
config = ConfigParser.ConfigParser()
config.readfp(open(settings_file))
PARAMS = 7
TEMP_DIR = config.get('globals', 'TEMP_DIR')
SPIDER_DIR = config.get('globals', 'SPIDER_DIR')
SPIDER_TEMPLATE = config.get('globals', 'SPIDER_TEMPLATE')
SPIDER_TEMPLATE_PL = config.get('globals', 'SPIDER_TEMPLATE_PL')

### check if proper arguments
if (len(sys.argv) < PARAMS):
    sys.exit("Not enough arguments.\nUsage: ./add-special-sensor.py <name> <link_src> <checkpoints> <response_size> <country> <city> <type>")
else:
    try:
        response_size = int(sys.argv[4])
    except:
        sys.exit("Bad size parameter: %s\nUsage: ./add-special-sensor.py <name> <link_src> <checkpoints> <response_size> <country> <city> <type>" % (sys.argv[4]))


### initial checks
if (len(sys.argv) < PARAMS):
    sys.exit("Not enough parameters")


### connect to the db
DB_HOST = config.get('database', 'DB_HOST')
DB_USER = config.get('database', 'DB_USER')
DB_PASS = config.get('database', 'DB_PASS')
DB_NAME = config.get('database', 'DB_NAME')
DB_TABLE = config.get('database', 'DB_TABLE')
db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME, use_unicode=True, charset="utf8")
cur = db.cursor()

from smog_functions import *

### process input
name = sys.argv[1]
link_src = sys.argv[2]
checkpoints = sys.argv[3]
response_size = int(sys.argv[4])
country = sys.argv[5]
city = sys.argv[6]
type = sys.argv[7]

checks = str(response_size) + '===' + checkpoints

### execute query
print "Inserting %s-%s into db" % ("special", name)
query = "INSERT INTO %s VALUES(0,'%d','%s','%s','','','%s','%s','','','%s','', now(), %d, '%d', '%d')" % (DB_TABLE, 0, name, link_src, checks, country, type, 0, 0, 1)
cur.execute(query)
db.commit()
id = int(cur.lastrowid)
db.close()

### check if the directories are created
if (not os.path.isdir("%s/%s" % (SPIDER_DIR, country))):
    os.makedirs("%s/%s" % (SPIDER_DIR, country))

### create new sensor spider on disk
spider_name = "special-%s" % (name)
spider_file = "%s/%s/%s.py" % (SPIDER_DIR, country, spider_name)
if ((country == 'pl') and (name == 'gios')):
    param_arr = type.split('--')
    decrypt_rounds = param_arr[0]
    decrypt_hashfunc = param_arr[1]
    decrypt_salt = param_arr[2]
    decrypt_iv = param_arr[3]
    link_csrf = link_src
    link_aqi = param_arr[4]
    data_regexp = param_arr[5]
    template = fill_special_spider_template_pl(TEMP_DIR, SPIDER_TEMPLATE_PL, name, decrypt_rounds, decrypt_hashfunc, decrypt_salt, decrypt_iv, link_csrf, link_aqi, data_regexp)
else:
    template = fill_special_spider_template(TEMP_DIR, SPIDER_TEMPLATE, name, link_src, checks, type)
write_template(spider_file, template)
