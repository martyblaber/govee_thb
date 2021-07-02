#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun 27 14:04:16 2021

@author: Marty Blaber

"""

# Module Imports
#import mariadb
import sys
import numpy as np

def remove_units(inp):
    temp = inp.replace('°C','')
    temp = temp.replace('%','')    
    return temp

def sanitize_str(inp_str,chars_to_remove="!@#$%^&*()[]{};'\"\\|/,<>?"):
    out_str = inp_str.translate(str.maketrans('','',chars_to_remove))
    return out_str


def dewpoint_from_relative_humidity(T_in_C, RH_in_pct):
    
    #Fractional RH
    RHf = RH_in_pct / 100.0
    
    a = 6.1121 #mbar
    b = 18.678
    c = 257.14 #deg C
    d = 234.5  #deg C.
    
    #saturation_vapor_pressure_in_mBar
    Psm = 6.1121 * np.exp( (b - T_in_C/d) * (T_in_C / (c + T_in_C)) )
    top = c * np.log(RHf * Psm / a)
    bottom = b - np.log(RHf * Psm / a)
    T_dewpoint = top/bottom
    return T_dewpoint

def dict_to_insert(table, input_dict, sanitize_keys=True, sanitize_values=True):
    raise NotImplementedError("Don't use this, it's garbage")
    table = sanitize_str(table)
    keys = input_dict.keys()
    
    print(input_dict)
    
    if sanitize_keys:
        cols = ",".join([sanitize_str(str(key)) for key in keys])
    else:
        cols = ",".join([str(key) for key in keys])
        
    if sanitize_values:
        values = ",".join([sanitize_str(str(input_dict[key])) for key in keys])
    else:
        values = ",".join([str(input_dict[key]) for key in keys])
    
    sql = "INSERT INTO " + table +" (" +cols +\
         ") VALUES (" + values + ");"
    return sql


def mac_str_to_int(mac_str):
    
    mac_int = int(mac_str.translate(str.maketrans('','',":.- ")), 16)
    return mac_int

def mac_int_to_str(mac_int):
    
    mac_hex = "{:012x}".format(mac_int)
    mac_str = ":".join(mac_hex[i:i+2] for i in range(0, len(mac_hex), 2))
    return mac_str


def decode_govee(line):
    if '(Temp)' not in line:
        return None
    
    elem = line.split()
    
    if len(elem) != 17:
        return None
    
    output = {}
    try:
        output['datetime'] = elem[0][1:-1]
        output['MAC_INT'] = mac_str_to_int(elem[2][1:-1])
        output['Name'] = elem[4]
        output['UUID'] = elem[6]
        output['Flags'] = elem[8]
        output['Manufacturer'] = elem[10]
        output['Temperature(C)'] = float(remove_units(elem[12]))
        output['Humidity(%)'] = float(remove_units(elem[14]))
        output['Battery(%)'] = float(remove_units(elem[16]))
        #Calculated Outputs:
        output['Dewpoint(C)'] = dewpoint_from_relative_humidity( 
                                  output['Temperature(C)'],
                                  output['Humidity(%)'])
        
    except:
        raise
        print("Processing Error")
        print(line)
        return None
    
    return output
    

class Govee_Device(object):
    def __init__(self, odict, n_measurements_to_average=10):
        self.n_measurements_to_average = n_measurements_to_average
        
        self.MAC = odict['MAC_INT']
        self.current_index = None
        self.next_index = 0
        self.dates = [None] * n_measurements_to_average
        self.temperatures = [None] * n_measurements_to_average
        self.humidities = [None] * n_measurements_to_average
        self.dewpoints = [None] * n_measurements_to_average
        self.batteries = [None] * n_measurements_to_average
        
        self.add_row(odict)
        
    def add_row(self,odict):
        i = self.next_index
        self.dates[i] = odict['datetime']
        self.temperatures[i] = float(odict['Temperature(C)'])
        self.humidities[i] = float(odict['Humidity(%)'])
        self.dewpoints[i] = float(odict['Dewpoint(C)'])
        self.batteries[i] = float(odict['Battery(%)'])
        self.current_index = i 
        self.next_index = (i + 1) % self.n_measurements_to_average
        if self.ready():
            self.update_averages()
    
    def ready(self):    
        if self.next_index==0:
            return True
        else:
            return False
    def average_datetime(self,dates):

        mean = (np.array(dates, dtype='datetime64[s]')
                .view('i8')
                .mean()
                .astype('datetime64[s]'))
        
        return mean
    
    def average(self,a_list):
        return np.array(a_list).mean()
    
    def update_averages(self):
        self.ave_dict = {}
        self.ave_dict['mac_address'] = self.MAC
        self.ave_dict['n_measurements'] = self.n_measurements_to_average
        self.ave_dict['average_date'] = str(
                self.average_datetime(self.dates)
                ).replace("T", " ")
        self.ave_dict['temperature'] = self.average(self.temperatures)
        self.ave_dict['humidity'] = self.average(self.humidities)
        self.ave_dict['dewpoint'] = self.average(self.dewpoints)
        self.ave_dict['battery'] = self.average(self.batteries)
        
    def get_averages(self,for_db=False):
        if not self.ready():
            return None

        return self.ave_dict
    
    def print_averages(self):
        if not self.ready():
            return None
        
        ad = self.get_averages()
        mac = mac_int_to_str()
        print("%15s%22s%11s%11s%11s%11s\n"%{"MAC ADDRESS", 
                    "Date", "Temp(C)", "RH(%)", "Dew pt.(C)", "Battery(%)"})
        print("%15s%22s%11.2f%11.2f%11.2f%11.2f\n"%{mac,
                    ad['average_date'], ad['temperature'],ad['humidity'],
                    ad['dewpoint'],ad['battery']})
    
if __name__ == "__main__":
    debug = True
    if debug:
        f = open("tmp.txt", "r")
        input_lines = f.readline
    else:
        input_lines = sys.stdin.readline
    
    devices = {}
    
    for line in iter(input_lines, ""):
        try:
            odict = decode_govee(line)
            if odict is None:
                continue
        except:
            raise
        
        if odict['MAC_INT'] not in devices.keys():
            devices[odict['MAC_INT']] = Govee_Device(odict, n_measurements_to_average = 30)
        else:
            this_device = devices[odict['MAC_INT']]
            this_device.add_row(odict)
            if this_device.ready():
                this_device.print_averages()

                
                
 
 
 
 
 
 
 
 

                      