#!/usr/bin/env python
# # -*- coding: utf-8 -*-

""" Smogdance

    An open-source collection of scripts to collect, store and graph air quality data
    from publicly available sources.

    This walks the user through a new sensor creation. This is good for adding
    single sensors, or creating a template that can be copied and edited
    to add dozens of sensors at once.

    gnd, 2017 - 2018
"""

import os
import sys
import pickle
import ConfigParser

### load config
settings_file = os.path.join(sys.path[0], 'settings_python')
config = ConfigParser.ConfigParser()
config.readfp(open(settings_file))
DATA_DIR = config.get('globals', 'DATA_DIR')

name = raw_input("Sensor name:")
link_src = raw_input("Sensor source link:")
link_web = raw_input("Sensor web link:")
link_stat=""
substances=[]
xpaths=[]
modifiers=[]
more = False
while not more:
   tmp_substance = raw_input("Substance: (enter n for no more)")
   if tmp_substance == "n" or tmp_substance =="":
       more = True
   else:
       substances.append(tmp_substance)

sql_substances = ""
for substance in substances:
    xpaths.append(raw_input(substance+" xpath:"))
    modifiers.append(raw_input(substance+" modifier:"))
    sql_substances += substance + " "

tmp = ""
sensor_xpaths = ""
for i in range(len(substances)):
    tmp = ""
    tmp += substances[i] + "--"
    tmp += xpaths[i] + "--"
    tmp += modifiers[i] + ";"
    sensor_xpaths += tmp

sensor_xpaths = sensor_xpaths.strip(";")

country = raw_input("Coutry:")
city = raw_input("City:")
gps = raw_input("GPS:")
gps = gps.replace(" sš","").replace(" vd","")
type = raw_input("Type:")


print "Running add sensor..."
script = "%s/%s" % (DATA_DIR, "add-sensor.py")
command = "%s \'%s\' \'%s\' \'%s\' \'%s\' \'%s\' \'%s\' \'%s\' \'%s\' \'%s\' \'%s\'" % (script, name, link_src, link_web, "", sensor_xpaths, country, city, gps, type, sql_substances.strip())
print command
os.system(command)
