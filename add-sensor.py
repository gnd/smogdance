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
import unicodedata
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
    if (substance == "pm10"):
        maxbytes = 300
    if (substance == "co"):
        maxbytes = 3000
    res = res.replace("MAXBYTES", str(maxbytes))
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

### initial checks
if (len(sys.argv) < 10):
    sys.exit("Not enough parameters")

### connect to the db
DB_HOST = config.get('database', 'DB_HOST')
DB_USER = config.get('database', 'DB_USER')
DB_PASS = config.get('database', 'DB_PASS')
DB_NAME = config.get('database', 'DB_NAME')
DB_TABLE = config.get('database', 'DB_TABLE')
db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
cur = db.cursor()

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
local_id = int(cur.fetchone()[0])

### execute query
print "Inserting %s-%s into db" % (city, name)
query = "INSERT INTO %s VALUES(0,'%d','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s', now(), %d, '%d', '%d')" % (DB_TABLE, local_id, name, link_src, link_web, link_stat, link_xpaths, country, city, gps, type, substances, 0, 0, 1)
cur.execute(query)
id = int(cur.lastrowid)
print "Inserting %s-%s into the temp table" % (city, name)
query = "INSERT INTO %s_temp VALUES('%d',now(),0,0,0,0,0,0)" % (DATA_TABLE, id)
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
    template = fill_mrtg_template(MRTG_TEMPLATE, id, local_id, name, city, country, substance)
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

    #//TODO - create prerequisities
    #//TODO - add mrtg to prerequisities
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
