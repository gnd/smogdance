#!/usr/bin/env python
# # -*- coding: utf-8 -*-

""" Smogdance

    An open-source collection of scripts to collect, store and graph air quality data
    from publicly available sources.

    This runs data collection on all sensors.

    In particular it:
    - runs active special sensors as first (sensor type = bulk), every 30 minutes
    - then runs the rest of the active sensors every 10 minutes
    - readings are stored into the db
    - if a gives wrong output, it is marked as problematic, if on the next readings
    the problem repeats the sensor is made inactive and a notification mail is sent.

    gnd, 2017 - 2018
"""

import os
import sys
import time
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
SPIDER_DIR = config.get('globals', 'SPIDER_DIR')

### connect to the db
DB_HOST = config.get('database', 'DB_HOST')
DB_USER = config.get('database', 'DB_USER')
DB_PASS = config.get('database', 'DB_PASS')
DB_NAME = config.get('database', 'DB_NAME')
DB_TABLE = config.get('database', 'DB_TABLE')
DATA_TABLE = config.get('database', 'DATA_TABLE')
DATA_TABLE_TEMP = config.get('database', 'DATA_TABLE_TEMP')
DATA_TABLE_MONTH = config.get('database', 'DATA_TABLE_MONTH')
db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
cur = db.cursor()

#####
##### Run special sensors (bulk collection & etc)
#####
print "-------------- Starting collection: %s --------------" % (time.strftime("%Y-%m-%d %H:%M"))
special_sensors = []
### add special sensors
query = "SELECT id, name, country, city, last_state FROM %s where active = 1 and type = 'bulk' and last_run < (now() - INTERVAL 30 minute)" % (DB_TABLE)
cur.execute(query)
for row in cur.fetchall():
    special_sensors.append(row)

if len(special_sensors) == 0:
    print "No runnable special sensors found"
else:
    ### run spiders for special sensors
    for sensor in special_sensors:
        sensor_id = sensor[0]
        sensor_name = sensor[1]
        sensor_country = sensor[2]
        sensor_city = sensor[3]
        sensor_last_state = sensor[4]
        sensor_cmd = "%s runspider %s/%s/special-%s.py --loglevel ERROR -o - -t csv" % (SCRAPY_BIN, SPIDER_DIR, sensor_country, sensor_name)
        spider_args = shlex.split(sensor_cmd)

        ### run the spider
        try:
            print "%s Trying to run %s/special-%s" % (time.strftime("%Y-%m-%d %H:%M:%S"), sensor_country, sensor_name),
            process = subprocess.Popen(spider_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (data_out, err_out) = process.communicate()
            returncode = process.returncode
        except:
            print "ERROR Couldnt run special sensor %s/special-%s" % (sensor_country, sensor_name)
            print "%s" % sys.exc_info()[1]
            pass

        ### if non-zero return, or err_out we have a problem
        if ((returncode != 0) or (err_out != "")):
            print "Spider %s/special-%s failed: %s" % (sensor_country, sensor_name, err_out[1])
            if (sensor_last_state == 0):
                print "Setting sensor %s state as 1" % (sensor_id)
                ### 0 is ok 1 is failed
                query = "UPDATE %s SET last_state = 1 WHERE id = %s" % (DB_TABLE, sensor_id)
                cur.execute(query)
                ### notify
                try:
                    notify_cmd = "%s/report-state-change.sh %s %s" % (DATA_DIR, sensor_name, "failed")
                    notify_args = shlex.split(notify_cmd)
                    process = subprocess.Popen(notify_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    process.communicate()
                except:
                    print "ERROR Couldnt report sensor state change:\n"
                    print "%s" % sys.exc_info()[1]
                    pass

            ### will not disable sensors for the time-being
            if (sensor_last_state == 1):
                print "setting sensor %s as inactive" % (sensor_id)
                ### 0 is ok 1 is failed, mark as inactive
                query = "UPDATE %s SET active = 0 WHERE id = %s" % (DB_TABLE, sensor_id)
                cur.execute(query)
                ### notify
                try:
                    print "Reporting sensor failure"
                    notify_cmd = "%s/report-state-change.sh %s %s" % (DATA_DIR, sensor_name, "inactive")
                    notify_args = shlex.split(notify_cmd)
                    process = subprocess.Popen(notify_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    process.communicate()
                except:
                    print "ERROR Couldnt report sensor state change:\n"
                    print "%s" % sys.exc_info()[1]
                    pass
            db.commit()

        ### or store the data in the database
        else:
            ### set last state and last_run
            query = "UPDATE %s SET last_state = 0, last_run = now() WHERE id = %s" % (DB_TABLE, sensor_id)
            cur.execute(query)
            db.commit()
            print ".. OK"

#####
##### Run normal sensors
#####

sensors = []
query = "SELECT id, local_id, country, city, last_state, substances, type FROM %s where active = 1 and (type = 'hourly' or type ='hourly-tor') and last_run < (now() - INTERVAL 10 minute)" % (DB_TABLE)
cur.execute(query)
for row in cur.fetchall():
    sensors.append(row)

if len(sensors) == 0:
    sys.exit("Exiting: no runnable sensors found")


### run spiders for sensors
for sensor in sensors:
    errors_found = False
    sensor_id = sensor[0]
    sensor_local_id = sensor[1]
    sensor_country = sensor[2]
    sensor_city = sensor[3]
    sensor_last_state = sensor[4]
    sensor_substances = sensor[5].split()
    sensor_type = sensor[6]
    if (sensor_type == 'hourly'):
        sensor_cmd = "%s runspider %s/%s/%s/%d.py --loglevel ERROR -o - -t csv" % (SCRAPY_BIN, SPIDER_DIR, sensor_country, sensor_city.replace(" ","_"), sensor_local_id)
    if (sensor_type == 'hourly-tor'):
        sensor_cmd = "torify %s runspider %s/%s/%s/%d.py --loglevel ERROR -o - -t csv" % (SCRAPY_BIN, SPIDER_DIR, sensor_country, sensor_city.replace(" ","_"), sensor_local_id)
    spider_args = shlex.split(sensor_cmd)

    ### run the spider
    try:
        print "%s Trying to run %s/%s/%s" % (time.strftime("%Y-%m-%d %H:%M:%S"), sensor_country, sensor_city, sensor_local_id),
        #print sensor_cmd
        process = subprocess.Popen(spider_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (data_out, err_out) = process.communicate()
        returncode = process.returncode
    except:
        print "ERROR Couldnt run sensor %s/%s/%s" % (sensor_country, sensor_city, sensor_id)
        print "%s" % sys.exc_info()[1]
        pass

    ### if non-zero return, or err_out we have a problem
    if ((returncode != 0) or (err_out != "")):
        print "\nSpider %s/%s/%s failed:" % (sensor_country, sensor_city, sensor_local_id)
        print err_out
        if (sensor_last_state == 0):
            print "Setting sensor %s state as 1" % (sensor_id)
            ### 0 is ok 1 is failed
            query = "UPDATE %s SET last_state = 1 WHERE id = %s" % (DB_TABLE, sensor_id)
            cur.execute(query)

        if (sensor_country == 'hu'):
            if ((sensor_last_state >= 1) and (sensor_last_state < 5)):
                print "Sensor %s gets more chances, setting last_state to %d" % (sensor_id, sensor_last_state+1)
                ### 0 is ok 1 is failed, mark as inactive
                query = "UPDATE %s SET last_state = %d WHERE id = %s" % (DB_TABLE, sensor_last_state+1, sensor_id)
                cur.execute(query)
            if (sensor_last_state == 5):
                print "Setting sensor %s as inactive:" % (sensor_id)
                ### 0 is ok 1 is failed, mark as inactive
                query = "UPDATE %s SET active = 0 WHERE id = %s" % (DB_TABLE, sensor_id)
                cur.execute(query)
                ### notify
                try:
                    print "Reporting sensor failure"
                    notify_cmd = "%s/report-state-change.sh %s %s" % (DATA_DIR, sensor_id, "failed fifth time")
                    notify_args = shlex.split(notify_cmd)
                    process = subprocess.Popen(notify_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    out = process.communicate()
                except:
                    print "ERROR Couldnt report sensor state change:\n"
                    print "%s %s %s" % sys.exc_info()
                    pass
        else:
            if (sensor_last_state == 1):
                print "Setting sensor %s as inactive:" % (sensor_id)
                ### 0 is ok 1 is failed, mark as inactive
                query = "UPDATE %s SET active = 0 WHERE id = %s" % (DB_TABLE, sensor_id)
                cur.execute(query)
        db.commit()

    ### or store the data in the database
    else:
        substance_names = ','.join(sensor_substances)
        substance_values = ','.join(data_out.replace(",",".").split())
        substance_values = substance_values.replace("None", "NULL")
        substance_values = substance_values.replace("**", "NULL")
        substance_values = substance_values.replace("*", "NULL")
        substance_values = substance_values.replace("PDL", "NULL")
        # temp data table keeping just the last record for every sensor
        update_string = ""
        temp_values = substance_values.replace("NULL","0").split(",")
        for i in range(len(sensor_substances)):
            update_string += sensor_substances[i] + "=\"" + temp_values[i]+ "\", "
        query = "UPDATE %s SET % stimestamp = now() WHERE sensor_id = %d" % (DATA_TABLE_TEMP, update_string, sensor_id)
        cur.execute(query)
        # last month storage
        query = "INSERT INTO %s (sensor_id, timestamp, %s) VALUES(%s, now(), %s)" % (DATA_TABLE_MONTH, substance_names, sensor_id, substance_values)
        cur.execute(query)
        # long term storage
        query = "INSERT INTO %s (sensor_id, timestamp, %s) VALUES(%s, now(), %s)" % (DATA_TABLE, substance_names, sensor_id, substance_values)
        cur.execute(query)

        ### set last state and last_run
        query = "UPDATE %s SET last_state = 0, last_run = now() WHERE id = %s" % (DB_TABLE, sensor_id)
        cur.execute(query)
        db.commit()
        print ".. OK"

db.close()
