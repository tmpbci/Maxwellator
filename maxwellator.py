 
#!/usr/bin/python3
# -*- coding: utf-8 -*-
# -*- mode: Python -*-

"""

Maxwellator
v0.2.2


LICENCE : CC
by Sam Neurohack 
from /team/laser
to$Maxwell$1
Network$Session$1

Program modes :

startup     : Set all maxwell function with init values from maxwell.json
programall  : Program all Maxwell function with Midi Learn 
program     : Reprogram a Maxwell function you type in with Midi Learn 
list        : List Maxwell functions and CC number
command     : Send a cc : to any particular Maxwell function name you type first, then type value to send
osc         : will only forward osc message (OSC port is 8090) and redis stored artnet to maxwell
live        : Listen to Artnet frame/publish to redis + forward osc message (OSC port is 8090) to maxwell
mitraille   : Read a midifile a generate curve changes according to notes
rand        : Send random value to Maxwell. Think of it as genetic selection. 


"""

#import os
import traceback
import pysimpledmx
from serial.tools import list_ports
import serial,time
#from threading import Thread
import socket
from sys import platform
import redis
import weakref
import sys


sys.path.append('libs/')
import gstt, random
from OSC3 import OSCServer, OSCClient, OSCMessage

print ("")
print ("")
print ("")
print ("Maxwellator v0.2.2")
print ("Loading modules and auto configuring...")

#myHostName = socket.gethostname()
#myHostName = socket.gethostbyaddr(socket.gethostname())[0]
#print("Name of the localhost is {}".format(myHostName))
#myIP = socket.gethostbyname(myHostName)
gstt.myIP = socket.gethostbyname('')


r = redis.StrictRedis(host='127.0.0.1', port=6379, db=0)

from rtmidi.midiconstants import (CHANNEL_PRESSURE, CONTROLLER_CHANGE, NOTE_ON, NOTE_OFF,
                                  PITCH_BEND, POLY_PRESSURE, PROGRAM_CHANGE)

import gstt, midi3, beatstep, laser, LPD8, C4, sequencer
import binascii

midi3.check()

import socket
import argparse
import json

import threading
#from libs import launchpad, bhoreal, dj
import maxwellccs, launchpad, bhoreal, dj
#from multiprocessing import Process


print ("")
print ("Arguments parsing if needed...")
argsparser = argparse.ArgumentParser(description="Maxwellator")
argsparser.add_argument("-m","--mode",help="MODE : startup, program, programall, list, command, osc, live, rand, mitraille, keyboard (live by default)",type=str)
argsparser.add_argument("-d","--destination",help="Midi destination name like Bus 1, to Maxwell 1,.. (to Maxwell 1 by default)",type=str)
argsparser.add_argument("-o","--oscip",help="iPad IP for TouchOSC UI",type=str)
argsparser.add_argument("-p","--oscport",help="iPad OSC port for TouchOSC UI",type=int)
argsparser.add_argument("-c","--channel",help="Start Midi channel (1 by default)",type=int)
argsparser.add_argument("-u","--universe",help="Universe, not implemented (0 by default)",type=int)
argsparser.add_argument("-s","--subuniverse",help="Subniverse, not implemented (0 by default)",type=int)
argsparser.add_argument("-i","--IP",help="Local IP (in the code by default) ",type=str)
#argsparser.add_argument("-v","--verbose",help="Verbosity level (0 by default)",type=int)



args = argsparser.parse_args()

# Mode
if args.mode:
    mode = args.mode
else:
    mode = "live"

if mode == "midifile":
     MidiLoad(midifile)

# Midi destinatio 
if args.destination:
    mididiest = args.destination
else:
    mididiest = "to Maxwell 1"

# Universe
if args.universe:
    universenb = args.universe
else:
    universenb = 0

# Universe
if args.subuniverse:
    subuniversenb = args.subuniverse
else:
    subuniversenb = 0

# start Midi Channel
if args.channel:
     gstt.basemidichannel = args.channel
else:
    gstt.basemidichannel = 1


# gstt.myIP
if args.IP  != None:
    gstt.myIP  = args.IP
#else:
#    gstt.myIP = '127.0.0.1'

# gstt.myIP = computerIP[0]
#print()
#print("IP address of the localhost is {}".format(gstt.myIP))
#print('Used IP', gstt.myIP)
#print('OSC incoming port :', gstt.MaxwellatorPort)



# iPad TouchOSC IP
if args.oscip  != None:
    gstt.TouchOSCIP = args.oscip

# Universe
if args.oscport:
    gstt.TouchOSCPort = args.oscport


def Disp(text, device = 'Launchpad Mini'):

    if midi3.FindInDevice(device)==-1:
        print("Matrix display",device,"not connected.")
    else:
        print("Matrix displaying ", text, 'to', device, midi3.FindInDevice(device))


    if (device.find("Launchpad Mini") or device =='launchpad') and midi3.FindInDevice('launchpad') != -1:
        #print("Display midi device",device, midi3.FindInDevice(device))
        scrolldisp.Display(text, color=(255,255,255), delay=0.2, mididest = 'launchpad')

    if device == 'bhoreal' and midi3.FindInDevice('Bhoreal'):
        scrolldisp.Display(text, color=(255,255,255), delay=0.2, mididest = device)

    '''
    if midi3.FindInDevice(device)
    if midi3.FindInDevice(device) != -1:
        if device == "Launchpad Mini":
            device ='launchpad'
        scrolldisp.Display(text, color=(255,255,255), delay=0.2, mididest = device)
    '''

#print("Midi Destination :", mididiest)

etherdreams = {
                0:       {"ID": "e60acc", "SrcIP": '127.0.0.1', "SrcMac": '08:6d:41:e6:0a:cc'},
                1:       {"ID": "dc5752", "SrcIP": '192.168.1.3', "SrcMac": '00:1e:c0:dc:57:52'},
                2:       {"ID": "e7c19a", "SrcIP": '192.168.1.4', "SrcMac": '00:04:a3:e7:c1:9a'},
                3:       {"ID": "dc1931", "SrcIP": '192.168.1.5', "SrcMac": '00:1e:c0:dc:19:31'},
                4:       {"ID": "dc03be", "SrcIP": '192.168.1.6', "SrcMac": '00:1e:c0:dc:03:be'},
                }



print('Scrolldisplay module...')

import scrolldisp
#scrolldisp.Display('.', color=(255,255,255), delay=0.2, mididest ='launchpad')


#
# OSC
#

print("OSC Server",gstt.myIP,':', gstt.MaxwellatorPort)
oscserver = OSCServer( (gstt.myIP, gstt.MaxwellatorPort) )
oscserver.timeout = 0
#oscrun = True

# this method of reporting timeouts only works by convention
# that before calling handle_request() field .timed_out is 
# set to False
def handle_timeout(self):
    self.timed_out = True

# funny python's way to add a method to an instance of a class
import types
oscserver.handle_timeout = types.MethodType(handle_timeout, oscserver)

# Generic client
def SendOSC(ip,port,oscaddress,oscargs=''):
        
    oscmsg = OSCMessage()
    oscmsg.setAddress(oscaddress)
    oscmsg.append(oscargs)
    
    osclient = OSCClient()
    osclient.connect((ip, port)) 

    print("sending OSC message : ", oscmsg, "to", ip, ":", port)

    try:
        osclient.sendto(oscmsg, (ip, port))
        oscmsg.clearData()
        return True
    except:
        print ('Connection to', ip, 'refused : died ?')
        return False


# RAW OSC Frame available ? 
def OSCframe():
    # clear timed_out flag
    oscserver.timed_out = False
    # handle all pending requests then return
    while not oscserver.timed_out:
        oscserver.handle_request()


# Properly close the system. Todo
def OSCstop():
    oscserver.close()


# default handler
def OSChandler(path, tags, args, source):

    oscaddress = ''.join(path.split("/"))
    print()
    print("Maxwellator Default OSC Handler got from " + str(source[0]),"OSC msg", path, "args", args)
    #print("OSC address", path)
    #print("find.. /bhoreal ?", path.find('/bhoreal'))
    if len(args) > 0:
        #print("with args", args)
        pass

    if FindCC(path) != None and len(args) > 0:
        SendCC(path,args[0])

    if path == '/note':
        print('sending note', args[0],'velocity', args[1])
        midi3.NoteOn(args[0],args[1],'to Maxwell 1') 

    if path.find('/bhoreal') == 0:
        #print('Incoming OSC Bhoreal with path', path[8:])
        bhoreal.FromOSC(path[8:],args)

    if path.find('/beatstep') == 0:
        #print('Incoming OSC Beatstep with path', path[8:])
        beatstep.FromOSC(path[9:],args)

    if path.find('/pad') == 0:
        print('Default : Incoming OSC launchpad with path', path[4:])
        launchpad.FromOSC(path[4:],args)

    if path.find('/laser') == 0:
        print('Incoming OSC laser with path', path[6:], "args", args)
        laser.FromOSC(path[6:], [1.0])

    if path[:4] =='/cc/':
        #print("Incoming CC", int(path[4:]), "with value", args[0], "function", maxwellccs.maxwell['ccs'][int(path[4:])]['Function'])
        maxwellccs.cc(int(path[4:]), int(args[0]),'to Maxwell 1')
        #beatstep.UpdateCC(int(path[4:]), int(args[0]))
        #maxwellccs.UpdateCCs(int(path[4:]), int(args[0]))

    if path.find('/LPD8') == 0:
        print('Incoming OSC LPD8 with path', path[5:])
        LPD8.FromOSC(path[5:],args)

    if path.find('/C4') == 0:
        print('Default : Incoming OSC C4 with path', path[4:])
        C4.FromOSC(path[4:],args)

    if path.find('/song/prev') > -1:
        maxwellccs.PSong()

    if path.find('/song/next') > -1:
        maxwellccs.NSong()

    if path.find('/blackout') > -1:
        print("SHOULD DO SOMETHING")


# /sendmx channel value
def OSCsendmx(path, tags, args, source):

    dmxchannel = args[0]
    val = args[1]
    updateDmxValue(dmxchannel, val)

# /bhoreal/note note velocity
def OSCNote(path, tags, args, source):

    gstt.patchnumber[0] = args[0]
    #print('New patch received',args)
    maxwellccs.runPatch(gstt.patchnumber[0])
    beatstep.UpdatePatch(gstt.patchnumber[0])
    C4.UpdatePatch(gstt.patchnumber[0])
    launchpad.UpdateDisplay()
    bhoreal.DisplayUpdate()

# /mixer/value 
def OSCMixerValue(path, tags, args, source):

    ccnumber = FindCC('/mixer/value')
    #print("Incoming Mixer L<->R : CC", ccnumber, "with value", args[0])
    maxwellccs.cc(ccnumber, int(args[0]),'to Maxwell 1')
    #beatstep.UpdateCC(ccnumber, int(args[0]))
    #maxwellccs.UpdateCCs(ccnumber, int(args[0]))

# /mixer/operation
def OSCMixerOperation(path, tags, args, source):

    ccnumber = FindCC('/mixer/operation')
    #print("Incoming Mixer operation: CC", ccnumber, "with value", args[0])
    maxwellccs.cc(ccnumber, int(args[0]),'to Maxwell 1')
    #beatstep.UpdateCC(ccnumber, int(args[0]))
    #maxwellccs.UpdateCCs(ccnumber, int(args[0]))

def SendEther(ip,oscaddress,oscargs=''):
        
    oscmsg = OSCMessage()
    oscmsg.setAddress(oscaddress)
    oscmsg.append(oscargs)
    
    osclientlj = OSCClient()
    osclientlj.connect((ip, 60000)) 

    print("sending OSC message : ", oscmsg, "to", ip, ":60000")
    try:
        osclientlj.sendto(oscmsg, (redisIP, 60000))
        oscmsg.clearData()
        return True
    except:
        print ('Connection to', ip, 'refused : died ?')
        return False



#
# CC functions
#

# /cc cc number value
def cc(ccnumber, value):

    if ccnumber > 127:
        midichannel = gstt.basemidichannel + 1
        ccnumber -= 127
    else:
        midichannel = gstt.basemidichannel

    gstt.ccs[0][ccnumber]= value
    #print("Sending Midi channel", midichannel, "cc", ccnumber, "value", value)
    midi3.MidiMsg([CONTROLLER_CHANGE+midichannel-1,ccnumber,value], mididiest)


def FindCC(FunctionName):

    for Maxfunction in range(len(maxwellccs.maxwell['ccs'])):
        if FunctionName == maxwellccs.maxwell['ccs'][Maxfunction]['Function']:
            #print(FunctionName, "is CC", Maxfunction)
            return Maxfunction


def LoadCC():
    global maxwell

    print("Loading Maxwell CCs Functions...")
    f=open("maxwell.json","r")
    s = f.read()
    maxwell = json.loads(s)
    gstt.maxwell = maxwell
    print(len(maxwell['ccs']),"Functions")
    #print("Loaded.")


def SendCC(path,init):

    funcpath = path.split("/")
    func = funcpath[len(funcpath)-1]
    #print(func)
    if func in maxwellccs.specificvalues:
        value = maxwellccs.specificvalues[func][init]
    else:
        value  = int(init)

    #print("sending CC", FindCC(path), "with value", value)
    cc(FindCC(path),value)
    time.sleep(0.005)


#
# Etherdreams commands
#

etherips = {"3": "192.168.1.3",
            "4": "192.168.1.4",
            "5": "192.168.1.5",
            "6": "192.168.1.6"
            }

def EtherCommands(path):

    if "ping" in path:
        EthersPings()
    else:

        commands = {"/ether/3/1": '192.168.3.3 /net/ipaddr 192.168.1.3',
                    "/ether/1/3": '192.168.1.3 /net/ipaddr 192.168.3.3', 
                    "/ether/4/1": '192.168.4.4 /net/ipaddr 192.168.1.4',
                    "/ether/1/4": '192.168.1.4 /net/ipaddr 192.168.4.4', 
                    "/ether/5/1": '192.168.5.5 /net/ipaddr 192.168.1.5',
                    "/ether/1/5": '192.168.1.5 /net/ipaddr 192.168.5.5', 
                    "/ether/6/1": '192.168.6.6 /net/ipaddr 192.168.1.6',
                    "/ether/1/6": '192.168.1.6 /net/ipaddr 192.168.6.6'
                    #"/ether/size": 
                  }
        newcommand = commands[path].split(" ")
        print (newcommand)
        SendEther(newcommand[0],newcommand[1],oscargs=newcommand[2])
    
def EthersPings():
    print()
    for ether in range(3,7):
        print()
        print("Testing etherdream", ether)
        #print("Testing", "192.168.1."+str(ether))
        if SendEther("192.168.1."+str(ether),"/ping"):
            etherips[str(ether)] = "192.168.1."+str(ether)
        elif SendEther("192.168."+str(ether)+"."+str(ether),"/ping"):
            etherips[str(ether)] = "192.168."+str(ether)+"."+str(ether)
        else:
            etherips[str(ether)] = "None"

        print (etherips[str(ether)])


#
# Artnet / DMX
#

def lhex(h):
    return ':'.join(x.encode('hex') for x in h)


def senddmx0():
    for dmxchannel in range (1,512):
        senddmx(dmxchannel,0)

def senddmx(dmxchannel, value):

    print("Setting dmxchannel %d to %d" % (i,value))
    #mydmx.setChannel((dmxchannel + 1 ), value, autorender=True)
    # calling render() is better more reliable to actually sending data
    # Some strange bug. Need to add one to required dmx channel is done automatically
    mydmx.setChannel((dmxchannel ), value)
    mydmx.render()
    print("Sending DMX Channel : ", str(dmxchannel), " value : ", str(value))

def updateDmxValue(dmxchannel, val):
    
    if dmxstates[dmxchannel] == -1:
        #print("assign channel", dmxchannel, "to",val)
        dmxstates[dmxchannel] = val

    # DMX UPDATE!!! WOW!!!
    if dmxstates[dmxchannel] != val:
        dmxstates[dmxchannel] = val
        print("updating DMX channel", dmxchannel, "with ", val )

        if mydmx != False:
            print("Sending DMX channel", dmxchannel, "with ", val )
            senddmx(dmxchannel, val) 
        newdmx = str(dmxchannel)+":"+str(val)
        #print("publishing", newdmx)
        r.publish('updates', newdmx)
        #print()

def StartArtnet():
    global sock, mydmx, dmxstates

    sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    sock.bind(('',6454))
    
    dmxeq = {}
    dmxstates = []
    dmxinit = False
    universe = []
    
    for i in range(1,514):
        dmxstates.append(-1)
            
    # Search for DMX devices
    #print("Available serial devices...")
    ports = list(list_ports.comports())
    
    portnumber = 0
    
    # Get all serial ports names
    for i, p in enumerate(ports):
    
        print(i, ":", p)
    
        if p[0]== "/dev/ttyUSB0":
          portname[portnumber] = p[0]
          portnumber += 1
    
    
        if platform == 'darwin' and p[1].find("DMX USB PRO") != -1:
          portname[portnumber] = p[0]
          portnumber += 1
    
    #print("Found", portnumber, "DMX devices")
    
    if portnumber > 0:
    
        print("with serial names", portname)
        mydmx = pysimpledmx.DMXConnection(gstt.serdmx[0])
        senddmx0()
        time.sleep(1)
    
        # Send a random value to dmxchannel 1
        vrand=random.randint(0,255)
        senddmx(1,vrand)
    
    else:
        mydmx = False
        print("No DMX interface, Art-Net receiver only.")

# Artnet Thread : 
def Artnet_thread():

    print()
    print("Artnet Thread...")
    dmxchannel = r.pubsub()

    StartArtnet()
    try:
        while True:

            data = sock.recv(10240)
            if len(data) < 20:
                continue
            
            if data[0:7] != "Art-Net" or data[7] != "\0":

                #print()
                #print("artnet package", len(data))
                    
                protverhi = data[10]
                protverlo = data[11]
                sequence  = data[12]
                physical  = data[13]
                subuni    = data[14]
                net       = data[15]
                lengthhi  = data[16]
                length    = data[17]
                dmx       = data[18:]
                
                #print(len(data))
                
                # ArtDMX part packet data length 530 (wireshark whole packet is 572)
                # ArtPollReply part packet data length 239 (wireshark whole packet : 281)
                if len(data) == 530:
                    #print (dmx)
                    for i in range(0,510):
                        pass
                        # Update DMX and send to Maxwell
                        updateDmxValue(i,dmx[i])
                
                continue
    
            if ord(data[8]) != 0x00 or ord(data[9]) != 0x50:
                print("OpDmx")
                continue
   
                  
    except Exception:
        traceback.print_exc()

    finally:
        print ("Stopping...")
        sock.close()
        artnet.join()


#
# Midifiles
#

# Load midifile
def MidiLoad(name):
    global MidiFileNotes, MidiFileIndex

    MidiFileNotes = []
    # Don't know how to browse MidiFile one by one.

    #print(ljpath+'/midifiles/')
    if os.path.exists(ljpath+'/midifiles/'+name):
        for msg in MidiFile(ljpath+'/midifiles/'+name):
            MidiFileNotes.append(msg)
    
    else:
        for msg in MidiFile('plugins/audio/midifiles/'+name):
            MidiFileNotes.append(msg)

    MidiFileIndex = 0
    return MidiFileNotes


#
# Run modes
#

# OSC / Artnet
def Osc():

    p = r.pubsub()
    p.subscribe('updates')
    print("Artnet updates subscribed")
    
    while True:

        # Handle OSC based changed
        OSCframe()

        # Handle Artnet change via redis key 'updates' subscription
        message = p.get_message()
        
        if message:
            messageCC = message['data']
            # print(type(messageCC))
            #print("Updates said: %s" % messageCC)
            if messageCC != 1:
                #if ":" in str(messageCC.decode('utf_8')):
                messageCC = messageCC.decode('utf_8')
                artnetCC = messageCC.split(":")               
                if len(artnetCC) > 1:
                    cc(int(artnetCC[0]), round(int(artnetCC[1])/2))
                    print()

        #time.sleep(0.0)


# OSC / Artnet
def Live():

    #Startup()
    try:

        artnet = threading.Thread(target = Artnet_thread, args = ())
        artnet.start()
        p = r.pubsub()
        p.subscribe('updates')
        print("Artnet updates subscribed")
    
        while True:
    
            # OSC event
            OSCframe()
            #time.sleep(0.01)
    
            # Artnet event via redis key 'updates' subscription
            message = p.get_message()
            
            if message:
                messageCC = message['data']
                # print(type(messageCC))
                #print("Updates said: %s" % messageCC)
                if messageCC != 1:
                    #if ":" in str(messageCC.decode('utf_8')):
                    messageCC = messageCC.decode('utf_8')
                    artnetCC = messageCC.split(":")               
                    if len(artnetCC) > 1:
                        cc(int(artnetCC[0]), round(int(artnetCC[1])/2))
                        print()
         
    except Exception:
        traceback.print_exc()

    finally:

        print ("Live mode Stopping...")
        artnet.join()
        if midi3.FindOutDevice("launchpad") != -1:
            launchpad.Cls()
        if midi3.FindOutDevice("bhoreal") != -1:
            bhoreal.Cls()



def Command():

    try:

        while True:

            OSCframe()
            path = input("What function ? (q to quit) : ")
            if path == "q" or path == "Q":
                break
            
            if "ether" in path:
                EtherCommands(path)
            else:
                init = input("What value ? (q to quit) : ")
                #FindCC(Funk)
                SendCC(path,init)

                  
    except Exception:
        traceback.print_exc()

    finally:
        print ("Stopping...")


def Startup():

    for Maxfunction in range(len(maxwell['ccs'])):

        path = maxwell['ccs'][Maxfunction]['Function']
        init = maxwell['ccs'][Maxfunction]['init']
        # print (path, "with", init)
        SendCC(path,init)
        # print()

def ProgramAll():

    print("Please put Maxwell in Midi learn mode.")
    for Maxfunction in range(len(maxwell['ccs'])):

        if "_comment" in maxwell['ccs'][Maxfunction]:
            
            print(maxwell['ccs'][Maxfunction]["_comment"])
            print()
        print()
        print ("Select",maxwell['ccs'][Maxfunction]['Function'], "function. Will be MIDI CC",Maxfunction)
        wait = input()
        cc(Maxfunction, 64)

def Program():

    try:

        while True:

            OSCframe()
            print("Please put Maxwell in Midi learn mode.")

            path = input("What function ? (q to quit) : ")
            if path == "q" or path == "Q":
                break
            
            if "ether" in path:
                EtherCommands(path)

            else:
                Maxfunction = FindCC(path)
                print ("Select", path, "function (will be MIDI CC", Maxfunction,":")
                wait = input()
                cc(Maxfunction, 64)
           
    except Exception:
        traceback.print_exc()

    finally:
        print ("Stopping...")


        
def List():

    for Maxfunction in range(len(maxwell['ccs'])):

        if "_comment" in maxwell['ccs'][Maxfunction]:
            print()
            print(maxwell['ccs'][Maxfunction]["_comment"])

        if Maxfunction > 127:
            midichannel = gstt.basemidichannel +1
            ccnumber = Maxfunction - 127
        else: 
            midichannel = gstt.basemidichannel
            ccnumber = Maxfunction
        print (maxwell['ccs'][Maxfunction]['Function'], "is Artnet", Maxfunction, "MIDI Channel", midichannel, "CC", ccnumber)
    print(Maxfunction +1, 'functions')



def Randomized():

    try:
        
        # Start Artnet
        artnet = threading.Thread(target = Artnet_thread, args = ())
        artnet.start()
        p = r.pubsub()
        p.subscribe('updates')
        print("Artnet updates subscribed")
        

        steps = gstt.steps
        rate = gstt.rate
    
        # Random choice of a function/gene
        gstt.randcc = random.randint(0,135)
        print(gstt.randcc, laser)

        startval = gstt.ccs[gstt.lasernumber][gstt.randcc] 
        endval = 64 + random.randint(-gstt.Range, gstt.Range)
        incval = int((endval - startval)/gstt.steps)
        print("Changing gene :", gstt.randcc, "from", startval, "to", endval, "incval", incval)

        while True:
    
            # OSC event
            OSCframe()
            #time.sleep(0.01)
    
            # Artnet event via redis key 'updates' subscription
            message = p.get_message()
            
            if message:
                messageCC = message['data']

                if messageCC != 1:
                    #if ":" in str(messageCC.decode('utf_8')):
                    messageCC = messageCC.decode('utf_8')
                    artnetCC = messageCC.split(":")               
                    if len(artnetCC) > 1:
                        maxwellccs.cc(int(artnetCC[0]), round(int(artnetCC[1])/2))
                        print()

            # 
            #print(counter)
            if steps == 0:

                inhib = random.randint(0,100) 
                #print(inhib, gstt.inhib)
                if random.randint(0,100) > gstt.inhib:
                    steps = gstt.steps
                    #print(gstt.randcc, gstt.fixedgenes)
                    gstt.randcc = random.randint(0,135)

                    while (gstt.randcc in gstt.fixedgenes) == True:    
                        print()
                        print("picked an already selected gene", gstt.randcc, "in", gstt.fixedgenes)
                        gstt.randcc = random.randint(0,135)
                        print("new random gene",gstt.randcc,gstt.fixedgenes)

                    startval = gstt.ccs[gstt.lasernumber][gstt.randcc] 
                    if startval > 127:
                        startval = 127
                    endval =  64 + random.randint(-gstt.Range, gstt.Range)
                    incval = int((endval - startval)/gstt.steps)
                    print("Changing gene :", maxwellccs.maxwell['ccs'][gstt.randcc]['Function'], "from", startval, "to", endval, "incval", incval)
                    print()

            rate -= 1
            if rate == 0:
                rate = gstt.rate

                if 0 < startval + incval < 127:
                    startval += incval
                    #print("Changing gene :",  maxwellccs.maxwell['ccs'][gstt.randcc]['Function'], "to", startval)
                    maxwellccs.cc(gstt.randcc, startval,'to Maxwell 1')
                if steps -1 >-1:
                    steps -= 1
            #print("rate", rate, "counter", counter)
                   
    except Exception:
        traceback.print_exc()

    finally:

        print ("Stopping...")
        artnet.join()
        if midi3.FindOutDevice("launchpad") != -1:
            launchpad.Cls()
        if midi3.FindOutDevice("bhoreal") != -1:
            bhoreal.Cls()


# Complexity indicator : how many notes are played at any moment
livenotes = 1
counter = 0

def Mitraille():
    global MidiFileIndex

    try:
        
        artnet = threading.Thread(target = Artnet_thread, args = ())
        artnet.start()
        p = r.pubsub()
        p.subscribe('updates')
        print("Artnet updates subscribed")
    
        while True:
    
            # OSC event
            OSCframe()
            #time.sleep(0.01)
    
            # Artnet event via redis key 'updates' subscription
            message = p.get_message()
            
            if message:
                messageCC = message['data']
                # print(type(messageCC))
                # print("Updates said: %s" % messageCC)
                if messageCC != 1:
                    #if ":" in str(messageCC.decode('utf_8')):
                    messageCC = messageCC.decode('utf_8')
                    artnetCC = messageCC.split(":")               
                    if len(artnetCC) > 1:
                        maxwellccs.cc(int(artnetCC[0]), round(int(artnetCC[1])/2))
                        print()


            msg = MidiFileNotes[MidiFileIndex]
            #print msg
            time.sleep(msg.time)

            if not msg.is_meta:    

                Message = msg.bytes()
                #print Message
                #print msg, msg.bytes()
            
                if len(Message) == 3 and Message[0]-144 < 15 :
                    MidiFileChannel = Message[0]-144
                    MidiFileNote = Message[1]
                    MidiFileVel = Message[2]
                    print()
                    print ("Midifile event ",MidiFileIndex, ": channel :", MidiFileChannel, "note :", MidiFileNote, 'velocity :', MidiFileVel)
                    midi3.NoteOn(MidiFileNote, MidiFileVel, "Bus 1")
                    #if MidiFileNote-24 >0:

                    # Other idea : rate control lfos
                    
                    # Lead : left part, for richter midi file : lead minimal note is E3 (64)
                    if MidiFileNote > 63:

                        # If lead note set a preset :
                        # midi3.NoteOn(MidiFileNote-63, MidiFileVel,'to Maxwell 1')
                        
                        # left curvetype is sin
                        SendCC('/osc/left/X/curvetype',0)

                        # octave is frequency. 25.6 is CC range (128)/5 low "pentatonic octave"
                        SendCC('/lfo/1/freq',round(MidiFileNote/12)*25.6)

                        # note is amplitude : decimal part of midinote number = CC range percentage 
                        SendCC('/lfo/1/phase',(MidiFileNote/12)%1*128)

                    # if note < 64 (E3) set RIGHT part
                    else:
                        # right curvetype is sin
                        SendCC('/osc/right/X/curvetype',0)

                        # octave is frequency. 25.6 is CC range (128)/5 low octave
                        SendCC('/lfo/2/freq',round(MidiFileNote/12)*25.6)
                        
                        # note is amplitude : decimal part of midinote number = CC range percentage 
                        SendCC('/lfo/2/phase',(MidiFileNote/12)%1*128)

                        '''
                        maxwellccs.current["prefixRight"]= "/osc/right/X"
                        maxwellccs.ChangeCurveRight(MidiFileNote/12)*25.6):
                        pass
                        0-11 
                        12-23
                        24-35
                        36-47
                        48-59
                        '''
                    '''
                    print (0, counter, 127)
                    midi3.NoteOn(counter, 127,'to Maxwell 1')
                    counter += 1
                    if counter > 64:
                    counter = 0
                    '''

                    if MidiFileVel == 0:
                        livenotes -= 1
                    else:
                        livenotes += 1 
                    print("livenotes :",livenotes)
                

            else:
                print ("Meta ",msg)

            MidiFileIndex += 1
            if MidiFileIndex == len(MidiFileNotes):
                MidiFileIndex = 0

                                 
    except Exception:
        traceback.print_exc()

    finally:

        print ("Stopping...")
        artnet.join()
        if midi3.FindOutDevice("launchpad") != -1:
            launchpad.Cls()
        if midi3.FindOutDevice("bhoreal") != -1:
            bhoreal.Cls()


def Midikeys():

    try:
        
        artnet = threading.Thread(target = Artnet_thread, args = ())
        artnet.start()
        p = r.pubsub()
        p.subscribe('updates')
        print("Artnet updates subscribed")
    
        while True:
    
            # OSC event
            OSCframe()
            #time.sleep(0.01)
    
            # Artnet event via redis key 'updates' subscription
            message = p.get_message()
            
            if message:
                messageCC = message['data']
                # print(type(messageCC))
                # print("Updates said: %s" % messageCC)
                if messageCC != 1:
                    #if ":" in str(messageCC.decode('utf_8')):
                    messageCC = messageCC.decode('utf_8')
                    artnetCC = messageCC.split(":")               
                    if len(artnetCC) > 1:
                        maxwellccs.cc(int(artnetCC[0]), round(int(artnetCC[1])/2))
                        print()


            msg = MidiFileNotes[MidiFileIndex]
            #print msg

            if not msg.is_meta:    

                Message = msg.bytes()
                #print Message
                #print msg, msg.bytes()
            
                if len(Message) == 3 and Message[0]-144 < 15 :
                    MidiFileChannel = Message[0]-144
                    MidiFileNote = Message[1]
                    MidiFileVel = Message[2]
                    print()
                    print ("Midi event ",MidiFileIndex, ": channel :", MidiFileChannel, "note :", MidiFileNote, 'velocity :', MidiFileVel)
                    midi3.NoteOn(MidiFileNote, MidiFileVel, "Bus 1")
                    #if MidiFileNote-24 >0:

                    # Other idea : rate control lfos
                    
                    # Lead : left part, for richter midi file : lead minimal note is E3 (64)
                    if MidiFileNote > 63:

                        # If lead note set a preset :
                        # midi3.NoteOn(MidiFileNote-63, MidiFileVel,'to Maxwell 1')
                        
                        # left curvetype is sin
                        SendCC('/osc/left/X/curvetype',0)

                        # octave is frequency. 25.6 is CC range (128)/5 low "pentatonic octave"
                        SendCC('/lfo/1/freq',round(MidiFileNote/12)*25.6)

                        # note is amplitude : decimal part of midinote number = CC range percentage 
                        SendCC('/lfo/1/phase',(MidiFileNote/12)%1*128)

                    # if note < 64 (E3) set RIGHT part
                    else:
                        # right curvetype is sin
                        SendCC('/osc/right/X/curvetype',0)

                        # octave is frequency. 25.6 is CC range (128)/5 low octave
                        SendCC('/lfo/2/freq',round(MidiFileNote/12)*25.6)
                        
                        # note is amplitude : decimal part of midinote number = CC range percentage 
                        SendCC('/lfo/2/phase',(MidiFileNote/12)%1*128)

                        '''
                        maxwellccs.current["prefixRight"]= "/osc/right/X"
                        maxwellccs.ChangeCurveRight(MidiFileNote/12)*25.6):
                        pass
                        0-11 
                        12-23
                        24-35
                        36-47
                        48-59
                        '''
                    '''
                    print (0, counter, 127)
                    midi3.NoteOn(counter, 127,'to Maxwell 1')
                    counter += 1
                    if counter > 64:
                    counter = 0
                    '''

                    if MidiFileVel == 0:
                        livenotes -= 1
                    else:
                        livenotes += 1 
                    print("livenotes :",livenotes)
                

            else:
                print ("Meta ",msg)

            MidiFileIndex += 1
            if MidiFileIndex == len(MidiFileNotes):
                MidiFileIndex = 0

                                 
    except Exception:
        traceback.print_exc()

    finally:

        print ("Stopping...")
        artnet.join()
        if midi3.FindOutDevice("launchpad") != -1:
            launchpad.Cls()
        if midi3.FindOutDevice("bhoreal") != -1:
            bhoreal.Cls()



#
# startup
#

SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/status', 'Maxwellator')
Disp('...')
oscserver.addMsgHandler( "default", OSChandler )
oscserver.addMsgHandler( "/bhoreal/note", OSCNote )
oscserver.addMsgHandler( "/mixer/value", OSCMixerValue )
oscserver.addMsgHandler( "/mixer/operation", OSCMixerOperation )
maxwellccs.LoadCC()
LoadCC()
laser.ResetUI()
#maxwellccs.runPatch(0)
print ("Beatstep Layer :",gstt.BeatstepLayer)
beatstep.ChangeLayer(gstt.BeatstepLayer)
print ("Beatstep Layer :",gstt.BeatstepLayers[gstt.BeatstepLayer])
LPD8.ChangeLayer(gstt.lpd8Layer)
launchpad.ChangeLayer(gstt.LaunchpadLayer)
bhoreal.ChangeLayer(gstt.BhorealLayer)
bhoreal.NoteOn(gstt.patchnumber[0],0)
C4.ChangeLayer(gstt.C4Layer)
sequencer.ChangeLayer(gstt.SequencerLayer)
SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/laser/patch/0', [0])
SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/laser/patch/1', [0])
SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/laser/patch/2', [0])
SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/laser/patch/3', [0])
SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/laser/led/'+str(gstt.lasernumber), [1])
SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/song/status', [gstt.songs[gstt.song]])
print()
print("Running in",mode,"mode")
print()
maxwellccs.RotarySpecifics(FindCC('/osc/left/Y/curvetype'), 0)

if mode =="startup":
    Startup()

if mode =="program":
    Program()

if mode =="programall":
    ProgramAll()

if mode =="osc":
    #artnet = Process(target=Artnet_thread, args=())
    artnet = threading.Thread(target = Artnet_thread, args = ())
    artnet.start()
    Osc()
    artnet.join()

if mode == "list":
    List()

if mode == "live":
    Live()

if mode == "command":
    Command()

if mode == "rand":
    Randomized()

if mode == "mitraille" :
    Mitraille()

if mode == "midikeys" :
    Midikeys()

OSCstop()

