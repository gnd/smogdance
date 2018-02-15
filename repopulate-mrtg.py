#!/usr/bin/env python
# # -*- coding: utf-8 -*-

""" Smogdance

    An open-source collection of scripts to collect, store and graph air quality data
    from publicly available sources.

    Helper script to repopulate MRTG with historical data.

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

### load config
settings_file = os.path.join(sys.path[0], 'settings_python')
config = ConfigParser.ConfigParser()
config.readfp(open(settings_file))
STATS_DIR = config.get('globals', 'STATS_DIR')

### connect to the db
DB_HOST = config.get('database', 'DB_HOST')
DB_USER = config.get('database', 'DB_USER')
DB_PASS = config.get('database', 'DB_PASS')
DB_NAME = config.get('database', 'DB_NAME')
DB_TABLE = config.get('database', 'DB_TABLE')
DATA_TABLE = config.get('database', 'DATA_TABLE')
db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
cur = db.cursor()

### check input TODO (sanitize like in poll-city)
city = ""
if (len(sys.argv) > 1):
    city = sys.argv[1]

#####
##### Reconstruct MRTG logfiles from scratch
#####
if (city != ""):
    query = "SELECT id, local_id, country, city, substances FROM %s where type = 'hourly' and city = '%s'" % (DB_TABLE, city)
else:
    query = "SELECT id, local_id, country, city, substances FROM %s where type = 'hourly'" % (DB_TABLE)
cur.execute(query)
for row in cur.fetchall():
    sensor_id = row[0]
    sensor_local_id = row[1]
    sensor_country = row[2]
    sensor_city = row[3]
    sensor_substances = row[4].split()
    print "Repopulating %s-%d: " % (sensor_city, sensor_local_id)

    # we could as well open all substance logs at once (and not iterate over substances, but wth..)
    for substance in sensor_substances:
        print substance

        # check if the directories are created
        city_dir = sensor_city.replace(" ", "_")
        if (not os.path.isdir("%s/%s" % (STATS_DIR, sensor_country))):
            os.makedirs("%s/%s" % (STATS_DIR, sensor_country))
        if (not os.path.isdir("%s/%s/%s" % (STATS_DIR, sensor_country, city_dir))):
            os.makedirs("%s/%s/%s" % (STATS_DIR, sensor_country, city_dir))

        # create new logfile
        query = "SELECT timestamp, %s FROM %s where sensor_id = %d ORDER BY timestamp ASC" % (substance,DATA_TABLE,sensor_id)
        cur.execute(query)
        previous_value = 0
        first = True

        # create an ideal mrtg-esque logfile array
        log_array = []
        for row in cur.fetchall():
            # if we are processing the first log value
            if first:
                # fix null value - if we start with None we make it zero
                substance_value = row[1]
                if substance_value is None:
                    substance_value = 0
                # get initial timestamp and round it off
                timestamp = int(time.mktime(row[0].timetuple()))
                if (timestamp % 300) > 150:
                    count = (timestamp / 300) + 1
                    timestamp = count * 300
                else:
                    count = time_diff / 300
                    timestamp = count * 300
                # append to log_array
                log_array.append("%s %d %d %d %d\n" % (timestamp, substance_value, substance_value, substance_value, substance_value))
                # flip values
                old_timestamp = timestamp
                old_substance_value = substance_value
                first = False
            # .. or processing further value
            else:
                substance_value = row[1]
                timestamp = int(time.mktime(row[0].timetuple()))
                time_diff = timestamp - old_timestamp
                if (time_diff % 300) > 150:
                    count = (time_diff / 300) + 1
                    now_timestamp = old_timestamp + count * 300
                else:
                    count = time_diff / 300
                    now_timestamp = old_timestamp + count * 300
                # extrapolate time values till now
                if count > 1:
                    for i in range(count-1):
                        extrapolated_timestamp = old_timestamp + (i+1)*300
                        log_array.append("%s %d %d %d %d\n" % (extrapolated_timestamp, old_substance_value, old_substance_value, old_substance_value, old_substance_value))
                # fix null values
                if substance_value is None:
                    substance_value = old_substance_value
                # append to log_array now
                log_array.append("%s %d %d %d %d\n" % (now_timestamp, substance_value, substance_value, substance_value, substance_value))
                # finally, flip values
                old_timestamp = now_timestamp
                old_substance_value = substance_value
        # write last value one more time for mrtg to be happy
        log_array.append("%s %d %d\n" % (now_timestamp, substance_value, substance_value))

        # now reverse and write the array to the logfile
        log_array.reverse()
        mrtg_logfile = "%s/%s/%s/%s-%d_%s.log" % (STATS_DIR,sensor_country,city_dir,city_dir,sensor_local_id,substance)
        f = file(mrtg_logfile, 'w')
        for logline in log_array:
            f.write(logline)
        f.close()

    print " ..done !"
