#!/usr/bin/env python
# # -*- coding: utf-8 -*-

""" Smogdance

    An open-source collection of scripts to collect, store and graph air quality data
    from publicly available sources.

    This removes a sensor from disk and database:
        - moves the sensor record from sensors to sensors_deleted in the db
        - moves all historical data associated with the sensor from sensors_data to sensors_data_deleted
        - deletes sensor spiderfile from the disk
        - recreates the city's sensor local id's (or deletes the city spider dir if only sensor)
        - recreates the city's mrtg directory (or deletes it if only sensor)

    gnd, 2017 - 2020
"""

import re
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
db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
cur = db.cursor()

### Import Smog functions
from smog_functions import *

def usage():
    print "Usage: delete-sensor.py <sensor_id>"

### check input
sensor_id = ""
if (len(sys.argv) > 1):
    if (sys.argv[1].isdigit()):
        sensor_id = int(sys.argv[1])
    else:
        sys.exit("Sensor id must be an integer")
        usage()
        sys.exit()
else:
    print("Not enough parameters")
    usage()
    sys.exit()


#####
##### Get sensor params
#####
query = "SELECT local_id, name, city, country, substances FROM %s where id = '%d'" % (DB_TABLE, sensor_id)
cur.execute(query)
for line in cur.fetchall():
    local_id = line[0]
    name = line[1]
    city = line[2]
    country = line[3]
    substances = line[4]
    city_dir = city.replace(" ", "_")


#####
##### Move sensor definition into sensors_deleted
#####
query = "INSERT INTO %s SELECT * FROM %s WHERE id = '%d'" % (DB_TABLE_DEL, DB_TABLE, sensor_id)
try:
    print "Moving db sensor definitions"
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)
db.commit()


#####
##### Delete sensor definition from sensors
#####
query = "DELETE FROM %s WHERE id = '%d'" % (DB_TABLE, sensor_id)
try:
    print "Deleting db sensor definitions"
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)
db.commit()


#####
##### Move the sensor data into sensor_data_deleted
#####
query = "INSERT INTO %s SELECT * FROM %s WHERE sensor_id = '%d'" % (DATA_TABLE_DEL, DATA_TABLE, sensor_id)
try:
    print "Moving db sensor data"
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)
db.commit()


#####
##### Delete the sensor data
#####
query = "DELETE FROM %s WHERE sensor_id = '%d'" % (DATA_TABLE, sensor_id)
try:
    print "Deleting db sensor data"
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)
db.commit()


#####
##### Delete spider file from disk
#####
spider_file = "%s/%s/%s/%s.py" % (SPIDER_DIR, country, city_dir, local_id)
try:
    print "Removing spider file %s" % (spider_file)
    os.remove(spider_file)
except:
    sys.exit("Something went wrong when removing: " + spider_file)


#####
##### Deterine city_substances
#####
city_substances = []
query = "SELECT substances FROM %s WHERE city = '%s' ORDER BY local_id" % (DB_TABLE, city)
try:
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)
line = cur.fetchone():
temp_substances_arr = line.split()
for temp_substance in temp_substances:
    if temp_substance not in city_substances:
        city_substances.append(temp_substance)


#####
##### Recreate or delete local ids, spider files
#####
# Determine how many sensors from the city are left
query = "SELECT count(id) FROM %s WHERE city = '%s'" % (DB_TABLE, city)
try:
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)
res = cur.fetchone()
sensor_count = res[0]
print "%d sensors remaining for %s" % (sensor_count, city)

# If this wasnt the last sensor in the city, renumber the leftover sensors
if ((sensor_count > 0) and (local_id < sensor_count)):
    id_mapping = {}
    new_local_id = 0
    query = "SELECT id, local_id FROM %s WHERE city = '%s' ORDER BY local_id" % (DB_TABLE, city)
    try:
        cur.execute(query)
    except:
        sys.exit("Something went wrong: " + query)
    for line in cur.fetchall():
        temp_sensor_id = line[0]
        old_local_id = line[1]
        query = "UPDATE %s SET local_id = %d WHERE id = '%d'" % (DB_TABLE, new_local_id, temp_sensor_id)
        try:
            cur.execute(query)
        except:
            sys.exit("Something went wrong: " + query)
        db.commit()

        # Delete old spiderfiles
        sensor_city_dir = "%s/%s/%s" % (SPIDER_DIR, country, city_dir)
        files = [f for f in os.listdir(sensor_city_dir) if os.path.isfile(os.path.join(sensor_city_dir, f))]
        for file in files:
            if ((".py" in file) or (".pyc" in file)):
                os.remove("%s/%s" % (sensor_city_dir, file))

        # store mapping
        id_mapping[old_local_id] = new_local_id
        new_local_id += 1

# If this was the last sensor, delete the directory and all its contents
if (sensor_count == 0):
    sensor_city_dir = "%s/%s/%s" % (SPIDER_DIR, country, city_dir)
    files = [f for f in os.listdir(sensor_city_dir) if os.path.isfile(os.path.join(sensor_city_dir, f))]
    for file in files:
        os.remove("%s/%s" % (sensor_city_dir, file))
    os.rmdir(sensor_city_dir)


#####
##### Regenerate spiderfiles
#####
if ((sensor_count > 0) and (local_id < sensor_count)):
    query = "SELECT local_id, name, link_src, link_xpaths FROM %s WHERE city = '%s' ORDER BY id" % (DB_TABLE, city)
    try:
        cur.execute(query)
    except:
        sys.exit("Something went wrong: " + query)
    ### create new sensor spider on disk
    for line in cur.fetchall():
        temp_local_id = line[0]
        temp_name = line[1]
        temp_link_src = line[2]
        temp_link_xpaths = line[3]
        temp_spider_file = "%s/%s/%s/%s.py" % (SPIDER_DIR, country, city_dir, temp_local_id)
        template = fill_spider_template(TEMP_DIR, SPIDER_TEMPLATE, temp_name, temp_link_src, temp_link_xpaths)
        write_template(temp_spider_file, template)


#####
##### Regenerate mrtg config files with new local ids
#####
if ((sensor_count > 0) and (local_id < sensor_count)):
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
##### Remove city from mrtg runlist if last sensor
#####
if (sensor_count == 0):
    runlist = "%s/%s" % (DATA_DIR, 'mrtg.runlist')
    if (os.path.isfile(runlist)):
        # Read runlist
        f = open(runlist, 'r')
        lines = f.readlines()
        f.close()

        # Write new runlist
        f = open(runlist, 'w')
        for line in lines:
            runlist_name = "%s/%s\n" % (country, city_dir)
            if (runlist_name not in line):
                f.write()
        f.close()


#####
##### Move mrtg data for deleted sensor
#####
# prepare directories
if (not os.path.isdir("%s" % (STATS_DIR_DEL))):
    os.makedirs("%s" % (STATS_DIR_DEL))
if (not os.path.isdir("%s/%s" % (STATS_DIR_DEL, country))):
    os.makedirs("%s/%s" % (STATS_DIR_DEL, country))
if (not os.path.isdir("%s/%s/%s" % (STATS_DIR_DEL, country, city_dir))):
    os.makedirs("%s/%s/%s" % (STATS_DIR_DEL, country, city_dir))
# Now move all files called like city-local_id*
for sub in substances:
    old_dir = "%s/%s/%s" % (STATS_DIR, country, city_dir)
    new_dir = "%s/%s/%s" % (STATS_DIR_DEL, country, city_dir)
    pattern = "%s-%s_%s" % (city, local_id, sub)
    files = [f for f in os.listdir(old_dir) if os.path.isfile(os.path.join(old_dir, f))]
    for file in files:
        if (pattern in file):
            print "Moving %s" % (file)
            os.rename("%s/%s" % (old_dir, file), "%s/%s" % (new_dir, file))


#####
##### Rename mrtg data for leftover sensors
#####
if ((sensor_count > 0) and (local_id < sensor_count)):
    old_dir = "%s/%s/%s" % (STATS_DIR, country, city_dir)
    for old_id, new_id in id_mapping.iteritems():
        pattern = "%s-%s.*\.(png|log|old)" % (city, old_id)
        files = [f for f in os.listdir(old_dir) if os.path.isfile(os.path.join(old_dir, f))]
        for file in files:
            if re.match(pattern, file):
                name_root = "%s-%s" % (city, new_id)
                name_tail = file.split('_')[1]
                new_name = "%s_%s" % (name_root, name_tail)
                print "Renaming %s to %s" % (file, new_name)
                os.rename("%s/%s" % (old_dir, file), "%s/%s" % (old_dir, new_name))


#####
##### Recreate mrtg stats for city
#####
### create index with indexmaker
if (sensor_count > 0):
    mrtg_statdir = "%s/%s/%s/" %(STATS_DIR, country, city_dir)
    # remove old index files
    for file in os.listdir(mrtg_statdir):
        if file.endswith(".html"):
            os.remove("%s/%s" % (mrtg_statdir, file))

    # Create new index files
    for substance in city_substances:
        links = ""
        index_sub = 'pm10'
        if 'pm10' in city_substances:
            index_sub = 'pm10'
        elif 'pm25' in city_substances:
            index_sub = 'pm25'
        elif 'co' in city_substances:
            index_sub = 'co'
        elif 'o3' in city_substances:
            index_sub = 'o3'
        for sub in city_substances:
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


#####
##### Done
#####
print "Sensor %s from %s with local_id %d and id %d deleted." % (name, city, local_id, sensor_id)
