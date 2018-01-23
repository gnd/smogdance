#!/usr/bin/python
#
# runs collection on all sensors
################################
import os
import sys
import shlex
import MySQLdb
import subprocess
import ConfigParser

### load config
config = ConfigParser.ConfigParser()
config.readfp(open(settings.conf))

### connect to the db
DB_HOST = config.getint('database', 'DB_HOST')
DB_USER = config.getint('database', 'DB_USER')
DB_PASS = config.getint('database', 'DB_PASS')
DB_NAME = config.getint('database', 'DB_NAME')
DB_TABLE = config.getint('database', 'DB_TABLE')
db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
cur = db.cursor()

#####
##### Run special sensors (bulk collection & etc)
#####
DATA_DIR = config.getint('globals', 'DATA_DIR')
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
        sensor_cmd = "%s runspider %s/%s/special-%s.py --nolog -o - -t csv" % ("/usr/local/bin/scrapy", DATA_DIR, sensor_country, sensor_name)
        spider_args = shlex.split(sensor_cmd)

        ### run the spider
        try:
            print "Trying to run %s/special-%s" % (sensor_country, sensor_name)
            print sensor_cmd
            process = subprocess.Popen(spider_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out = process.communicate()
        except:
            # dont be lazy gnd
            pass

        ### if non-zero return, we have a problem
        print out
        if ((out[1] != "") or (out[0].strip() != "OK")):
            print "Spider %s/special-%s failed: %s" % (sensor_country, sensor_name, out[1])
            if (sensor_last_state == 0):
                print "setting sensor %s state as 1" % (sensor_id)
                ### 0 is ok 1 is failed
                query = "UPDATE %s SET last_state = 1 WHERE id = %s" % (DB_TABLE, sensor_id)
                cur.execute(query)
                ### notify
                try:
                    notify_cmd = "%s/report-state-change.sh %s %s" % (DATA_DIR, sensor_name, "failed")
                    print notify_cmd
                    notify_args = shlex.split(notify_cmd)
                    process = subprocess.Popen(notify_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    out = process.communicate()
                except:
                    print "Couldnt report sensor state change\n"
                    pass

            ### will not disable sensors for the time-being
            if (sensor_last_state == 666):
                print "setting sensor %s as inactive" % (sensor_id)
                ### 0 is ok 1 is failed, mark as inactive
                query = "UPDATE %s SET active = 0 WHERE id = %s" % (DB_TABLE, sensor_id)
                cur.execute(query)
                ### notify
                try:
                    notify_cmd = "%s/report-state-change.sh %s %s" % (DATA_DIR, sensor_name, "inactive")
                    print notify_cmd
                    notify_args = shlex.split(notify_cmd)
                    process = subprocess.Popen(notify_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    out = process.communicate()
                except:
                    print "Couldnt report sensor state change\n"
                    pass

            db.commit()

        ### or store the data in the database
        else:
            ### set last state and last_run
            query = "UPDATE %s SET last_state = 0, last_run = now() WHERE id = %s" % (DB_TABLE, sensor_id)
            cur.execute(query)
            db.commit()



#####
##### Run normal sensors
#####

sensors = []
query = "SELECT id, local_id, country, city, last_state, substances FROM %s where active = 1 and type = 'hourly' and last_run < (now() - INTERVAL 10 minute)" % (DB_TABLE)
cur.execute(query)
for row in cur.fetchall():
    sensors.append(row)

if len(sensors) == 0:
    sys.exit("Exiting: no runnable sensors found")


### run spiders for sensors
for sensor in sensors:
    sensor_id = sensor[0]
    sensor_local_id = sensor[1]
    sensor_country = sensor[2]
    sensor_city = sensor[3]
    sensor_last_state = sensor[4]
    sensor_substances = sensor[5].split()
    sensor_cmd = "%s runspider %s/%s/%s/%d.py --nolog -o - -t csv" % ("/usr/local/bin/scrapy", DATA_DIR, sensor_country, sensor_city.replace(" ","_"), sensor_local_id)
    spider_args = shlex.split(sensor_cmd)

    ### run the spider
    try:
        print "Trying to run %s/%s/%s" % (sensor_country, sensor_city, sensor_local_id)
        #print sensor_cmd
        process = subprocess.Popen(spider_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = process.communicate()
    except:
        # dont be lazy gnd
        pass

    ### if non-zero return, we have a problem
    if (out[1] != ""):
        print "Spider %s/%s/%s failed:" % (sensor_country, sensor_city, sensor_local_id)
        print out[1]
        if (sensor_last_state == 0):
            print "setting sensor %s state as 1" % (sensor_id)
            ### 0 is ok 1 is failed
            query = "UPDATE %s SET last_state = 1 WHERE id = %s" % (DB_TABLE, sensor_id)
            cur.execute(query)

        if (sensor_last_state == 1):
            print "setting sensor %s as inactive:" % (sensor_id)
            ### 0 is ok 1 is failed, mark as inactive
            query = "UPDATE %s SET active = 0 WHERE id = %s" % (DB_TABLE, sensor_id)
            cur.execute(query)
        db.commit()

    ### or store the data in the database
    else:
        print "storing values for " + str(sensor_id)
        substance_names = ','.join(sensor_substances)
        substance_values = ','.join(out[0].replace(",",".").split())
        substance_values = substance_values.replace("None", "NULL")
        substance_values = substance_values.replace("**", "NULL")
        substance_values = substance_values.replace("*", "NULL")
        query = "INSERT INTO sensor_data (sensor_id, timestamp, %s) VALUES(%s, now(), %s)" % (substance_names, sensor_id, substance_values)
        print query
        cur.execute(query)

        ### set last state and last_run
        query = "UPDATE %s SET last_state = 0, last_run = now() WHERE id = %s" % (DB_TABLE, sensor_id)
        cur.execute(query)
        db.commit()

db.close()
