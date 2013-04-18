#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import math
from HTMLParser import HTMLParser
import urllib2
import os
import pickle

def getSizeForDiagonal(widthRes, heightRes, diagSize):
    diagRes = math.sqrt(widthRes ** 2 + heightRes ** 2)
    sin = widthRes / diagRes
    cos = heightRes / diagRes
    widthSize = sin * diagSize
    heightSize = cos * diagSize
    return widthSize, heightSize

class DeviceInfoRetriever(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.waitingForSize = False
        self.waitingForResolution = False
        self.waitingForRealSize = False
        self.widthSize = None
        self.heightSize = None
        self.diagSize = None
        self.resolutionWidth = None
        self.resolutionHeight = None
        self.infos = {}

    def parseUrl(self, url):
        url = "http://www.android.com" + url
        req = urllib2.urlopen(url)

        for data in req:
            self.feed(data)
            if self.resolutionWidth is not None:
                break

        width, height = getSizeForDiagonal(self.resolutionWidth, self.resolutionHeight, self.diagSize)

        if width > height: #  reverse width and heigth
            proxy = height
            height = width
            width = proxy

        if self.widthSize > self.heightSize: #  reverse width and heigth
            proxy = self.heightSize
            self.heightSize = self.widthSize
            self.widthSize = proxy
            
        self.infos["total_width"] = self.widthSize
        self.infos["total_height"] = self.heightSize
        self.infos["screen_width"] = width
        self.infos["screen_height"] = height

        return self.infos

    def handle_starttag(self, tag, attrs):
        pass

    def handle_data(self, data):
        data = filter(lambda x: x not in [' ', '\n', '\r', ')'], data)

        if data and self.waitingForResolution:
            data = data.split('(')[1]
            data = data.split('x')
            self.resolutionHeight = float(data[0])
            self.resolutionWidth = float(data[1])
            self.waitingForResolution = False
        elif data and self.waitingForSize:
            self.diagSize = float(data.split('(')[0])
            if "inches" in data.split('(')[1]:
                self.diagSize *= 25.4
            self.waitingForSize = False
        elif data and self.waitingForRealSize:
            if self.widthSize == None:
                self.widthSize = float(data.split("mm")[0])
            elif self.heightSize == None:
                self.heightSize = float(data.split("mm")[0])
                self.waitingForRealSize = False

        elif "Dimensions" in data:
            self.waitingForRealSize = True
        elif "Screensize" in data:
            self.waitingForSize = True
        elif "Screenresolution" in data:
            self.waitingForResolution = True

class LinkRetriever(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.listBegun = False
        self.ulBegun = False
        self.deviceInfoRetriever = DeviceInfoRetriever()
        self.devices = {}
        self.nbrSuccesses = 0
        self.nbrDevices = 0

    def handle_starttag(self, tag, attrs):
        
        if attrs and attrs[0] and tag == 'div' and 'listing' in attrs[0][1]:
            self.listBegun = True
        if self.listBegun and tag == 'ul':
            self.ulBegun = True
        if self.ulBegun and tag == 'a':
            try:
                link = attrs[0][1]
                if link[0:15] == "/devices/detail":
                    self.deviceInfoRetriever.__init__()
                    print link
                    self.nbrDevices += 1
                    try:
                        infos = self.deviceInfoRetriever.parseUrl(link)
                        name = link.split('/')[-1]
                        self.devices[name] = infos
                        self.nbrSuccesses += 1
                        print name, "has been succesfully identified"
                    except Exception as e:
                        print link, " is missing a resolution"
            except IndexError:
                pass

    def handle_endtag(self, tag):
        if self.ulBegun and tag == 'ul':
            self.listBegun = False

if __name__=="__main__":
    f = open("index.html")
    linkRetriever = LinkRetriever()
    if os.path.exists("./database.pickle"):
        print "Database already created, loading it"
        devices = pickle.load(open("./database.pickle", 'rb'))
    else:
        print "No database found, creating it now"
        for data in f:
            linkRetriever.feed(unicode(data, errors='replace'))
        devices = linkRetriever.devices
        pickle.dump(devices, open("./database.pickle", 'wb'))
        print "Done creating database !"
        print "we recognized", linkRetriever.nbrSuccesses, "on", linkRetriever.nbrDevices, "devices"

    while (1):
        command = raw_input('Ask for a device name or for a list with the "list" command\r\n')
        if command[:4] == "list":
            for device in devices:
                print device
        else:
            try:
                print devices[command]
            except KeyError:
                print "No such device"
