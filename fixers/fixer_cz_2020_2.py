#!/usr/bin/env python
# # -*- coding: utf-8 -*-

""" Smogdance

    An open-source collection of scripts to collect, store and graph air quality data
    from publicly available sources.

    This does some fixing of SK spiders (March, 2020)

    gnd, 2020
"""

import os
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import shlex
import MySQLdb
import subprocess
import ConfigParser

### Import smog functions
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from smog_functions import *

### load config
settings_file = os.path.join(sys.path[0], '../settings_python')
config = ConfigParser.ConfigParser()
config.readfp(open(settings_file))
DATA_DIR = config.get('globals', 'DATA_DIR')
TEMP_DIR = config.get('globals', 'TEMP_DIR')
STATS_DIR = config.get('globals', 'STATS_DIR')
SPIDER_DIR = config.get('globals', 'SPIDER_DIR')
MRTG_TEMPLATE = config.get('globals', 'MRTG_TEMPLATE')
SPIDER_TEMPLATE = config.get('globals', 'SPIDER_TEMPLATE')
SPIDER_COMMAND = config.get('globals', 'SPIDER_COMMAND')

all_substances = ["co","no2","o3","pm10","pm25","so2"]

### connect to the db
DB_HOST = config.get('database', 'DB_HOST')
DB_USER = config.get('database', 'DB_USER')
DB_PASS = config.get('database', 'DB_PASS')
DB_NAME = config.get('database', 'DB_NAME')
DB_TABLE = config.get('database', 'DB_TABLE')
DATA_TABLE = config.get('database', 'DATA_TABLE')
db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
cur = db.cursor()

################ Begin new substances ###################

# 0. add no2 to vrsovice
params = "7 no2:6"
run_cmd = "%s/add-substance-to-sensor.py %s" % (DATA_DIR, params)
run_args = shlex.split(run_cmd)
### run the change
try:
    print "Trying to run %s/add-substance-to-sensor.py %s" % (DATA_DIR, params)
    process = subprocess.Popen(run_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/add-substance-to-sensor.py %s" % (DATA_DIR, params)

# 1. add no2 to suchdol
params = "12 no2:6"
run_cmd = "%s/add-substance-to-sensor.py %s" % (DATA_DIR, params)
run_args = shlex.split(run_cmd)
### run the change
try:
    print "Trying to run %s/add-substance-to-sensor.py %s" % (DATA_DIR, params)
    process = subprocess.Popen(run_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/add-substance-to-sensor.py %s" % (DATA_DIR, params)

# 2. add co to letiste
params = "490 co:7"
run_cmd = "%s/add-substance-to-sensor.py %s" % (DATA_DIR, params)
run_args = shlex.split(run_cmd)
### run the change
try:
    print "Trying to run %s/add-substance-to-sensor.py %s" % (DATA_DIR, params)
    process = subprocess.Popen(run_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/add-substance-to-sensor.py %s" % (DATA_DIR, params)

# 3. add o3 to letiste
params = "490 o3:9"
run_cmd = "%s/add-substance-to-sensor.py %s" % (DATA_DIR, params)
run_args = shlex.split(run_cmd)
### run the change
try:
    print "Trying to run %s/add-substance-to-sensor.py %s" % (DATA_DIR, params)
    process = subprocess.Popen(run_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/add-substance-to-sensor.py %s" % (DATA_DIR, params)

# 4. add so2 to primda
params = "38 so2:5"
run_cmd = "%s/add-substance-to-sensor.py %s" % (DATA_DIR, params)
run_args = shlex.split(run_cmd)
### run the change
try:
    print "Trying to run %s/add-substance-to-sensor.py %s" % (DATA_DIR, params)
    process = subprocess.Popen(run_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/add-substance-to-sensor.py %s" % (DATA_DIR, params)

# 5. add no2 to primda
params = "38 no2:6"
run_cmd = "%s/add-substance-to-sensor.py %s" % (DATA_DIR, params)
run_args = shlex.split(run_cmd)
### run the change
try:
    print "Trying to run %s/add-substance-to-sensor.py %s" % (DATA_DIR, params)
    process = subprocess.Popen(run_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/add-substance-to-sensor.py %s" % (DATA_DIR, params)

# 6. add so2 to polom
params = "64 so2:5"
run_cmd = "%s/add-substance-to-sensor.py %s" % (DATA_DIR, params)
run_args = shlex.split(run_cmd)
### run the change
try:
    print "Trying to run %s/add-substance-to-sensor.py %s" % (DATA_DIR, params)
    process = subprocess.Popen(run_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/add-substance-to-sensor.py %s" % (DATA_DIR, params)

# 7. add pm25 to brno vystaviste
params = "81 pm25:11"
run_cmd = "%s/add-substance-to-sensor.py %s" % (DATA_DIR, params)
run_args = shlex.split(run_cmd)
### run the change
try:
    print "Trying to run %s/add-substance-to-sensor.py %s" % (DATA_DIR, params)
    process = subprocess.Popen(run_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/add-substance-to-sensor.py %s" % (DATA_DIR, params)

# 7.1 add o3 to brno arboretum
params = "78 o3:9"
run_cmd = "%s/add-substance-to-sensor.py %s" % (DATA_DIR, params)
run_args = shlex.split(run_cmd)
### run the change
try:
    print "Trying to run %s/add-substance-to-sensor.py %s" % (DATA_DIR, params)
    process = subprocess.Popen(run_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/add-substance-to-sensor.py %s" % (DATA_DIR, params)

# 7.2 add pm25 to brno arboretum
params = "78 pm25:11"
run_cmd = "%s/add-substance-to-sensor.py %s" % (DATA_DIR, params)
run_args = shlex.split(run_cmd)
### run the change
try:
    print "Trying to run %s/add-substance-to-sensor.py %s" % (DATA_DIR, params)
    process = subprocess.Popen(run_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/add-substance-to-sensor.py %s" % (DATA_DIR, params)

# 8. add pm25 to poruba dd
params = "117 pm25:11"
run_cmd = "%s/add-substance-to-sensor.py %s" % (DATA_DIR, params)
run_args = shlex.split(run_cmd)
### run the change
try:
    print "Trying to run %s/add-substance-to-sensor.py %s" % (DATA_DIR, params)
    process = subprocess.Popen(run_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/add-substance-to-sensor.py %s" % (DATA_DIR, params)

# 9. add pm10 to poruba chmu
params = "118 pm10:8"
run_cmd = "%s/add-substance-to-sensor.py %s" % (DATA_DIR, params)
run_args = shlex.split(run_cmd)
### run the change
try:
    print "Trying to run %s/add-substance-to-sensor.py %s" % (DATA_DIR, params)
    process = subprocess.Popen(run_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/add-substance-to-sensor.py %s" % (DATA_DIR, params)

# 10. add co to studenka
params = "126 co:7"
run_cmd = "%s/add-substance-to-sensor.py %s" % (DATA_DIR, params)
run_args = shlex.split(run_cmd)
### run the change
try:
    print "Trying to run %s/add-substance-to-sensor.py %s" % (DATA_DIR, params)
    process = subprocess.Popen(run_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/add-substance-to-sensor.py %s" % (DATA_DIR, params)

# 11. add pm25 to kanada
params = "127 pm25:11"
run_cmd = "%s/add-substance-to-sensor.py %s" % (DATA_DIR, params)
run_args = shlex.split(run_cmd)
### run the change
try:
    print "Trying to run %s/add-substance-to-sensor.py %s" % (DATA_DIR, params)
    process = subprocess.Popen(run_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/add-substance-to-sensor.py %s" % (DATA_DIR, params)

################ End of new substances ###################

################ Begin remove substances ###################

# 0. rem pm25 from churanov
params = "25 pm25"
run_cmd = "%s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)
run_args = shlex.split(run_cmd)
### run the change
try:
    print "Trying to run %s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)
    process = subprocess.Popen(run_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)

# 1. rem so2 from prachatice
params = "28 so2"
run_cmd = "%s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)
run_args = shlex.split(run_cmd)
### run the change
try:
    print "Trying to run %s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)
    process = subprocess.Popen(run_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)

# 2. rem co from prachatice
params = "28 co"
run_cmd = "%s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)
run_args = shlex.split(run_cmd)
### run the change
try:
    print "Trying to run %s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)
    process = subprocess.Popen(run_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)

# 3. rem co from plzen stred
params = "33 co"
run_cmd = "%s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)
run_args = shlex.split(run_cmd)
### run the change
try:
    print "Trying to run %s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)
    process = subprocess.Popen(run_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)

# 4. rem o3 from ustnl mesto
params = "56 o3"
run_cmd = "%s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)
run_args = shlex.split(run_cmd)
### run the change
try:
    print "Trying to run %s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)
    process = subprocess.Popen(run_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)

# 5. rem so2 from ustnl mesto
params = "56 so2"
run_cmd = "%s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)
run_args = shlex.split(run_cmd)
### run the change
try:
    print "Trying to run %s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)
    process = subprocess.Popen(run_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)

# 6. rem o3 from brno zvonarka
params = "82 o3"
run_cmd = "%s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)
run_args = shlex.split(run_cmd)
### run the change
try:
    print "Trying to run %s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)
    process = subprocess.Popen(run_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)

# 7. rem no2 from brno masna
params = "83 no2"
run_cmd = "%s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)
run_args = shlex.split(run_cmd)
### run the change
try:
    print "Trying to run %s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)
    process = subprocess.Popen(run_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)

# 8. rem pm10 from kucharovice
params = "88 pm10"
run_cmd = "%s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)
run_args = shlex.split(run_cmd)
### run the change
try:
    print "Trying to run %s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)
    process = subprocess.Popen(run_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)

# 9. rem pm25 from kucharovice
params = "88 pm25"
run_cmd = "%s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)
run_args = shlex.split(run_cmd)
### run the change
try:
    print "Trying to run %s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)
    process = subprocess.Popen(run_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)

# 10. rem so2 from sivice
params = "90 so2"
run_cmd = "%s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)
run_args = shlex.split(run_cmd)
### run the change
try:
    print "Trying to run %s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)
    process = subprocess.Popen(run_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)

# 11. rem co from otrokovice mesto
params = "99 co"
run_cmd = "%s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)
run_args = shlex.split(run_cmd)
### run the change
try:
    print "Trying to run %s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)
    process = subprocess.Popen(run_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)

# 12. rem co from ostrava privoz
params = "119 co"
run_cmd = "%s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)
run_args = shlex.split(run_cmd)
### run the change
try:
    print "Trying to run %s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)
    process = subprocess.Popen(run_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/remove-substance-from-sensor.py %s" % (DATA_DIR, params)

################ End of remove substances ###################

################ Begin add new sensors ###################
# 0. Insert new sensor
line = "'Pelhrimov' 'file://127.0.0.1TEMP_DIR/chmi.html' 'http://portal.chmi.cz/files/portal/docs/uoco/web_generator/aqindex_slide2/mp_JPEMA_CZ.html' 'https://STATS_URL/cz/pelhrimov' 'pm10--JPEMA:8--cz_chmi;pm25--JPEMA:11--cz_chmi' 'cz' 'pelhrimov' '49° 26´ 6.005\" 15° 12´ 29.999\"' 'hourly' 'pm10 pm25'"
import_cmd = "%s/add-sensor.py %s" % (DATA_DIR, line)
import_args = shlex.split(import_cmd)
### run the import
try:
    print "Trying to run %s/add-sensor.py %s" % (DATA_DIR, line)
    process = subprocess.Popen(import_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/add-sensor.py %s" % (DATA_DIR, line)

# 1. Insert new sensor
line = "'Hranice' 'file://127.0.0.1TEMP_DIR/chmi.html' 'http://portal.chmi.cz/files/portal/docs/uoco/web_generator/aqindex_slide2/mp_MPHRA_CZ.html' 'https://STATS_URL/cz/hranice' 'no2--MPHRA:6--cz_chmi;o3--MPHRA:9--cz_chmi;pm10--MPHRA:8--cz_chmi;pm25--MPHRA:11--cz_chmi' 'cz' 'hranice' '49° 33´ 6.795\" 17° 43´ 52.400\"' 'hourly' 'no2 o3 pm10 pm25'"
import_cmd = "%s/add-sensor.py %s" % (DATA_DIR, line)
import_args = shlex.split(import_cmd)
### run the import
try:
    print "Trying to run %s/add-sensor.py %s" % (DATA_DIR, line)
    process = subprocess.Popen(import_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/add-sensor.py %s" % (DATA_DIR, line)

# 2. Insert new sensor
line = "'Chotebuz' 'file://127.0.0.1TEMP_DIR/chmi.html' 'http://portal.chmi.cz/files/portal/docs/uoco/web_generator/aqindex_slide3/mp_TCHOA_CZ.html' 'https://STATS_URL/cz/chotebuz' 'so2--TCHOA:5--cz_chmi;no2--TCHOA:6--cz_chmi;co--TCHOA:7--cz_chmi;pm10--TCHOA:8--cz_chmi' 'cz' 'chotebuz' '49° 46´ 40.827\" 18° 35´ 59.219\"' 'hourly' 'so2 no2 co pm10'"
import_cmd = "%s/add-sensor.py %s" % (DATA_DIR, line)
import_args = shlex.split(import_cmd)
### run the import
try:
    print "Trying to run %s/add-sensor.py %s" % (DATA_DIR, line)
    process = subprocess.Popen(import_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/add-sensor.py %s" % (DATA_DIR, line)

# 3. Insert new sensor
line = "'Hostalkovice' 'file://127.0.0.1TEMP_DIR/chmi.html' 'http://portal.chmi.cz/files/portal/docs/uoco/web_generator/aqindex_slide3/mp_TOHOA_CZ.html' 'https://STATS_URL/cz/ostrava' 'so2--TOHOA:5--cz_chmi;no2--TOHOA:6--cz_chmi;co--TOHOA:7--cz_chmi;pm10--TOHOA:8--cz_chmi' 'cz' 'ostrava' '49° 51´ 41.015\" 18° 12´ 48.047\"' 'hourly' 'so2 no2 co pm10'"
import_cmd = "%s/add-sensor.py %s" % (DATA_DIR, line)
import_args = shlex.split(import_cmd)
### run the import
try:
    print "Trying to run %s/add-sensor.py %s" % (DATA_DIR, line)
    process = subprocess.Popen(import_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/add-sensor.py %s" % (DATA_DIR, line)

# 4. Insert new sensor
line = "'Hrusov' 'file://127.0.0.1TEMP_DIR/chmi.html' 'http://portal.chmi.cz/files/portal/docs/uoco/web_generator/aqindex_slide3/mp_TOHUA_CZ.html' 'https://STATS_URL/cz/ostrava' 'pm10--TOHUA:8--cz_chmi;pm25--TOHUA:11--cz_chmi' 'cz' 'ostrava' '49° 52´ 3.798\" 18° 17´ 1.502\"' 'hourly' 'pm10 pm25'"
import_cmd = "%s/add-sensor.py %s" % (DATA_DIR, line)
import_args = shlex.split(import_cmd)
### run the import
try:
    print "Trying to run %s/add-sensor.py %s" % (DATA_DIR, line)
    process = subprocess.Popen(import_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/add-sensor.py %s" % (DATA_DIR, line)

# 5. Insert new sensor
line = "'Komarov' 'file://127.0.0.1TEMP_DIR/chmi.html' 'http://portal.chmi.cz/files/portal/docs/uoco/web_generator/aqindex_slide3/mp_TOKOA_CZ.html' 'https://STATS_URL/cz/opava' 'so2--TOKOA:5--cz_chmi;no2--TOKOA:6--cz_chmi;co--TOKOA:7--cz_chmi;pm10--TOKOA:8--cz_chmi' 'cz' 'opava' '49° 54´ 54.965\" 17° 57´ 56.575\"' 'hourly' 'so2 no2 co pm10'"
import_cmd = "%s/add-sensor.py %s" % (DATA_DIR, line)
import_args = shlex.split(import_cmd)
### run the import
try:
    print "Trying to run %s/add-sensor.py %s" % (DATA_DIR, line)
    process = subprocess.Popen(import_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Import failed:\n%s" % (out)
except:
    print "Couldnt run %s/add-sensor.py %s" % (DATA_DIR, line)

################ End of new sensors ###################

################ Begin delete sensors ###################
# 0. Delete Praha - Smichov
id_to_delete = "6"
delete_cmd = "%s/delete-sensor.py %s" % (DATA_DIR, id_to_delete)
delete_args = shlex.split(delete_cmd)
### run the delete
try:
    print "Trying to run %s/delete-sensor.py %s" % (DATA_DIR, id_to_delete)
    process = subprocess.Popen(delete_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Delete failed:\n%s" % (out)
except:
    print "Couldnt run %s/delete-sensor.py %s" % (DATA_DIR, id_to_delete)

# 1. Delete Vratimov
id_to_delete = "499"
delete_cmd = "%s/delete-sensor.py %s" % (DATA_DIR, id_to_delete)
delete_args = shlex.split(delete_cmd)
### run the delete
try:
    print "Trying to run %s/delete-sensor.py %s" % (DATA_DIR, id_to_delete)
    process = subprocess.Popen(delete_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Delete failed:\n%s" % (out)
except:
    print "Couldnt run %s/delete-sensor.py %s" % (DATA_DIR, id_to_delete)

# 2. Delete Ostrava - Hrabova
id_to_delete = "500"
delete_cmd = "%s/delete-sensor.py %s" % (DATA_DIR, id_to_delete)
delete_args = shlex.split(delete_cmd)
### run the delete
try:
    print "Trying to run %s/delete-sensor.py %s" % (DATA_DIR, id_to_delete)
    process = subprocess.Popen(delete_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Delete failed:\n%s" % (out)
except:
    print "Couldnt run %s/delete-sensor.py %s" % (DATA_DIR, id_to_delete)

# 3. Delete Ostrava - Kuncicky
id_to_delete = "501"
delete_cmd = "%s/delete-sensor.py %s" % (DATA_DIR, id_to_delete)
delete_args = shlex.split(delete_cmd)
### run the delete
try:
    print "Trying to run %s/delete-sensor.py %s" % (DATA_DIR, id_to_delete)
    process = subprocess.Popen(delete_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Delete failed:\n%s" % (out)
except:
    print "Couldnt run %s/delete-sensor.py %s" % (DATA_DIR, id_to_delete)
################ End delete sensors ###################

################ Fix sensor name ###################
# 0. Rename Ostrava - Ceskobratrsk to Ceskobratrska
line = "113 Ceskobratrska"
rename_cmd = "%s/rename-sensor.py %s" % (DATA_DIR, line)
import_args = shlex.split(rename_cmd)
### run the rename
try:
    print "Trying to run %s/rename-sensor.py %s" % (DATA_DIR, line)
    process = subprocess.Popen(import_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = process.communicate()[1]
    if (process.returncode != 0):
        print "Delete failed:\n%s" % (out)
except:
    print "Couldnt run %s/rename-sensor.py %s" % (DATA_DIR, line)
