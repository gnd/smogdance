#!/usr/bin/env python
# # -*- coding: utf-8 -*-

""" Smogdance

    An open-source collection of scripts to collect, store and graph air quality data
    from publicly available sources.

    This creates a new sensor. In particular it:
   - adds a sensor definition to the database
   - creates a spiderfile from a template and adds it to disk
   - creates or updates a mrtg config for the sensor and its substances
   - updates mrtg index for the given city and substances

   gnd, 2017 - 2018
"""

import os
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import shlex
import MySQLdb
import subprocess
import ConfigParser

### load config
settings_file = os.path.join(sys.path[0], 'settings_python')
config = ConfigParser.ConfigParser()
config.readfp(open(settings_file))
DATA_DIR = config.get('globals', 'DATA_DIR')
STATS_DIR = config.get('globals', 'STATS_DIR')
SPIDER_DIR = config.get('globals', 'SPIDER_DIR')
MRTG_TEMPLATE = config.get('globals', 'MRTG_TEMPLATE')
SPIDER_TEMPLATE = config.get('globals', 'SPIDER_TEMPLATE')
SPIDER_COMMAND = config.get('globals', 'SPIDER_COMMAND')

### initial checks
if (len(sys.argv) < 10):
    sys.exit("Not enough parameters")

### connect to the db
DB_HOST = config.get('database', 'DB_HOST')
DB_USER = config.get('database', 'DB_USER')
DB_PASS = config.get('database', 'DB_PASS')
DB_NAME = config.get('database', 'DB_NAME')
DB_TABLE = config.get('database', 'DB_TABLE')
DATA_TABLE = config.get('database', 'DATA_TABLE')
db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
cur = db.cursor()

### Import Smog functions
from smog_functions import *

### process input
name = strip_accents(unicode(sys.argv[1]))
link_src = sys.argv[2]
link_web = sys.argv[3]
link_stat = sys.argv[4]
link_xpaths = sys.argv[5]
country = sys.argv[6]
city = sys.argv[7]
gps = db.escape_string(sys.argv[8])
type = sys.argv[9]
substances = sys.argv[10]

### get sensor id
query = "SELECT count(*) as count from %s WHERE city = '%s'" % (DB_TABLE, city)
cur.execute(query)
num_sensors = int(cur.fetchone()[0])
if (num_sensors > 0):
    query = "SELECT local_id FROM %s WHERE city = '%s' ORDER BY local_id DESC LIMIT 1" % (DB_TABLE, city)
    cur.execute(query)
    # we make this grow monotonicaly so we avoid conflicts in the mrtg config files
    local_id = int(cur.fetchone()[0]) + 1
else:
    local_id = 0

### execute query
print "Inserting %s-%s into db" % (city, name)
query = "INSERT INTO %s VALUES(0,'%d','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s', now(), %d, '%d', '%d')" % (DB_TABLE, local_id, name, link_src, link_web, link_stat, link_xpaths, country, city, gps, type, substances, 0, 0, 1)
cur.execute(query)
id = int(cur.lastrowid)
print "Inserting %s-%s into the temp table" % (city, name)
query = "INSERT INTO %s_temp VALUES('%d',now(),0,0,0,0,0,0)" % (DATA_TABLE, id)
cur.execute(query)
db.commit()
db.close()

city_dir = city.replace(" ", "_")
### check if the directories are created
if (not os.path.isdir("%s/%s" % (SPIDER_DIR, country))):
    os.makedirs("%s/%s" % (SPIDER_DIR, country))
if (not os.path.isdir("%s/%s/%s" % (SPIDER_DIR, country, city_dir))):
    os.makedirs("%s/%s/%s" % (SPIDER_DIR, country, city_dir))
if (not os.path.isdir("%s/%s" % (STATS_DIR, country))):
    os.makedirs("%s/%s" % (STATS_DIR, country))
if (not os.path.isdir("%s/%s/%s" % (STATS_DIR, country, city_dir))):
    os.makedirs("%s/%s/%s" % (STATS_DIR, country, city_dir))

### create new sensor spider on disk
spider_name = local_id
spider_file = "%s/%s/%s/%s.py" % (SPIDER_DIR, country, city_dir, spider_name)
template = fill_spider_template(SPIDER_TEMPLATE, name, link_src, link_xpaths)
write_template(spider_file, template)

### update mrtg for the city and substance
for substance in substances.split():
    mrtg_name = "%s.cfg" % (substance)
    mrtg_workdir = "%s/%s/%s/" %(STATS_DIR, country, city_dir)
    mrtg_file = "%s/%s/%s/%s" % (SPIDER_DIR, country, city_dir, mrtg_name)
    template = fill_mrtg_template(DATA_DIR, SPIDER_COMMAND, MRTG_TEMPLATE, id, local_id, name, city, country, substance)
    write_mrtg_template(mrtg_file, mrtg_workdir, template)

### add mrtg configs to the runlist
if (not os.path.isfile("%s/%s" % (DATA_DIR, 'mrtg.runlist'))):
    lines = []
else:
    f = file("%s/%s" % (DATA_DIR, 'mrtg.runlist'), 'r')
    lines = f.readlines()
    f.close()
if (not "%s/%s\n" % (country, city_dir) in lines):
    f = file("%s/%s" % (DATA_DIR, 'mrtg.runlist'), 'a')
    f.write("%s/%s\n" % (country, city_dir))
    f.close()

### check what substances we are already having for the city (if any)
sensor_substances = substances.split()
mrtg_workdir = "%s/%s/%s/" %(SPIDER_DIR, country, city_dir)
for file in os.listdir(mrtg_workdir):
    if file.endswith(".cfg"):
        if (file.replace(".cfg","") not in sensor_substances):
            sensor_substances.append(file.replace(".cfg",""))

### create index with indexmaker
# indexmaker --title="Brno PM10 Levels (<a href=no2.html>NO2</a>  <a href=o3.html>O3</a> <a href=pm25.html>PM25</a>)" --nolegend cz/brno/pm10.cfg
for substance in substances.split():
    links = ""
    for sub in sensor_substances:
        if (sub != substance):
            if (sub == 'pm10'):
                links += "<a href=index.html>%s</a> " % (sub.upper())
            else:
                links += "<a href=%s.html>%s</a> " % (sub, sub.upper())

    if (substance == 'pm10'):
        command = "indexmaker --output=%s/%s/%s/%s.html --title=\"%s %s Levels (%s)\" --nolegend %s/%s/%s/%s.cfg" % (STATS_DIR, country, city_dir, "index", city.capitalize(), substance.upper(), links, SPIDER_DIR, country, city_dir, substance)
    else:
        command = "indexmaker --output=%s/%s/%s/%s.html --title=\"%s %s Levels (%s)\" --nolegend %s/%s/%s/%s.cfg" % (STATS_DIR, country, city_dir, substance, city.capitalize(), substance.upper(), links, SPIDER_DIR, country, city_dir, substance)

    command_args = shlex.split(command)
    ### run indexmaker
    try:
        process = subprocess.Popen(command_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = process.communicate()
    except subprocess.CalledProcessError as e:
        print e
        out = "UGH"
        pass

    ### if non-zero return, we have a problem
    if (out[1] != ""):
        print "Something went wrong: %s" % (out[1])
    else:
        print "mrtg index for %s created" % (substance)

### If we reached end
sys.exit()
