#!/usr/bin/env python
# # -*- coding: utf-8 -*-

""" Smogdance

    An open-source collection of scripts to collect, store and graph air quality data
    from publicly available sources.

    This adds sensors according to their definitions into the database.

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
SCRAPY_BIN = config.get('globals', 'SCRAPY_BIN')
DATA_DIR = config.get('globals', 'DATA_DIR')
TEMP_DIR = config.get('globals', 'TEMP_DIR')
SPIDER_DIR = config.get('globals', 'SPIDER_DIR')

### connect to the db
DB_HOST = config.get('database', 'DB_HOST')
DB_USER = config.get('database', 'DB_USER')
DB_PASS = config.get('database', 'DB_PASS')
DB_NAME = config.get('database', 'DB_NAME')
DB_TABLE = config.get('database', 'DB_TABLE')
DATA_TABLE = config.get('database', 'DATA_TABLE')
db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
cur = db.cursor()

### process input
if (len(sys.argv) > 1):
    task = sys.argv[1]
else:
    sys.exit("Usage: ./add-definitions.py <custom file> <normal | special> [at | cz | hu | pl | sk]")


### import custom sensors
if (task == 'custom'):
    if (len(sys.argv) > 2):
        custom = sys.argv[2]
        f = file(custom, 'r')
        definitions = f.readlines()
        f.close()
        print "Importing definitions from %s" % (custom)
        for line in definitions:
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
    else:
        sys.exit("Usage: ./add-definitions.py <custom file> <normal | special> [at | cz | hu | pl | sk]")

### import normal sensors
elif (task == 'normal'):
    if (len(sys.argv) > 2):
        country = sys.argv[2]
        files = [f for f in os.listdir(DATA_DIR+"/definitions") if os.path.isfile(os.path.join(DATA_DIR+"/definitions", f))]
        for def_file in files:
            if (def_file.split("-")[0] == country):
                f = file(DATA_DIR+"/definitions/"+def_file, 'r')
                definitions = f.readlines()
                f.close()
                print "Importing definitions from %s" % (def_file)
                for line in definitions:
                    line = line.replace('TEMP_DIR', TEMP_DIR)
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

    else:
        files = [f for f in os.listdir(DATA_DIR+"/definitions") if os.path.isfile(os.path.join(DATA_DIR+"/definitions", f))]
        for def_file in files:
            if (def_file != "special"):
                f = file(DATA_DIR+"/definitions/"+def_file, 'r')
                definitions = f.readlines()
                f.close()
                print "Importing definitions from %s" % (def_file)
                for line in definitions:
                    line = line.replace('TEMP_DIR', TEMP_DIR)
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


### import special sensors
elif (task == 'special'):
    if (len(sys.argv) > 2):
        country = sys.argv[2]
        f = file(DATA_DIR+"/definitions/special", 'r')
        definitions = f.readlines()
        f.close()
        print "Importing definitions from special"
        for line in definitions:

            if (line.split(' ')[4] == country):
                import_cmd = "%s/add-special-sensor.py %s" % (DATA_DIR, line)
                import_args = shlex.split(import_cmd)

                ### run the import
                try:
                    print "Trying to run %s/add-special-sensor.py %s" % (DATA_DIR, line)
                    process = subprocess.Popen(import_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    out = process.communicate()[1]
                    if (process.returncode != 0):
                        print "Import failed:\n%s" % (out)
                except:
                    print "Couldnt run %s/add-sensor.py %s" % (DATA_DIR, line)

    else:
        f = file(DATA_DIR+"/definitions/special", 'r')
        definitions = f.readlines()
        f.close()
        print "Importing definitions from special"
        for line in definitions:
            import_cmd = "%s/add-special-sensor.py %s" % (DATA_DIR, line)
            import_args = shlex.split(import_cmd)

            ### run the import
            try:
                print "Trying to run %s/add-special-sensor.py %s" % (DATA_DIR, line)
                process = subprocess.Popen(import_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out = process.communicate()[1]
                if (process.returncode != 0):
                    print "Import failed:\n%s" % (out)
            except:
                print "Couldnt run %s/add-sensor.py %s" % (DATA_DIR, line)

### just show the usage
else:
    sys.exit("Usage: ./add-definitions.py <custom file> <normal | special> [at | cz | hu | pl | sk]")
