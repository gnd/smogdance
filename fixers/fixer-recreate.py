#!/usr/bin/env python
# # -*- coding: utf-8 -*-

""" Smogdance

    An open-source collection of scripts to collect, store and graph air quality data
    from publicly available sources.

    Helper script to recreate spider directories and mrtg data for cities with deleted sensors

    gnd, 2017 - 2018
"""

import os
import sys
import time
import shlex
import fnmatch
import MySQLdb
import datetime
import subprocess
import ConfigParser

#####
##### Check input TODO (sanitize like in poll-city)
#####
city = ""
if (len(sys.argv) > 1):
    city = sys.argv[1]
else:
    sys.exit("Not enough parameters")


#####
##### Load config
#####
settings_file = os.path.join(sys.path[0], 'settings_python')
config = ConfigParser.ConfigParser()
config.readfp(open(settings_file))
DATA_DIR = config.get('globals', 'DATA_DIR')
STATS_DIR = config.get('globals', 'STATS_DIR')
SPIDER_DIR = config.get('globals', 'SPIDER_DIR')
MRTG_TEMPLATE = config.get('globals', 'MRTG_TEMPLATE')
SPIDER_COMMAND = config.get('globals', 'SPIDER_COMMAND')
SPIDER_TEMPLATE = config.get('globals', 'SPIDER_TEMPLATE')
rebuild = False

#####
##### Define functions (TODO: create a file with commonly used functions to be included)
#####
def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
       if unicodedata.category(c) != 'Mn')

def fill_spider_template(template, name, link_src, link_xpaths):
    f = file(template, 'r')
    tmp = f.read()
    f.close()
    res = tmp.replace("SPIDER_NAME", name)
    res = res.replace("LINK_SRC", link_src)

    ### build some outputs
    outputs = ""
    substances = []
    for line in link_xpaths.split(";"):
        tmp = ""
        substance = line.split("--")[0]
        substances.append(substance)
        xpath = line.split("--")[1]
        modifier = line.split("--")[2]
        if (modifier == 'hu_json'):
            tmp = "        xpath = \"%s\"\n" % (xpath)
            tmp += "        %s = j[\"data\"][xpath][\"value\"] if ((j[\"data\"] != {}) and (\"value\" in j[\"data\"][xpath])) else 'None'\n" % (substance)
            outputs += tmp
        else:
            tmp = "        %s = ' '.join(response.xpath('%s').extract()).strip().replace(' ','')\n" % (substance, xpath)
            tmp += "        %s = 'None' if %s == '' else %s\n" % (substance, substance, substance)
            ### modifiers are currently not really used, but might be handy
            if modifier == "int":
                tmp += "        %s = int(float(%s))\n" % (substance)
            outputs += tmp
    if (modifier == 'hu_json'):
        head = "        j = json.loads(json.loads(response.text))\n"
        outputs = head + outputs
    tmp = ""
    for substance in substances:
        tmp += '%s '
    outputs += '        print "' + tmp.strip() + '" % ' + "(%s)" % (','.join(substances))

    res = res.replace("OUTPUTS", outputs)
    return res

def fill_mrtg_template(template, id, local_id, name, city, country, substance):
    f = file(template, 'r')
    tmp = f.read()
    f.close()

    name = "%s - %s" % (city.capitalize(), name)
    run_command = "%s/%s"  % (DATA_DIR, SPIDER_COMMAND)
    sensor_desc = "%s-%s" % (city, local_id)
    mrtg_id = "%s_%s" % (sensor_desc.replace(" ","_"), substance)

    res = tmp.replace("SENSOR_NAME", name)
    res = res.replace("RUN_COMMAND", run_command)
    res = res.replace("SENSOR_DESC", sensor_desc.upper())
    res = res.replace("SUBSTANCE_NAME", substance)
    res = res.replace("SUBSTANCE_DESC", substance.upper())
    res = res.replace("MRTG_ID", mrtg_id)
    res = res.replace("SPIDER_ID", str(id))
    maxbytes = 200
    absmax = 300
    if (substance == "pm10"):
        maxbytes = 160
        absmax = 500
    if (substance == "co"):
        maxbytes = 3000
        absmax = 5000
    res = res.replace("MAXBYTES", str(maxbytes))
    res = res.replace("ABSMAX", str(absmax))
    return res

def write_template(filename, template):
    f = file(filename, 'w')
    f.write(template)
    f.close()

def write_mrtg_template(filename, workdir, template):
    if os.path.isfile(filename):
        f = file(filename, 'a')
    else:
        f = file(filename, 'w')
        f.write("WorkDir: %s\n\n" % (workdir))
    f.write(template)
    f.close()

#####
##### Connect to the db
#####
DB_HOST = config.get('database', 'DB_HOST')
DB_USER = config.get('database', 'DB_USER')
DB_PASS = config.get('database', 'DB_PASS')
DB_NAME = config.get('database', 'DB_NAME')
DB_TABLE = config.get('database', 'DB_TABLE')
DATA_TABLE = config.get('database', 'DATA_TABLE')
db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME, use_unicode=True, charset="utf8")
cur = db.cursor()


#####
##### Check if the city needs reassembly
#####
query = "SELECT count(*) as count FROM %s where city = '%s' ORDER BY local_id" % (DB_TABLE, city)
cur.execute(query)
count = cur.fetchone()[0]
query = "SELECT local_id FROM %s where city = '%s' ORDER BY local_id DESC LIMIT 1" % (DB_TABLE, city)
cur.execute(query)
if (count == cur.fetchone()[0]+1):
    sys.exit("Nothing to rebuild for %s" % city)

#####
##### Remove all mrtg configs & all mrtg output & compiled spiders
#####
query = "SELECT country FROM %s where city = '%s' LIMIT 1" % (DB_TABLE, city)
cur.execute(query)
country = cur.fetchone()[0]
for filename in os.listdir("%s/%s/%s" % (SPIDER_DIR, country, city.replace(' ','_'))):
    if fnmatch.fnmatch(filename, '*.pyc'):
        os.remove("%s/%s/%s/%s" % (SPIDER_DIR, country, city.replace(' ','_'), filename))
    if fnmatch.fnmatch(filename, '*.cfg'):
        os.remove("%s/%s/%s/%s" % (SPIDER_DIR, country, city.replace(' ','_'), filename))
for filename in os.listdir("%s/%s/%s" % (STATS_DIR, country, city.replace(' ','_'))):
    if fnmatch.fnmatch(filename, '*.html'):
        os.remove("%s/%s/%s/%s" % (STATS_DIR, country, city.replace(' ','_'), filename))
    if fnmatch.fnmatch(filename, '*.png'):
        os.remove("%s/%s/%s/%s" % (STATS_DIR, country, city.replace(' ','_'), filename))

#####
##### Get params for the city's sensors
#####
query = "SELECT id, local_id, name, country, substances, link_src, link_xpaths FROM %s where city = '%s' ORDER BY local_id" % (DB_TABLE, city)
cur.execute(query)
new_local_id = 0
city_substances = []
for sensor_data in cur.fetchall():
    sensor_id = sensor_data[0]
    sensor_local_id = int(sensor_data[1])
    sensor_name = sensor_data[2]
    sensor_country = sensor_data[3]
    sensor_substances = sensor_data[4].split()
    sensor_link_src = sensor_data[5]
    sensor_link_xpaths = sensor_data[6]
    sensor_city_dir = city.replace(" ", "_")
    ### Get all substances collected in the city
    for substance in sensor_substances:
        if (substance not in city_substances):
            city_substances.append(substance)

    if (sensor_local_id != new_local_id):
        ### Rename spider files
        print "Renaming spider file: {1}/{2}/{3}.py".format(SPIDER_DIR, sensor_country, sensor_city_dir, sensor_local_id)
        spider_from = "{0}/{1}/{2}/{3}.py".format(SPIDER_DIR, sensor_country, sensor_city_dir, sensor_local_id)
        spider_to = "{0}/{1}/{2}/{3}.py".format(SPIDER_DIR, sensor_country, sensor_city_dir, new_local_id)
        os.rename(spider_from, spider_to)

        for substance in sensor_substances:
            ### Rename mrtg log files for each sensor substance
            print "Renaming mrtg log: {0}/{1}/{1}-{2}_{4}.log to {0}/{1}/{1}-{3}_{4}.log".format(sensor_country, sensor_city_dir, sensor_local_id, new_local_id, substance)
            mrtg_from = "{0}/{1}/{2}/{2}-{3}_{4}.log".format(STATS_DIR, sensor_country, sensor_city_dir, sensor_local_id, substance)
            mrtg_to = "{0}/{1}/{2}/{2}-{3}_{4}.log".format(STATS_DIR, sensor_country, sensor_city_dir, new_local_id, substance)
            os.rename(mrtg_from, mrtg_to)

            ### Rename mrtg oldlog files for each sensor substance
            print "Renaming mrtg oldlog: {0}/{1}/{1}-{2}_{4}.old to {0}/{1}/{1}-{3}_{4}.old".format(sensor_country, sensor_city_dir, sensor_local_id, new_local_id, substance)
            mrtg_from = "{0}/{1}/{2}/{2}-{3}_{4}.old".format(STATS_DIR, sensor_country, sensor_city_dir, sensor_local_id, substance)
            mrtg_to = "{0}/{1}/{2}/{2}-{3}_{4}.old".format(STATS_DIR, sensor_country, sensor_city_dir, new_local_id, substance)
            os.rename(mrtg_from, mrtg_to)

        ### Change local_id in the database
        print "Changing local_id from %d to %d in the database" % (sensor_local_id, new_local_id)
        query = "UPDATE %s set local_id = %d WHERE id = %d" % (DB_TABLE, new_local_id, sensor_id)
        cur.execute(query)
        db.commit()

    ### Recreate the mrtg config files
    for substance in sensor_substances:
        mrtg_name = "%s.cfg" % (substance)
        mrtg_file = "%s/%s/%s/%s" % (SPIDER_DIR, sensor_country, sensor_city_dir, mrtg_name)
        template = fill_mrtg_template(MRTG_TEMPLATE, sensor_id, new_local_id, sensor_name, city, sensor_country, substance)
        mrtg_workdir = "%s/%s/%s/" %(STATS_DIR, sensor_country, sensor_city_dir)
        write_mrtg_template(mrtg_file, mrtg_workdir, template)

    ### Increment new_local_id
    new_local_id += 1

### create index with indexmakerCleanup old mrtg logs (if any)
# indexmaker --title="Brno PM10 Levels (<a href=no2.html>NO2</a>  <a href=o3.html>O3</a> <a href=pm25.html>PM25</a>)" --nolegend cz/brno/pm10.cfg
for substance in city_substances:
    print substance
    links = ""
    for sub in city_substances:
        if (sub != substance):
            if (sub == 'pm10'):
                links += "<a href=index.html>%s</a> " % (sub.upper())
            else:
                links += "<a href=%s.html>%s</a> " % (sub, sub.upper())

    if (substance == 'pm10'):
        command = "indexmaker --output=%s/%s/%s/%s.html --title=\"%s %s Levels (%s)\" --nolegend %s/%s/%s/%s.cfg" % (STATS_DIR, sensor_country, sensor_city_dir, "index", city.capitalize(), substance.upper(), links, SPIDER_DIR, sensor_country, sensor_city_dir, substance)
    else:
        command = "indexmaker --output=%s/%s/%s/%s.html --title=\"%s %s Levels (%s)\" --nolegend %s/%s/%s/%s.cfg" % (STATS_DIR, sensor_country, sensor_city_dir, substance, city.capitalize(), substance.upper(), links, SPIDER_DIR, sensor_country, sensor_city_dir, substance)

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
##### Cleanup old mrtg logs (if any)
#####
for filename in os.listdir("%s/%s/%s" % (STATS_DIR, country, city.replace(' ','_'))):
    if (fnmatch.fnmatch(filename, '*.log') | fnmatch.fnmatch(filename, '*.old')):
        if (int(filename.split('-')[1].split('_')[0]) >= new_local_id):
            os.remove("%s/%s/%s/%s" % (STATS_DIR, country, city.replace(' ','_'), filename))

#####
##### doooneeee chrr
#####
print "Done !"
print "Please verify all is ok in %s/%s/%s" % (SPIDER_DIR, sensor_country, sensor_city_dir)
print "Also verify all is ok in %s/%s/%s" % (STATS_DIR, sensor_country, sensor_city_dir)
