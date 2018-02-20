#!/usr/bin/env python
# # -*- coding: utf-8 -*-

""" Smogdance

    An open-source collection of scripts to collect, store and graph air quality data
    from publicly available sources.

    Helper script to recreate spider directories for cities with deleted sensors

    gnd, 2017 - 2018
"""

import os
import sys
import time
import shlex
import MySQLdb
import datetime
import subprocess
import ConfigParser

#####
##### Load config
#####
settings_file = os.path.join(sys.path[0], 'settings_python')
config = ConfigParser.ConfigParser()
config.readfp(open(settings_file))
SPIDER_DIR = config.get('globals', 'SPIDER_DIR')
SPIDER_TEMPLATE = config.get('globals', 'SPIDER_TEMPLATE')

#####
##### Define functions (TODO: create a file with commonly used functions to be included)
#####
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

def write_template(filename, template):
    f = file(filename, 'w')
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
db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
cur = db.cursor()

#####
##### Check input TODO (sanitize like in poll-city)
#####
city = ""
if (len(sys.argv) > 1):
    city = sys.argv[1]
else:
    sys.exit("Not enough parameters")

#####
##### Get params for the city's sensors
#####
query = "SELECT id, local_id, name, country, substances, link_src, link_xpaths FROM %s where city = '%d' ORDER BY local_id" % (DB_TABLE, city)
cur.execute(query)
new_local_id = 0
for sensor_data in cur.fetchall():
    sensor_id = sensor_data[0]
    sensor_local_id = int(sensor_data[1])
    sensor_name = sensor_data[2]
    sensor_country = sensor_data[3]
    sensor_substances = sensor_data[4]
    sensor_link_src = sensor_data[5]
    sensor_link_xpaths = sensor_data[6]
    sensor_city_dir = sensor_city.replace(" ", "_")

    ### Rename old spider files
    command = "mv {0}/{1}/{2}/{3}.py {0}/{1}/{2}/old_{3}.py".format(SPIDER_DIR, sensor_country, sensor_city_dir, sensor_local_id)
    command_args = shlex.split(command)
    try:
        print "Renaming spider file: {0}/{1}/{2}/{3}.py".format(SPIDER_DIR, sensor_country, sensor_city_dir, sensor_local_id)
        process = subprocess.Popen(command_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = process.communicate()
    except subprocess.CalledProcessError as e:
        print e
        sys.exit("Renaming spider file {0}/{1}/{2}/{3}.py failed").format(SPIDER_DIR, sensor_country, sensor_city_dir, sensor_local_id)

    ### For each sensor recreate their spider files
    print "Creating new spider file: {0}/{1}/{2}/{3}.py".format(SPIDER_DIR, sensor_country, sensor_city_dir, new_local_id)
    spider_file = "%s/%s/%s/%s.py" % (SPIDER_DIR, sensor_country, sensor_city_dir, new_local_id)
    template = fill_spider_template(SPIDER_TEMPLATE, sensor_name, sensor_link_src, sensor_link_xpaths)
    write_template(spider_file, template)

    ### Change local_id in the database
    print "Changing local_id from %d to %d in the database" % (sensor_local_id, new_local_id)
    query = "UPDATE %s set local_id = %d WHERE id = %d" % (DB_TABLE, new_local_id, sensor_id)
    cur.execute(query)
    db.commit()

    ### Increment new_local_id
    new_local_id += 1


#####
##### Cleanup
#####
print "Done !"
print "Please cleanup old sensor files in %s/%s/%s" % (SPIDER_DIR, sensor_country, sensor_city_dir)
