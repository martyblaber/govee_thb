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

print("Reading Settings File")
db_settings = govee_db.load_db_settings(settings_path)
tablename = db_settings['database'] + "." + db_settings['table']
print("We're going to use %s"%tablename)

print("Opening DB Connection")
gdb = govee_db.GoveeDB(db_settings)

debug = False
if debug:
    f = open("tmp.txt", "r")
    input_lines = f.readline
else:
    print("Opening Input Stream")
    input_lines = sys.stdin.readline

devices = {}
print_header = True

for line in iter(input_lines, ""):
    try:
        odict = gp.decode_govee(line)
        if odict is None:
            continue
    except:
        raise
    
    if odict['MAC_INT'] not in devices.keys():
        devices[odict['MAC_INT']] = gp.Govee_Device(odict, n_measurements_to_average = 30)
        if print_header:
            devices[odict['MAC_INT']].print_header()
            print_header = False
        continue

    this_device = devices[odict['MAC_INT']]
    this_device.add_row(odict)
    if this_device.ready():
        this_device.print_averages()
        
        rowdict = this_device.get_averages()
        
        gdb.add_row(tablename, rowdict)
        
        
            
            

 
 
 
 
 
 

                      
