#!/usr/bin/python
#
# This creates a new sensor. In particular it:
#   - adds a special sensor defition to the database
#   - adds spiderfile to disk
#
# Note:
# A special sensor is eg. a sensor that just downloads a bigger
# chunk of data for later processing, by 'normal' sensors,
# such as chmi or shmu pages, thus saving total requests sent
####################################################################

import os
import sys
import shlex
import MySQLdb
import subprocess
import ConfigParser

### load config
config = ConfigParser.ConfigParser()
config.readfp(open('settings_python'))
PARAMS = 7

### check if proper arguments
if (len(sys.argv) < PARAMS):
    sys.exit("Not enough arguments.\nUsage: ./add-special-sensor.py <name> <link_src> <response_size> <country> <city> <type>")
else:
    try:
        response_size = int(sys.argv[3])
    except:
        sys.exit("Bad size parameter: %s\nUsage: ./add-special-sensor.py <name> <link_src> <response_size> <country> <city> <type>" % (sys.argv[3]))


def fill_spider_template(template, name, link_src, size, type):
    f = file(template, 'r')
    tmp = f.read()
    f.close()
    res = tmp.replace("SPIDER_NAME", name)
    res = res.replace("LINK_SRC", link_src)
    if (type == 'bulk'):
        outputs = "        if ((response.status == 200) and len(response.text) > %d):\n" % (size)
        outputs += "            file('%s/%s.html','w').write(response.text)\n" % (DATA_DIR, name)
        outputs += '            print "OK"\n'
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
DB_HOST = config.getint('database', 'DB_HOST')
DB_USER = config.getint('database', 'DB_USER')
DB_PASS = config.getint('database', 'DB_PASS')
DB_NAME = config.getint('database', 'DB_NAME')
DB_TABLE = config.getint('database', 'DB_TABLE')
db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
cur = db.cursor()


### process input
name = sys.argv[1]
link_src = sys.argv[2]
response_size = int(sys.argv[3])
country = sys.argv[4]
city = sys.argv[5]
type = sys.argv[6]


### execute query
print "Inserting %s-%s into db" % ("special", name)
query = "INSERT INTO %s VALUES(0,'%d','%s','%s','','','%d','%s','','','%s','', now(), '%d', '%d', '%d')" % (DB_TABLE, 0, name, link_src, response_size, country, type, 0, 0, 1)
cur.execute(query)
db.commit()
id = int(cur.lastrowid)
db.close()

### check if the directories are created
DATA_DIR = config.getint('globals', 'DATA_DIR')
if (not os.path.isdir("%s/%s" % (DATA_DIR, country))):
    os.makedirs("%s/%s" % (DATA_DIR, country))

### create new sensor spider on disk
SPIDER_TEMPLATE = config.getint('globals', 'SPIDER_TEMPLATE')
spider_name = "special-%s" % (name)
spider_file = "%s/%s/%s.py" % (DATA_DIR, country, spider_name)
template = fill_spider_template(SPIDER_TEMPLATE, name, link_src, response_size, type)
write_template(spider_file, template)
