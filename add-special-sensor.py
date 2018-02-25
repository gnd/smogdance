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
    chunk of data for later processing, by 'normal' sensors,
    such as chmi or shmu pages, thus saving total requests sent

    gnd, 2017 - 2018
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

### check if proper arguments
if (len(sys.argv) < PARAMS):
    sys.exit("Not enough arguments.\nUsage: ./add-special-sensor.py <name> <link_src> <response_size> <country> <city> <type>")
else:
    try:
        response_size = int(sys.argv[4])
    except:
        sys.exit("Bad size parameter: %s\nUsage: ./add-special-sensor.py <name> <link_src> <response_size> <country> <city> <type>" % (sys.argv[4]))


def fill_spider_template(template, name, link_src, checks, type):
    f = file(template, 'r')
    tmp = f.read()
    f.close()
    res = tmp.replace("SPIDER_NAME", name)
    res = res.replace("LINK_SRC", link_src)
    outputs = ""
    if (type == 'bulk'):
        expected_string_all = []
        remote_string_all = []
        response_size = int(checks.split('===')[0])
        checkpoints = checks.split('===')[1]
        for line in checkpoints.split(";"):
            expected_string = line.split("--")[0]
            remote_string = line.split("--")[1]
            expected_string_all.append(expected_string)
            remote_string_all.append("%s")
            outputs += "        %s = response.xpath('%s').extract()[1]\n" % (expected_string, remote_string)
        outputs += "        EXPECTED = '%s'\n" % (' '.join(expected_string_all))
        outputs += "        REMOTE = \"%s\" %% (%s)\n" % (' '.join(remote_string_all), ','.join(expected_string_all))
        outputs += "        if ((EXPECTED == REMOTE) and (response.status == 200) and (len(response.text) > %d)):\n" % (response_size)
        outputs += "            file('%s/%s.html','w').write(response.text)\n" % (TEMP_DIR, name)
        outputs += '            print "OK"\n'
        outputs += "        else:\n"
        outputs += "            os.remove('%s/%s.html')\n" % (TEMP_DIR, name)
        outputs += '            print "Integrity check failed"\n'
    res = res.replace("OUTPUTS", outputs)
    return res


def write_template(filename, template):
    f = file(filename, 'w')
    f.write(template)
    f.close()


### initial checks
if (len(sys.argv) < PARAMS):
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
template = fill_spider_template(SPIDER_TEMPLATE, name, link_src, checks, type)
write_template(spider_file, template)
