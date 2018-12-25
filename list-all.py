#!/usr/bin/env python
# # -*- coding: utf-8 -*-

""" Smogdance

    An open-source collection of scripts to collect, store and graph air quality data
    from publicly available sources.

    This is so far a pretty primitive script that outputs a simple HTML list of all
    collected sensors and their current ait quality readings trying to color code
    the amounts of substances detected according to the EC's air quality standards.

    gnd, 2017 - 2018
"""

import os
import sys
import MySQLdb
import ConfigParser

### load config
settings_file = os.path.join(sys.path[0], 'settings_python')
config = ConfigParser.ConfigParser()
config.readfp(open(settings_file))
STATS_URL = config.get('globals', 'STATS_URL')

thresholds = {}
so2_thresholds = [0, 125, 350, 500, 800]			# http://ec.europa.eu/environment/air/quality/standards.htm
o3_thresholds = [0, 50, 100, 150, 200, 300]         # saved in smogdance local
pm10_thresholds = [0, 55, 155, 255, 355]            # ??
pm25_thresholds = [0, 15, 40, 65, 150]              # ??
co_thresholds = [0, 10000, 20000, 30000, 40000]		# http://ec.europa.eu/environment/air/quality/standards.htm
no2_thresholds = [0, 100, 150, 200, 300]			# http://ec.europa.eu/environment/air/quality/standards.htm
thresholds['so2'] = so2_thresholds
thresholds['o3'] = o3_thresholds
thresholds['pm10'] = pm10_thresholds
thresholds['pm25'] = pm25_thresholds
thresholds['co'] = co_thresholds
thresholds['no2'] = no2_thresholds


### connect to the db
DB_HOST = config.get('database', 'DB_HOST')
DB_USER = config.get('database', 'DB_USER')
DB_PASS = config.get('database', 'DB_PASS')
DB_NAME = config.get('database', 'DB_NAME')
DB_TABLE = config.get('database', 'DB_TABLE')
DATA_TABLE = config.get('database', 'DATA_TABLE')
db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
cur = db.cursor()

#####
##### List all sensors (this might get very big very soon)
#####

countries = []
query = "SELECT DISTINCT country FROM %s ORDER BY country" % (DB_TABLE)
cur.execute(query)
for country in cur.fetchall():
    sensor_ids = 0
    cities = 0
    countries.append(country[0])
    query = "SELECT DISTINCT city FROM %s WHERE country = '%s' AND city not like '' ORDER by city" % (DB_TABLE, country[0])
    cur.execute(query)
    for res in cur.fetchall():
        cities += 1
        city = res[0]
        query = "SELECT DISTINCT id from %s WHERE city = '%s' order by id" % (DB_TABLE, city)
        cur.execute(query)
        for id in cur.fetchall():
            sensor_ids += 1
    print "<a href=\"#%s\">%s</a> (%d cities, %d sensors) " % (country[0], country[0].upper(), cities, sensor_ids)
print "<br/><br/>"


for country in countries:
    print "<a name=\"%s\"></a>" % (country)
    print "<a href=https://%s/%s>%s</a><br/>" % (STATS_URL, country, country.upper())
    print "<table>"
    print "<tr><td width=\"140\">&nbsp;</td><td width=\"35\">co</td><td width=\"20\">no2</td><td width=\"20\">o3</td><td width=\"20\">pm10</td><td width=\"20\">pm25</td><td width=\"20\">so2</td><tr>\n"
    query = "SELECT DISTINCT city, link_stat FROM %s WHERE country = '%s' AND city not like '' ORDER by city" % (DB_TABLE, country)
    cur.execute(query)
    #//TODO - rewrite this with poll-city instead
    for res in cur.fetchall():
        city = res[0]
        link = res[1]
        query = "SELECT DISTINCT id from %s WHERE city = '%s' order by id" % (DB_TABLE, city)
        cur.execute(query)
        city_co = 0
        city_no2 = 0
        city_o3 = 0
        city_pm10 = 0
        city_pm25 = 0
        city_so2 = 0
        sensors_co = 0
        sensors_no2 = 0
        sensors_o3 = 0
        sensors_pm10 = 0
        sensors_pm25 = 0
        sensors_so2 = 0
        for id in cur.fetchall():
            id = id[0]
            query = "SELECT * from %s_temp WHERE sensor_id = %s" % (DATA_TABLE, id)
            cur.execute(query)
            co = 0
            no2 = 0
            o3 = 0
            pm10 = 0
            pm25 = 0
            so2 = 0
            for res in cur.fetchall():
                if res[2] != None and res[2] > 0:
                    co = float(res[2])
                    sensors_co += 1
                if res[3] != None and res[3] > 0:
                    no2 = float(res[3])
                    sensors_no2 += 1
                if res[4] != None and res[4] > 0:
                    o3 = float(res[4])
                    sensors_o3 += 1
                if res[5] != None and res[5] > 0:
                    pm10 = float(res[5])
                    sensors_pm10 += 1
                if res[6] != None and res[6] > 0:
                    pm25 = float(res[6])
                    sensors_pm25 += 1
                if res[7] != None and res[7] > 0:
                    so2 = float(res[7])
                    sensors_so2 += 1
            city_co += co
            city_no2 += no2
            city_o3 += o3
            city_pm10 += pm10
            city_pm25 += pm25
            city_so2 += so2
        if sensors_co > 0 and city_co > 0:
            city_co /= sensors_co
        if sensors_no2 > 0 and city_no2 > 0:
            city_no2 /= sensors_no2
        if sensors_o3 > 0 and city_o3 > 0:
            city_o3 /= sensors_o3
        if sensors_pm10 > 0 and city_pm10 > 0:
            city_pm10 /= sensors_pm10
        if sensors_pm25 > 0 and city_pm25 > 0:
            city_pm25 /= sensors_pm25
        if sensors_so2 > 0 and city_so2 > 0:
            city_so2 /= sensors_so2
        # levels
        so2_level = 0
        for threshold in thresholds['so2']:
            if city_so2 > threshold:
                so2_level += 1
        no2_level = 0
        for threshold in thresholds['no2']:
            if city_no2 > threshold:
                no2_level += 1
        o3_level = 0
        for threshold in thresholds['o3']:
            if city_o3 > threshold:
                o3_level += 1
        pm10_level = 0
        for threshold in thresholds['pm10']:
            if city_pm10 > threshold:
                pm10_level += 1
        pm25_level = 0
        for threshold in thresholds['pm25']:
            if city_pm25 > threshold:
                pm25_level += 1
        co_level = 0
        for threshold in thresholds['co']:
            if city_co > threshold:
                co_level += 1
        pm10_col = "#dddddd"
        pm25_col = "#dddddd"
        so2_col = "#dddddd"
        o3_col = "#dddddd"
        no2_col = "#dddddd"
        co_col = "#dddddd"
        if so2_level > 0:
            so2_col = "#9eec80"
        if so2_level > 1:
            so2_col = "#ffff00"
        if so2_level > 2:
            so2_col = "#ffa500"
        if so2_level > 3:
            so2_col = "#ff0000"
        if so2_level > 4:
            so2_col = "#e50883"
        if no2_level > 0:
            no2_col = "#9eec80"
        if no2_level > 1:
            no2_col = "#ffff00"
        if no2_level > 2:
            no2_col = "#ffa500"
        if no2_level > 3:
            no2_col = "#ff0000"
        if no2_level > 4:
            no2_col = "#e50883"
        if o3_level > 0:
            o3_col = "#9eec80"
        if o3_level > 1:
            o3_col = "#ffff00"
        if o3_level > 2:
            o3_col = "#ffa500"
        if o3_level > 3:
            o3_col = "#ff0000"
        if o3_level > 4:
            o3_col = "#e50883"
        if pm10_level > 0:
            pm10_col = "#9eec80"
        if pm10_level > 1:
            pm10_col = "#ffff00"
        if pm10_level > 2:
            pm10_col = "#ffa500"
        if pm10_level > 3:
            pm10_col = "#ff0000"
        if pm10_level > 4:
            pm10_col = "#e50883"
        if pm25_level > 0:
            pm25_col = "#9eec80"
        if pm25_level > 1:
            pm25_col = "#ffff00"
        if pm25_level > 2:
            pm25_col = "#ffa500"
        if pm25_level > 3:
            pm25_col = "#ff0000"
        if pm25_level > 4:
            pm25_col = "#e50883"
        if co_level > 0:
            co_col = "#9eec80"
        if co_level > 1:
            co_col = "#ffff00"
        if co_level > 2:
            co_col = "#ffa500"
        if co_level > 3:
            co_col = "#ff0000"
        if co_level > 4:
            co_col = "#e50883"
        print "<tr>\n"
        print "<td width=\"140\"><a href=%s>%s</a></td>\n" % (link, city.capitalize())
        print "<td width=\"35\" style=\"background-color: %s;\">%02d</td>\n" % (co_col, float(city_co))
        print "<td width=\"20\" style=\"background-color: %s;\">%02d</td>\n" % (no2_col, float(city_no2))
        print "<td width=\"20\" style=\"background-color: %s;\">%02d</td>\n" % (o3_col, float(city_o3))
        print "<td width=\"20\" style=\"background-color: %s;\">%02d</td>\n" % (pm10_col, float(city_pm10))
        print "<td width=\"20\" style=\"background-color: %s;\">%02d</td>\n" % (pm25_col, float(city_pm25))
        print "<td width=\"20\" style=\"background-color: %s;\">%02d</td>\n" % (so2_col, float(city_so2))
        print "<td width=\"20\" style=\"background-color: %s;\"><a href=chart.php?city=%s>more</a></td>\n" % ("white", city)
        print "</tr>\n"
    print "</table></br><br/>"
