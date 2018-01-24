#!/usr/bin/python
#
# smog dance installer script
#
############################################################

import os
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import shlex
import MySQLdb
import subprocess
import unicodedata
import ConfigParser

# globals
config_name = "settings_python"
bash_config_name = "settings_bash"

#//TODO - dont run after already installed

# create config object
config = ConfigParser.RawConfigParser()

## create the database section
#//TODO - rename db_table to sensor_table
config.add_section('database')
db_host = raw_input("Please provide db host: ")
db_user = raw_input("Please provide db user: ")
db_name = raw_input("Please provide db name: ")
db_pass = raw_input("Please provide db pass: ")
db_table = "sensors"
data_table = "sensor_data"
config.set('database', 'DB_HOST', db_host)
config.set('database', 'DB_NAME', db_name)
config.set('database', 'DB_USER', db_user)
config.set('database', 'DB_PASS', db_pass)
config.set('database', 'DB_TABLE', db_table)
config.set('database', 'DATA_TABLE', data_table)

## create the globals config section
#//TODO - sanitize and/or verify all user input
#//TODO - default option for data_dir - determine working directory
#//TODO - default option - search for scrapy first
#//TODO - add comments
config.add_section('globals')
scrapy_bin = raw_input("Please input Scrapy location (usually /usr/bin/scrapy): ")
data_dir = raw_input("Please input data directory (not accessible via web): ")
stats_dir = raw_input("Please input stats direcotry (accessible via web): ")
stats_url = raw_input("Please input the stats URL (eg. stats.smog.dance): ")
temp_dir = data_dir + "/temp"
spider_dir = data_dir + "/countries"
definitions_dir = data_dir + "/definitions"
config.set('globals', 'SCRAPY_BIN', scrapy_bin)
config.set('globals', 'DATA_DIR', data_dir)
config.set('globals', 'SPIDER_DIR', spider_dir)
config.set('globals', 'DEFINITIONS_DIR', definitions_dir)
config.set('globals', 'STATS_DIR', stats_dir)
config.set('globals', 'TEMP_DIR', temp_dir)
config.set('globals', 'SPIDER_TEMPLATE', 'template.spider')
config.set('globals', 'MRTG_TEMPLATE', 'template.mrtg')
config.set('globals', 'SPIDER_COMMAND', 'poll-sensor.py')
if (not os.path.isdir("%s" % (temp_dir))):
    os.makedirs("%s" % (temp_dir))
if (not os.path.isdir("%s" % (spider_dir))):
        os.makedirs("%s" % (spider_dir))

## write configuration
print "Writing config file %s" % config_name
with open(config_name, 'wb') as configfile:
    config.write(configfile)

# create settings_bash
report_from = raw_input("Please provide a mail sender address for reporting: ")
report_recps = raw_input("Please provide a mail destination address for reporting: ")
f = open(bash_config_name, "w")
f.write("DATA_DIR=\"%s\"\n" % data_dir)
f.write("RUNLIST=\"$DATA_DIR/mrtg.runlist\"\n")
f.write("REPORT_FROM=\"%s\"\n" % report_from)
f.write("REPORT_RECPS=\"%s\"\n" % report_recps)
f.close()

# create database
print "Trying to connect to the database"
db_err = False
try:
    db = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name)
    cur = db.cursor()
except:
    print "Could not connect to the database %s on host %s as user %s" % (db_name, db_host, db_user)
    print "Please check database setup yourself."
    db_err = True

if not db_err:
    db_empty = True
    table_err = False
    print "Checking if tables exists"
    query = "SHOW TABLES"
    cur.execute(query)
    if cur.rowcount != 0:
        print "DB is not empty, will not create tables"
        db_empty = False
        db.close()

    if db_empty:
        query = ("CREATE TABLE %s ("
        "id int AUTO_INCREMENT PRIMARY KEY, "
        "local_id int, "
        "name varchar(255), "
        "link_src varchar(255), "
        "link_web varchar(255), "
        "link_stat varchar(255), "
        "link_xpaths text, "
        "country varchar(255), "
        "city varchar(255), "
        "gps varchar(255), "
        "type varchar(255), "
        "substances varchar(255), "
        "added timestamp default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP, "
        "last_run timestamp NULL on update CURRENT_TIMESTAMP, "
        "last_state int, "
        "active int"
        ")" % (db_table))
        print "Creating table %s: %s" % (db_table, query)
        try:
            cur.execute(query)
        except (MySQLdb.Error, MySQLdb.Warning) as e:
            print "Creating table %s failed: %s" % (db_table, e)
            table_err = True

        query = ("CREATE TABLE %s ("
        "sensor_id int, "
        "timestamp timestamp default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP, "
        "co float, "
        "no2 float, "
        "o3 float, "
        "pm10 float, "
        "pm25 float, "
        "so2 float"
        ")" % (data_table))
        print "Creating table %s: %s" % (data_table, query)
        try:
            cur.execute(query)
        except (MySQLdb.Error, MySQLdb.Warning) as e:
            print "Creating table %s failed: %s" % (data_table, e)
            table_err = True

        if not table_err:
            print "Tables successfuly created!"
            db.close()
        else:
            print "There were errors creating the tables, please fix manually"
            db.close()


# run spider templates
for filename in os.listdir(definitions_dir):
    print "Adding sensors from %s" % filename
    filepath = "%s/%s" % (definitions_dir, filename)
    f = open(filepath, 'r')
    for line in f.readlines():
        definition = line.strip().replace("TEMP_DIR", temp_dir).replace("STATS_URL", stats_url)
        if ("special" in filename):
            command = "%s/add-special-sensor.py %s" % (data_dir, definition)
        else:
            command = "%s/add-sensor.py %s" % (data_dir, definition)
        command_args = shlex.split(command)
        #print "Running: %s" % command
        try:
            process = subprocess.Popen(command_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out = process.communicate()
        except subprocess.CalledProcessError as e:
            print e
            pass
    f.close()

# finito
#//TODO - add cronjob definitions
print "Install finished."
