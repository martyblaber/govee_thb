#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 29 21:26:50 2021

@author: Marty Blaber
"""

# Module Imports
import mariadb
import pathlib as pl
import json

class GoveeDB(object):
    def __init__(self, gid):
        try:
            # Connect to MariaDB Platform

            conn = mariadb.connect(
                user = gid['username'],
                password = gid['password'],
                host = gid['host'],
                port = gid['port'],
                database = gid['database']
            )
            cursor = conn.cursor()
            self.conn = conn
            self.cursor = cursor
            
        except mariadb.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")
            raise
            
    def add_row(self, tablename, rowdict):
        keys = rowdict.keys()
    
        columns = ", ".join(keys)
        values_template = ", ".join(["%s"] * len(keys))
    
        sql = "insert into %s (%s) values (%s)" % (
            tablename, columns, values_template)
        values = tuple(rowdict[key] for key in keys)
        
        try:
            self.cursor.execute(sql, values)
            self.conn.commit()
        except mariadb.Error as e: 
            print(f"Error: {e}")
            print("Tablename", tablename)
            print("rowdict", rowdict)
            print("sql---------")
            print(sql)
            print("values-------")
            print(values)
            print("---------")
            raise
        
        
def load_db_settings(settings_path=None):
    try:
        with open(settings_path) as f:
            gi = json.load(f)
        gid = gi['database']
        
    except FileNotFoundError as e:
        print(f"Error loading file {settings_path}: {e}")
        raise
        
    except KeyError as e:
        print(f"Error reading key 'database': {e}")
        print("Contents of JSON Follows")
        print(settings_path)
        print("----------")
        print(gi)
        print("----------")
        raise
        
    return gid 
    
def self_test():
    print("Running self test")
    settings_path = pl.Path.home() / pl.Path("govee_info.json")
    
    gid = load_db_settings(settings_path)
    
    gdb = GoveeDB(gid)
    
    return gdb


# Get Cursor
if __name__ == "__main__":
    gb = self_test()
    
    sql = 'insert into trogadog.govee_thb (mac_address, n_measurements, average_date, temperature, humidity, battery) values (%s, %s, %s, %s, %s, %s)'
    values = (181149778475935, 30, '2021-06-27 19:09:03', 23.45134333333333, 51.34333333333333, 100.0)
    
    
    
