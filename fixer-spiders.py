#!/usr/bin/env python
# # -*- coding: utf-8 -*-

""" Smogdance

    An open-source collection of scripts to collect, store and graph air quality data
    from publicly available sources.

    This polls SQL for the latest values of all sensors from a given city.

    gnd, 2017 - 2018
"""

import os
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import MySQLdb
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

all_substances = ["co","no2","o3","pm10","pm25","so2"]

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

### connect to the db
DB_HOST = config.get('database', 'DB_HOST')
DB_USER = config.get('database', 'DB_USER')
DB_PASS = config.get('database', 'DB_PASS')
DB_NAME = config.get('database', 'DB_NAME')
DB_TABLE = config.get('database', 'DB_TABLE')
DATA_TABLE = config.get('database', 'DATA_TABLE')
db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME, charset='utf8')
cur = db.cursor()

# get all AT sensors  -- fixing AT - 26.2.2018
query = "SELECT local_id, name, country, city, link_src, link_xpaths FROM %s WHERE country = 'at' and type ='hourly' ORDER BY id" % (DB_TABLE)
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
    template = fill_spider_template(SPIDER_TEMPLATE, name, link_src, link_xpaths)
    write_template(spider_file, template)
