#!/usr/bin/env python
# # -*- coding: utf-8 -*-

""" Smogdance

    An open-source collection of scripts to collect, store and graph air quality data
    from publicly available sources.

    This removes substance(s) from a existing sensor.
    Step-by-step it:
        - remove substance(s) from the sensor description in the db
        - for each removed substance, lines with city-local_id_substance are removed from substance.cfg (MRTG)
        - move city-local_id-substance* files from stats into stats_deleted folder
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
DEL_STATS_DIR = config.get('globals', 'DEL_STATS_DIR')
SPIDER_DIR = config.get('globals', 'SPIDER_DIR')
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
    sys.exit("Usage: ./remove-substance-from-sensor.py <sensor_id> <substance | substance1,substance2,substance3,..,substanceN>")

### Process arguments
delete_substances = []
if ("," in input_substances):
    temp = input_substances.split(",")
    for sub in temp:
        if sub in all_substances:
            delete_substances.append(sub)
        else:
            sys.exit("Please provide a valid substance name")
else:
    if (input_substances in all_substances):
        delete_substances.append(input_substances)
    else:
        sys.exit("Please provide a valid substance name")

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

### Remove substance(s) from the sensor description in the db
print "Removing %s from sensor %d" % (delete_substances, sensor_id)
query = "SELECT substances FROM %s WHERE id = '%d'" % (DB_TABLE, sensor_id)
cur.execute(query)
substances = cur.fetchone()[0].split()
for sub in delete_substances:
    if sub in substances:
        substances.remove(sub)
new_substances = ' '.join(substances)
query = "UPDATE %s SET substances = '%s' WHERE id = '%d'" % (DB_TABLE, new_substances, sensor_id)
cur.execute(query)
old_xpaths = xpaths.split(";")
for sub in delete_substances:
    for xpath in old_xpaths:
        if (sub in xpath):
            old_xpaths.remove(xpath)
new_xpaths = ';'.join(old_xpaths)
query = "UPDATE %s SET link_xpaths = '%s' WHERE id = '%d'" % (DB_TABLE, new_xpaths, sensor_id)
cur.execute(query)
db.commit()

### For each removed substance, lines with city-local_id_substance are removed from substance.cfg (MRTG)
for sub in delete_substances:
    print "Removing MRTG definitions for %s" % (sub)
    pattern = "%s-%s_%s" % (city, local_id, sub)
    pattern_name = "%s-%s" % (city.upper(), local_id)
    mrtg_name = "%s.cfg" % (sub)
    mrtg_workdir = "%s/%s/%s/" %(STATS_DIR, country, city_dir)
    mrtg_file = "%s/%s/%s/%s" % (SPIDER_DIR, country, city_dir, mrtg_name)
    if (os.path.isfile(mrtg_file)):
        f = file(mrtg_file, 'r')
        lines = f.readlines()
        f.close()

        new_lines = []
        for line in lines:
            if ((not pattern in line) and (not pattern_name in line)):
                new_lines.append(line)
        lines_left = sum(1 for line in new_lines if line.rstrip())

        # Now replace or delete the file
        if (lines_left < 10):
            print "Removing %s" % (mrtg_file)
            os.remove(mrtg_file)
        else:
            print "Modifying %s" % (mrtg_file)
            f = file(mrtg_file, 'w')
            for line in new_lines:
                f.write(line)
            f.close()

### Move city-local_id-substance* files from stats into stats_deleted folder
if (not os.path.isdir("%s" % (DEL_STATS_DIR))):
    os.makedirs("%s" % (DEL_STATS_DIR))
if (not os.path.isdir("%s/%s" % (DEL_STATS_DIR, country))):
    os.makedirs("%s/%s" % (DEL_STATS_DIR, country))
if (not os.path.isdir("%s/%s/%s" % (DEL_STATS_DIR, country, city_dir))):
    os.makedirs("%s/%s/%s" % (DEL_STATS_DIR, country, city_dir))

# Now move all files called like city-local_id-substance*
for sub in delete_substances:
    old_dir = "%s/%s/%s" % (STATS_DIR, country, city_dir)
    new_dir = "%s/%s/%s" % (DEL_STATS_DIR, country, city_dir)
    pattern = "%s-%s_%s" % (city, local_id, sub)
    files = [f for f in os.listdir(old_dir) if os.path.isfile(os.path.join(old_dir, f))]
    for file in files:
        if (pattern in file):
            print "Moving %s" % (file)
            os.rename("%s/%s" % (old_dir, file), "%s/%s" % (new_dir, file))

### Regenerate spider file on disk from db
spider_name = local_id
spider_file = "%s/%s/%s/%s.py" % (SPIDER_DIR, country, city_dir, spider_name)
template = fill_spider_template(TEMP_DIR, SPIDER_TEMPLATE, name, link_src, new_xpaths)
write_template(spider_file, template)

### Create a new mrtg index for the city
# Check what substances we are already having for the city (if any)
sensor_substances = new_substances.split()
mrtg_workdir = "%s/%s/%s/" %(SPIDER_DIR, country, city_dir)
for file in os.listdir(mrtg_workdir):
    if file.endswith(".cfg"):
        if (file.replace(".cfg","") not in sensor_substances):
            sensor_substances.append(file.replace(".cfg",""))


### create index with indexmaker
# TODO - this needs actually to move old files to a deleted directory
# Remove old html files
mrtg_statdir = "%s/%s/%s/" %(STATS_DIR, country, city_dir)
for file in os.listdir(mrtg_statdir):
    if file.endswith(".html"):
        os.remove("%s/%s" % (mrtg_statdir, file))

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

### All OK !
print "All OK !"

### Print out a new definition file
print "New sensor definition:"
query = "SELECT name, link_src, link_web, link_stat, link_xpaths, country, city, gps, type, substances FROM %s WHERE id = '%s'" % (DB_TABLE, sensor_id)
cur.execute(query)
l = cur.fetchone()
print "'%s' '%s' '%s' '%s' '%s' '%s' '%s' '%s' '%s' '%s'" % (l[0],l[1].replace('/data/www/smog.dance/smogdance/temp','TEMP_DIR'),l[2],l[3].replace('stats.smog.dance','STATS_URL'),l[4],l[5],l[6],l[7],l[8],l[9])
