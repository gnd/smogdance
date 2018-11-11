#!/usr/bin/env python
# # -*- coding: utf-8 -*-

""" Smogdance

    An open-source collection of scripts to collect, store and graph air quality data
    from publicly available sources.

    This rewrites CZ CHMI definitions to the new format where sensor's unique name is used for crawling
    rather than its position in the table

   gnd, 2018
"""

f = file('../definitions/cz-chmi','r')
lines = f.readlines()
f.close()
newlines = []
for line in lines:
    uid = line.split("' '")[2].split("mp_")[1].split("_CZ")[0]
    subs = line.split("' '")[4].split(";")
    xpath = ""
    for sub in subs:
        subname = sub.split("--")[0]
        subrow = sub.split("--")[1].split("td[")[1].split("]")[0]
        newpath = "%s--%s:%s--%s" % (subname, uid, subrow, "cz_chmi")
        xpath = xpath + ";" + newpath
    arr = line.split("' '")
    arr[4] = xpath[1:]
    newlines.append("' '".join(arr))
f = file('../definitions/cz-chmi-fixed','w')
for line in newlines:
    f.write(line)
f.close()
