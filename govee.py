#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun 27 14:04:16 2021

@author: Marty Blaber


"""

# Module Imports
#import mariadb
import sys
import pathlib as pl
import govee_db
import govee_processor as gp

#Connect to the database:
settings_path = pl.Path.home() / pl.Path("govee_info.json")

db_settings = govee_db.load_db_settings(settings_path)

gdb = govee_db.GoveeDB(db_settings)


debug = True
if debug:
    f = open("tmp.txt", "r")
    input_lines = f.readline
else:
    input_lines = sys.stdin.readline

devices = {}

for line in iter(input_lines, ""):
    try:
        odict = gp.decode_govee(line)
        if odict is None:
            continue
    except:
        raise
    
    if odict['MAC_INT'] not in devices.keys():
        devices[odict['MAC_INT']] = gp.Govee_Device(odict, n_measurements_to_average = 30)
    else:
        devices[odict['MAC_INT']].add_row(odict)
        ave =  devices[odict['MAC_INT']].get_averages(for_db=True)
        if ave is not None:
            print(ave)
 
 
 
 
 
 
 
 

                      