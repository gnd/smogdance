#!/usr/bin/env python
# # -*- coding: utf-8 -*-

""" Smogdance

    An open-source collection of scripts to collect, store and graph air quality data
    from publicly available sources.

    This adds substance(s) from a existing sensor.
    Step-by-step it:
        - add substance(s) from the sensor description in the db (substances and xpaths)
        - for each added substance, mrtg substance.cfg is modified or created (city-local_id_substance)
        - regenerate spider file on disk from db
        - create a new mrtg index for the city
        - print out a new definition file

    gnd, 2018
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
SCRAPY_BIN = config.get('globals', 'SCRAPY_BIN')
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
DATA_TABLE = config.get('database', 'DATA_TABLE')
db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
cur = db.cursor()

all_substances = ["co","no2","o3","pm10","pm25","so2"]

### Import Smog functions
from smog_functions import *

### process input
if (len(sys.argv) > 2):
    try:
        sensor_id = int(sys.argv[1])
    except:
        sys.exit("Please provide a valid sensor_id")
    input_substances = sys.argv[2]
else:
    sys.exit("Usage: ./add-substance-to-sensor.py <sensor_id> <substance:col | substance1:col1,substance2:col2,substance3:col3,..,substanceN:colN>")

### Process arguments
add_substances = []
if ("," in input_substances):
    temp = input_substances.split(",")
    for subcol in temp:
        subcol_arr = subcol.split(":")
        if (len(subcol_arr) > 1):
            sub = subcol_arr[0]
            if sub in all_substances:
                add_substances.append(subcol)
            else:
                sys.exit("Please provide a valid substance name")
        else:
            sys.exit("Please provide a substance:rowid pair")
else:
    subcol_arr = input_substances.split(":")
    if (len(subcol_arr) > 1):
        sub = subcol_arr[0]
        if (sub in all_substances):
            add_substances.append(input_substances)
        else:
            sys.exit("Please provide a valid substance name")
    else:
        sys.exit("Please provide a substance:rowid pair")

### Verify sensor_id exists
query = "SELECT count(*) as count FROM %s WHERE id = '%d'" % (DB_TABLE, sensor_id)
cur.execute(query)
if (int(cur.fetchone()[0]) != 1):
    sys.exit("Sensor_id %d doesnt exist.")

### Retrieve sensor data
query = "SELECT local_id, name, country, city, link_xpaths, link_src FROM %s WHERE id = '%d'" % (DB_TABLE, sensor_id)
cur.execute(query)
res = cur.fetchone()
local_id = res[0]
name = res[1]
country = res[2]
city = res[3]
xpaths = res[4]
link_src = res[5]
city_dir = city.replace(" ", "_")

### Add substance(s) from the sensor description in the db (substances and xpaths)
print "Adding %s to sensor %d" % (add_substances, sensor_id)
query = "SELECT substances FROM %s WHERE id = '%d'" % (DB_TABLE, sensor_id)
cur.execute(query)
old_substances = cur.fetchone()[0].split()
new_substances = []
for sub in old_substances:
    new_substances.append(sub)
for subcol in add_substances:
    sub = subcol.split(":")[0]
    if sub not in old_substances:
        new_substances.append(sub)
new_substances = ' '.join(new_substances) # this is so bad lol
query = "UPDATE %s SET substances = '%s' WHERE id = '%d'" % (DB_TABLE, new_substances, sensor_id)
cur.execute(query)
old_xpaths = xpaths.split(";")
xpath_modifier = old_xpaths[0].split("--")[2]
new_xpaths = []
for xpath in old_xpaths:
    new_xpaths.append(xpath)
for subcol in add_substances:
    sub = subcol.split(":")[0]
    if sub not in old_substances:
        # Slovak sensors
        if (xpath_modifier == 'n'):
            col = int(subcol.split(":")[1])
            rownum = int(old_xpaths[0].split("--")[1].split('tr[')[1].split("]")[0])
            xpath = '//table[@class="black w600 center"][1]/tr[%d]/td[%d]//text()' % (rownum, col)
            new_xpaths.append("%s--%s--%s" % (sub, xpath, xpath_modifier))
        if (xpath_modifier == 'cz_chmi'):
            col = int(subcol.split(":")[1])
            rowid = old_xpaths[0].split("--")[1].split(":")[0]
            new_xpaths.append("%s--%s:%s--%s" % (sub, rowid, col, xpath_modifier))
        if (xpath_modifier == 'hu_json'):
            col = subcol.split(":")[1]
            new_xpaths.append("%s--%s--%s" % (sub, col, xpath_modifier))
new_xpaths = ';'.join(new_xpaths)
query = "UPDATE %s SET link_xpaths = '%s' WHERE id = '%d'" % (DB_TABLE, new_xpaths, sensor_id)
cur.execute(query)
db.commit()

### For each added substance, mrtg substance.cfg is modified or created (city-local_id_substance)
for subcol in add_substances:
    substance = subcol.split(":")[0]
    if sub not in old_substances:
        print "Adding MRTG definitions for %s" % (sub)
        city_dir = city.replace(" ", "_")
        mrtg_name = "%s.cfg" % (substance)
        mrtg_workdir = "%s/%s/%s/" %(STATS_DIR, country, city_dir)
        mrtg_file = "%s/%s/%s/%s" % (SPIDER_DIR, country, city_dir, mrtg_name)
        template = fill_mrtg_template(DATA_DIR, SPIDER_COMMAND, MRTG_TEMPLATE, sensor_id, local_id, name, city, country, substance)
        write_mrtg_template(mrtg_file, mrtg_workdir, template)

### Regenerate spider file on disk from db
spider_name = local_id
spider_file = "%s/%s/%s/%s.py" % (SPIDER_DIR, country, city_dir, spider_name)
template = fill_spider_template(TEMP_DIR, SPIDER_TEMPLATE, name, link_src, new_xpaths)
write_template(spider_file, template)

### Create a new mrtg index for the city
# Check what substances we are already having for the city (if any)
sensor_substances = []
for sub in new_substances.split():
    sensor_substances.append(sub)
mrtg_workdir = "%s/%s/%s/" %(SPIDER_DIR, country, city_dir)
for file in os.listdir(mrtg_workdir):
    if file.endswith(".cfg"):
        if (file.replace(".cfg","") not in sensor_substances):
            sensor_substances.append(file.replace(".cfg",""))

### create index with indexmaker
# indexmaker --title="Brno PM10 Levels (<a href=no2.html>NO2</a>  <a href=o3.html>O3</a> <a href=pm25.html>PM25</a>)" --nolegend cz/brno/pm10.cfg
for substance in sensor_substances:
    links = ""
    index_sub = 'pm10'
    if 'pm10' in sensor_substances:
        index_sub = 'pm10'
    elif 'pm25' in sensor_substances:
        index_sub = 'pm25'
    elif 'co' in sensor_substances:
        index_sub = 'co'
    elif 'o3' in sensor_substances:
        index_sub = 'o3'
    for sub in sensor_substances:
        if (sub != substance):
            if (sub == index_sub):
                links += "<a href=index.html>%s</a> " % (sub.upper())
            else:
                links += "<a href=%s.html>%s</a> " % (sub, sub.upper())

    if (substance == index_sub):
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

### All OK !
print "All OK !"

### Print out a new definition file
print "New sensor definition:"
query = "SELECT name, link_src, link_web, link_stat, link_xpaths, country, city, gps, type, substances FROM %s WHERE id = '%s'" % (DB_TABLE, sensor_id)
cur.execute(query)
l = cur.fetchone()
print "'%s' '%s' '%s' '%s' '%s' '%s' '%s' '%s' '%s' '%s'" % (l[0],l[1].replace('/data/www/smog.dance/smogdance/temp','TEMP_DIR'),l[2],l[3].replace('stats.smog.dance','STATS_URL'),l[4],l[5],l[6],l[7],l[8],l[9])
