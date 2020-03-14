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

# # 0. '//table[@class="black w600 center"]' => '//table[@class="black w600 center"][1]''
query = "SELECT id, link_xpaths from %s WHERE country = 'sk' and type = 'hourly'" % (DB_TABLE)
try:
 cur.execute(query)
except:
 sys.exit("Something went wrong: " + query)

for line in cur.fetchall():
    id = line[0]
    xpaths = line[1]
    xpaths = xpaths.replace('//table[@class="black w600 center"]','//table[@class="black w600 center"][1]')
    query = "UPDATE %s set link_xpaths = '%s' WHERE id = %d" % (DB_TABLE, xpaths, id)
    try:
        cur.execute(query)
    except:
        sys.exit("Something went wrong: " + query)
    db.commit()

# 1. replace - td[6] >> tdnew[2], td[7] >> tdnew[3], td[2] >> tdnew[4], td[3] >> tdnew[5], td[8] >> tdnew[6], td[4] >> tdnew[7], tdnew[ >> td[
query = "SELECT id, link_xpaths from %s WHERE country = 'sk' and type = 'hourly'" % (DB_TABLE)
try:
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)

for line in cur.fetchall():
    id = line[0]
    xpaths = line[1]
    xpaths = xpaths.replace('td[6]','tdnew[2]')
    xpaths = xpaths.replace('td[7]','tdnew[3]')
    xpaths = xpaths.replace('td[2]','tdnew[4]')
    xpaths = xpaths.replace('td[3]','tdnew[5]')
    xpaths = xpaths.replace('td[8]','tdnew[6]')
    xpaths = xpaths.replace('td[4]','tdnew[7]')
    xpaths = xpaths.replace('tdnew[','td[')
    xpaths = xpaths.replace('text())','text()')
    query = "UPDATE %s set link_xpaths = '%s' WHERE id = %d" % (DB_TABLE, xpaths, id)
    try:
        cur.execute(query)
    except:
        sys.exit("Something went wrong: " + query)
    db.commit()

# 2. tr[x] -> tr[x+1], for x=>6
query = "SELECT id, link_xpaths from %s WHERE country = 'sk' and type = 'hourly'" % (DB_TABLE)
try:
     cur.execute(query)
except:
     sys.exit("Something went wrong: " + query)

for line in cur.fetchall():
    id = line[0]
    xpaths = line[1]
    row_number = xpaths.split('tr[')[1].split(']')[0]
    if (int(row_number) >= 6):
         xpaths = xpaths.replace('tr['+row_number+']','tr['+str(int(row_number)+1)+']')
         query = "UPDATE %s set link_xpaths = '%s' WHERE id = %d" % (DB_TABLE, xpaths, id)
    try:
        cur.execute(query)
    except:
        sys.exit("Something went wrong: " + query)
    db.commit()

# 3. replace - tr[8]->trnew[9], - tr[9]->trnew[8], - trnew[ -> tr[ (sensor swap)
query = "SELECT id, link_xpaths from %s WHERE country = 'sk' and type = 'hourly'" % (DB_TABLE)
try:
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)

for line in cur.fetchall():
    id = line[0]
    xpaths = line[1]
    xpaths = xpaths.replace('tr[8]','trnew[9]')
    xpaths = xpaths.replace('tr[9]','trnew[8]')
    xpaths = xpaths.replace('trnew[','tr[')
    query = "UPDATE %s set link_xpaths = '%s' WHERE id = %d" % (DB_TABLE, xpaths, id)
    try:
        cur.execute(query)
    except:
        sys.exit("Something went wrong: " + query)
    db.commit()

# 4. tr[x] -> tr[x+1], for x=>26
query = "SELECT id, link_xpaths from %s WHERE country = 'sk' and type = 'hourly'" % (DB_TABLE)
try:
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)

for line in cur.fetchall():
    id = line[0]
    xpaths = line[1]
    row_number = xpaths.split('tr[')[1].split(']')[0]
    if (int(row_number) >= 26):
        xpaths = xpaths.replace('tr['+row_number+']','tr['+str(int(row_number)+1)+']')
        query = "UPDATE %s set link_xpaths = '%s' WHERE id = %d" % (DB_TABLE, xpaths, id)
    try:
        cur.execute(query)
    except:
        sys.exit("Something went wrong: " + query)
    db.commit()

# 5. Recreate spider files on disk
query = "SELECT local_id, name, country, city, link_src, link_xpaths FROM %s WHERE country = 'sk' and type = 'hourly' ORDER BY id" % (DB_TABLE)
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

# 6. update 'Trnavske Myto' sensor
# add pm25
# params <sensor_id> <substance_name:substance_column>
params = "261 pm25:3"
run_cmd = "%s/add-substance-to-sensor.py %s" % (DATA_DIR, params)
run_args = shlex.split(run_cmd)

### run the change
try:
    print "Trying to run %s/add-substance-to-sensor.py %s" % (DATA_DIR, params)
    process = subprocess.Popen(run_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/add-substance-to-sensor.py %s" % (DATA_DIR, params)

# 7. update 'Jeseniova' sensor
# add so2
# params <sensor_id> <substance_name:substance_column>
params = "262 so2:5"
run_cmd = "%s/add-substance-to-sensor.py %s" % (DATA_DIR, params)
run_args = shlex.split(run_cmd)

### run the change
try:
    print "Trying to run %s/add-substance-to-sensor.py %s" % (DATA_DIR, params)
    process = subprocess.Popen(run_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/add-substance-to-sensor.py %s" % (DATA_DIR, params)

# 8. Insert new sensor
line = "'Rovinka' 'file://127.0.0.1TEMP_DIR/shmu.html' 'http://www.shmu.sk/sk/?page=1&id=oko_imis' 'https://STATS_URL/sk/bratislava' 'co--//table[@class=\"black w600 center\"][1]/tr[6]/td[6]//text()--n;so2--//table[@class=\"black w600 center\"][1]/tr[6]/td[5]//text()--n;no2--//table[@class=\"black w600 center\"][1]/tr[6]/td[7]//text()--n;pm10--//table[@class=\"black w600 center\"][1]/tr[6]/td[2]//text()--n' 'sk' 'bratislava' '' 'hourly' 'pm10 so2 co no2'"
import_cmd = "%s/add-sensor.py %s" % (DATA_DIR, line)
import_args = shlex.split(import_cmd)

### run the import
try:
    print "Trying to run %s/add-sensor.py %s" % (DATA_DIR, line)
    process = subprocess.Popen(import_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/add-sensor.py %s" % (DATA_DIR, line)

# 9. Insert new sensor
line = "'Mobilna AMS' 'file://127.0.0.1TEMP_DIR/shmu.html' 'http://www.shmu.sk/sk/?page=1&<id=oko_imis' 'https://STATS_URL/sk/ruzomberok' 'so2--//table[@class=\"black w600 center\"][1]/tr[26]/td[5]//text()--n;no2--//table[@class=\"black w600 center\"][1]/tr[26]/td[7]//text()--n;co--//table[@class=\"black w600 center\"][1]/tr[26]/td[6]//text()--n;pm10--//table[@class=\"black w600 center\"][1]/tr[26]/td[2]//text()--n' 'sk' 'ruzomberok' '' 'hourly' 'so2 no2 co pm10'"
import_cmd = "%s/add-sensor.py %s" % (DATA_DIR, line)
import_args = shlex.split(import_cmd)

### run the import
try:
    print "Trying to run %s/add-sensor.py %s" % (DATA_DIR, line)
    process = subprocess.Popen(import_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/add-sensor.py %s" % (DATA_DIR, line)
