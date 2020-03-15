#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""

Maxwell Macros
v0.7.0

by Sam Neurohack 
from /team/laser

Launchpad set a "current path"

"""
 
from OSC3 import OSCServer, OSCClient, OSCMessage
import time
import numpy as np
import rtmidi
from rtmidi.midiutil import open_midiinput 
from threading import Thread
from rtmidi.midiconstants import (CHANNEL_PRESSURE, CONTROLLER_CHANGE, NOTE_ON, NOTE_OFF,
                                  PITCH_BEND, POLY_PRESSURE, PROGRAM_CHANGE)

import os, json
from datetime import datetime, timedelta
import midi3, gstt, beatstep, launchpad, bhoreal, LPD8, C4, bcr
#import tkinter.filedialog
import easygui

if os.uname()[1]=='raspberrypi':
    pass

#ip = "127.0.0.1"
mididest = 'Session 1'
djdest = 'Port'

midichannel = 1
lastcc = 0

computer = 0

current = {
    "prefixLeft": "/osc/left/X", 
    "prefixRight": "/osc/right/X", 
    "suffix": "/amp",
    "path": "/scaler/amt",
    "pathLeft": "/osc/left/X/curvetype",
    "pathRight": "/osc/left/X/curvetype",
    "previousmacro": -1,
    "LeftCurveType":  0,
    "lfo": 1,
    "rotator": 1,
    "translator": 1
    }

specificvalues = {

    # Sine: 0-32, Tri: 33-64, Square: 65-96, Line: 96-127
    "curvetype": {"sin": 0, "saw": 33, "squ": 95, "lin": 127},
    "freqlimit": {"1": 0, "4": 26, "16": 52, "32": 80, "127": 127},
    "amptype": {"constant": 0, "lfo1": 33, "lfo2": 95, "lfo3": 127},
    "phasemodtype": {"linear": 0,"sin": 90},
    "phaseoffsettype": {"manual": 0, "lfo1": 33, "lfo2": 95, "lfo3": 127},
    "ampoffsettype": { "manual": 0, "lfo1": 33, "lfo2": 95, "lfo3": 127},
    "inversion": {"off": 0, "on": 127},
    "colortype": {"solid": 0, "lfo": 127},
    "modtype": {"sin": 0,"linear": 127},
    "switch": {"off": 0,"on": 127},
    "operation": {"+": 0, "-": 50, "*": 127},
    "mode": {"solid": 0,"lfo": 127}
    }

shortnames = {
    "/osc/left/X" : "L X",
    "/osc/left/Y" : "L Y",
    "/osc/left/Z" : "L Z",
    "/osc/right/X" : "R X",
    "/osc/right/Y" : "R Y",
    "/osc/right/Z" : "R Z",
    "/duplicator" : "Dupli",
    "/rotator/X" : "Ro X",
    "/rotator/Y" : "Ro Y",
    "/rotator/Z" : "Ro Z",
    "/rotator/X/lfo" : "Ro X",
    "/rotator/Y/lfo" : "Ro Y",
    "/rotator/Z/lfo" : "Ro Z",
    "/translator/X" : "Tr X",
    "/translator/Y" : "Tr Y",
    "/translator/Z" : "Tr Z",
    "/translator/X/lfo" : "Tr X",
    "/translator/Y/lfo" : "Tr Y",
    "/translator/Z/lfo" : "Tr Z",
    "/color" : "",
    "/scaler" : "scale"
    }


# OSC Generic client
def SendOSC(ip, port, oscaddress, oscargs=''):
        
    oscmsg = OSCMessage()
    oscmsg.setAddress(oscaddress)
    oscmsg.append(oscargs)
    
    osclient = OSCClient()
    osclient.connect((ip, port)) 

    print("maxwellccs sending OSC message : ", oscmsg, "to", ip, ":", port)

    try:
        osclient.sendto(oscmsg, (ip, port))
        oscmsg.clearData()
        return True
    except:
        print ('Connection to', ip, 'refused : died ?')
        return False



#
# Maxwell CCs 
# 

def FindCC(FunctionName):

    for Maxfunction in range(len(maxwell['ccs'])):
        if FunctionName == maxwell['ccs'][Maxfunction]['Function']:
            #print(FunctionName, "is CC", Maxfunction)
            return Maxfunction

def LoadCC():
    global maxwell

    print("Maxwell CCs Functions...")

    if os.path.exists('maxwell.json'):
        #print('File maxwell.json exits')
        f=open("maxwell.json","r")

    else:
        if os.path.exists('../maxwell.json'):
            #print('File ../maxwell.json exits')
            f=open("../maxwell.json","r")

    s = f.read()
    maxwell = json.loads(s)
    #print(len(maxwell['ccs']),"Functions")
    #print("Loaded.")

# /cc cc number value
def cc(ccnumber, value, dest=mididest, midichannel =  gstt.basemidichannel):
    global lastcc

    if ccnumber > 127:
        midichannel = gstt.basemidichannel + 1
        ccnumber -= 127

    # mixer change display in OSC UI 
    if ccnumber ==90:
        SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/mixer/value', [value])
    
    gstt.ccs[gstt.lasernumber][ccnumber]= value
    lastcc = ccnumber
    print('Maxwellccs sending CC',[CONTROLLER_CHANGE+midichannel-1, ccnumber, value], dest)
    if gstt.lasernumber == 0:
        midi3.MidiMsg([CONTROLLER_CHANGE+midichannel-1, ccnumber, value], dest)
        UpdateCCs(ccnumber, value, laser = 0)
        # update CCs TouchOSC screen
        SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/cc/'+str(ccnumber),[value])
    else:
        SendOSC(gstt.computerIP[gstt.lasernumber], gstt.MaxwellatorPort, '/cc/'+str(ccnumber),[value])

    #SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/cc/'+str(ccnumber), [value])


def UpdateCCs(ccnumber, value, laser = 0):

    bhoreal.UpdateCC(ccnumber, value, laser)
    beatstep.UpdateCC(ccnumber, value, laser)
    LPD8.UpdateCC(ccnumber, value, laser)
    launchpad.UpdateCC(ccnumber, value, laser)
    C4.UpdateCC(ccnumber, value, laser)
    bcr.UpdateCC(ccnumber, value, laser)


# Reset CC Mode

# Reset current CC to 64 meaning no speed,... 
def resetCCON(value):

    print("CC Reseting mode ON")
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/status', ["CC resets ON"])
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/bcr/status', ["CC resets ON"])
    gstt.resetCC = 0



# Reset current CC to 64 meaning no speed,... 
def resetCCOFF(value):

    print("CC Reseting mode OFF")
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/status', ["CC resets OFF"])
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/bcr/status', ["CC resets OFF"])
    gstt.resetCC = -1


# Bang Mode

# Output to Maxwell on the bang 
def bangON(value):

    print("Bang mode ON")
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/status', ["Bang ON"])
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/bcr/status', ["Bang ON"])
    gstt.bang = 0

# Stop bang mode
def bangOFF(value):

    print("Bang OFF")
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/status', ["Bang OFF"])
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/bcr/status', ["Bang OFF"])
    gstt.bang = -1

# bang is trigged by something !
def bangbang(value):

    print()
    print("Bang !!")
    print()
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/status', ["Bang !!"])
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/bcr/status', ["Bang !!"])
    gstt.bangbang = 0




def NoteOn(note,velocity, dest=mididest, laser = gstt.lasernumber):
    midi3.NoteOn(note,velocity, mididest, laser)

def NoteOff(note, dest=mididest, laser = gstt.lasernumber):
    midi3.NoteOn(note, mididest, laser)


def Send(oscaddress,oscargs=''):

    oscmsg = OSCMessage()
    oscmsg.setAddress(oscaddress)
    oscmsg.append(oscargs)
    
    osclient = OSCClient()
    osclient.connect((ip, port)) 

    print("sending OSC message : ", oscmsg, "to", ip, ":",port)
    try:
        osclient.sendto(oscmsg, (ip, port))
        oscmsg.clearData()
        return True
    except:
        print ('Connection to', ip, 'refused : died ?')
        return False



def ssawtooth(samples,freq,phase):

    samparray = [0] * samples
    t = np.linspace(0+phase, 1+phase, samples)
    for ww in range(samples):
        samparray[ww] = signal.sawtooth(2 * np.pi * freq * t[ww])
    return samparray

def ssquare(samples,freq,phase):

    samparray = [0] * samples
    t = np.linspace(0+phase, 1+phase, samples)
    for ww in range(samples):
        samparray[ww] = signal.square(2 * np.pi * freq * t[ww])
    return samparray

def ssine(samples,freq,phase):

    t = np.linspace(0+phase, 1+phase, samples)
    for ww in range(samples):
        samparray[ww] = np.sin(2 * np.pi * freq  * t[ww])
    return samparray


def slinear(samples, min, max):

    samparray = [0] * samples
    linearinc = (max-min)/samples
    for ww in range(samples):
        if ww == 0:
            samparray[ww] = min
        else:
            samparray[ww] = samparray[ww-1] + linearinc
    #print('linear min max', min, max)
    #print ('linear',samparray)
    return samparray

def slinearound(samples, min, max):

    samparray = [0] * samples
    linearinc = (max-min)/samples
    for ww in range(samples):
        if ww == 0:
            samparray[ww] = round(min)
        else:
            samparray[ww] = round(samparray[ww-1] + linearinc)
    #print('linear min max', min, max)
    #print ('linear',samparray)
    return samparray


# * 11.27 : to get value from 0 to 127
def lin2squrt(value):
    return round(np.sqrt(value)*11.27)
     
def squrt2lin(value):
    return round(np.square(value/11.27))


def curved(value):
    return round(np.sqrt(value)*11.27)
'''
def curved(value):
    return round(np.sqrt(value)*11.27)
''' 

def Mixer(value):

    Send("/mixer/value", value)

def MixerLeft(value):

    if value == 127:
        Send("/mixer/value", 0)


def MixerRight(value):

    if value == 127:
        Send("/mixer/value", 127)

def MixerTempo(tempo):

    for counter in range(127):
        Send("/mixer/value", counter)

# Jog CC send : 127 to left and 1 to right
# increase or decrease current CC defined in current path  
def jogLeft(value):

    path = current["pathLeft"]
    print("jog : path =",path, "CC :", FindCC(path), "value", value)
    MaxwellCC = FindCC(current["pathLeft"])
    if value == 127:
        # decrease CC
        if gstt.ccs[0][MaxwellCC] > 0:
            gstt.ccs[0][MaxwellCC] -= 1
    else:
        if gstt.ccs[0][MaxwellCC] < 127:
            gstt.ccs[0][MaxwellCC] += 1
    #print("sending", gstt.ccs[0][MaxwellCC], "to CC", MaxwellCC )
    cc(MaxwellCC, gstt.ccs[0][MaxwellCC] , dest ='to Maxwell 1')
    #RotarySpecifics(MaxwellCC, path[path.rfind("/")+1:len(path)], value)


# Jog send 127 to left and 1 to right
# increase or decrease current CC defined in current path  
def jogRight(value):
    
    path = current["pathRight"]
    print("jog : path =",path, "CC :", FindCC(path), "value", value)
    MaxwellCC = FindCC(current["pathRight"])
    if value == 127:
        # decrease CC
        if gstt.ccs[0][MaxwellCC] > 0:
            gstt.ccs[0][MaxwellCC] -= 1
    else:
        if gstt.ccs[0][MaxwellCC] < 127:
            gstt.ccs[0][MaxwellCC] += 1
    #print("sending", gstt.ccs[0][MaxwellCC], "to CC", MaxwellCC )
    cc(MaxwellCC, gstt.ccs[0][MaxwellCC] , dest ='to Maxwell 1')
    #RotarySpecifics(MaxwellCC, path[path.rfind("/")+1:len(path)], value)


# Parameter change  : 127 : Previous type / 0 or 1 Next type
def RotarySpecifics(MaxwellCC, value):
    global maxwell

    #print("Maxwell CC :", MaxwellCC)
    #print("path :", maxwell['ccs'][MaxwellCC]['Function'])
    #print("Current :", maxwell['ccs'][MaxwellCC]['init'])
    #print("midi value :", value)
    #print("List Values", list(specificvalues))

    for count,cctype in list(enumerate(specificvalues)):
        if (cctype in maxwell['ccs'][MaxwellCC]['Function']) == True:
            specificsname = cctype
            #print(cctype, "is in :",maxwell['ccs'][MaxwellCC]['Function'])
            break

    #print("Specifics :",specificvalues[specificsname])

    elements = list(enumerate(specificvalues[specificsname]))
    #print("elements", elements)
    nextype = maxwell['ccs'][MaxwellCC]['init']
    #print('nextype', nextype)

    for count,ele in elements: 

        #if  maxwell['ccs'][MaxwellCC]['init'].Find(maxwell['ccs'][MaxwellCC]['init'])
        if ele == maxwell['ccs'][MaxwellCC]['init']:
            if count > 0 and value == 127:
                nextype = elements[count-1][1]

            if count < len(elements)-1 and value < 2:
                #print("next is :",elements[count+1][1])
                nextype = elements[count+1][1]

    #print("result :", nextype, "new value :", specificvalues[specificsname][nextype], "Maxwell CC", MaxwellCC)
    maxwell['ccs'][MaxwellCC]['init'] = nextype
    cc(MaxwellCC, specificvalues[specificsname][nextype], dest ='to Maxwell 1')


# Change type : trig with only with midi value 127 on a CC event
def ButtonSpecifics127( MaxwellCC, specificsname, value):
    global maxwell

    #print("Maxwell CC :",MaxwellCC)
    #print("Current :",maxwell['ccs'][MaxwellCC]['init'])
    #print("Specifics :",specificvalues[specificsname])
    #print("midi value :", value)


    elements = list(enumerate(specificvalues[specificsname]))
    #print(elements)
    nextype = maxwell['ccs'][MaxwellCC]['init']

    for count,ele in elements: 

        if ele == maxwell['ccs'][MaxwellCC]['init']:
            if count >0 and value == 127:
                nextype = elements[count-1][1]

            if count < len(elements)-1 and value < 2:
                #print("next is :",elements[count+1][1])
                nextype = elements[count+1][1]

    print("result :", nextype, "new value :", specificvalues[specificsname][nextype], "Maxwell CC", MaxwellCC)
    maxwell['ccs'][MaxwellCC]['init'] = nextype
    cc(MaxwellCC, specificvalues[specificsname][nextype], dest ='to Maxwell 1')


#
# Maxwell patchs files
#

def LoadPatchFile(filename, laser = 0):
    global patchs

    print("Load Maxwell patchs file :", filename)
    f=open("patchs/"+filename,"r")
    s = f.read()
    gstt.patchs = json.loads(s)
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/bhoreal/status', [filename])

    #print(len(gstt.patchs['pattrstorage']))
    #print(gstt.patchs['pattrstorage']['slots']['1']['data']["gen1-x::interfm-phase-offset"])
    #print("Loaded.")


def getPatchValue(patchnumber, ccnumber):

    #print("patch", patchnumber,"CC", ccnumber, ":",maxwell['ccs'][ccnumber]['maxwell'],"=",gstt.patchs['pattrstorage']['slots'][str(patchnumber)]['data'][maxwell['ccs'][ccnumber]['maxwell']])
    return int(gstt.patchs['pattrstorage']['slots'][str(patchnumber + 1)]['data'][maxwell['ccs'][ccnumber]['maxwell']][0]*127)



def runPatch(number, laser = 0):

    print()
    print("Run patch :", number, "on laser", laser,"...")
    
    # Patch exist ?
    if (str(number + 1) in gstt.patchs['pattrstorage']['slots']) != False:

        # Yes
        gstt.patchnumber[laser] = number
        for ccnumber in range(len(maxwell['ccs'])):

            # Update cc variable content and OSC UI for given laser
            gstt.ccs[laser][ccnumber] = getPatchValue(gstt.patchnumber[laser], ccnumber)

            SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/cc/'+str(ccnumber), [getPatchValue(gstt.patchnumber[laser], ccnumber)])
            
            # Update BCR 2000 CC if exists
            if bcr.Here != -1:
                midi3.MidiMsg([CONTROLLER_CHANGE, ccnumber, getPatchValue(gstt.patchnumber[laser], ccnumber)], "BCR2000")
        for ccnumber in range(len(maxwell['ccs'])):
            print(ccnumber," ",gstt.ccs[laser][ccnumber])

        # Update OSC UI patch number and send to Maxwell via midi
        SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/laser/patch/'+str(laser), [gstt.patchnumber[laser]])
        midi3.NoteOn(gstt.patchnumber[laser], 127, 'to Maxwell 1')
        

        #print("Laser", laser, ": current patch is now :", gstt.patchnumber[laser], 'ccs', gstt.ccs[laser])
    else:
        print("Patch doesnt exists")

def morphPatch(number, laser = 0):

    print()
    print("Morphing to patch number", number, "laser", laser,"in", gstt.morphsteps, "steps...")
    

    # Patch exist ?
    if (str(number + 1) in gstt.patchs['pattrstorage']['slots']) != False:

        # Yes
        gstt.patchnumber[laser] = number
        for ccnumber in range(len(maxwell['ccs'])):

            gstt.morphCCinc[ccnumber] = (getPatchValue(gstt.patchnumber[laser], ccnumber) - gstt.ccs[laser][ccnumber]) / gstt.morphsteps
            gstt.morphCC[ccnumber] = gstt.ccs[laser][ccnumber]
            print("CC", ccnumber, "was", gstt.ccs[laser][ccnumber],"will be", getPatchValue(gstt.patchnumber[laser], ccnumber), "so inced is", gstt.morphCCinc[ccnumber])

        gstt.morphing = 0
        
    else:
        print("Patch doesnt exists")
        gstt.morphing = -1


# Left cue button 127 = on  0 = off
def PrevPatch(value):

    print('PrevPatchVal function')
    if value == 127 and  gstt.patchnumber[0] - 1 > -1:
        cc(9, 127, dest=djdest)
        time.sleep(0.1)
        runPatch(gstt.patchnumber[0] - 1)
        #midi3.NoteOn(current['patch'], 127, 'to Maxwell 1')
        cc(9, 0, dest=djdest)

# Right cue button 127 = on  0 = off
def NextPatch(value):

    print('NextPatchVal function')
    if value == 127 and  gstt.patchnumber[0] + 1 < 41:
        cc(3, 127, dest = djdest)
        runPatch(gstt.patchnumber[0] + 1)
        time.sleep(0.1)
        cc(3, 0, dest = djdest)

#
# CCs
#


# increase/decrease a CC. Value can be positive or negative
def changeCC(value, path):

    MaxwellCC = FindCC(path)

    if gstt.ccs[0][MaxwellCC] + value > 127:
        gstt.ccs[0][MaxwellCC] = 127
    if gstt.ccs[0][MaxwellCC] + value < 0:
        gstt.ccs[0][MaxwellCC] = 0
    if gstt.ccs[0][MaxwellCC] + value < 127 and gstt.ccs[0][MaxwellCC] + value >0:
        gstt.ccs[0][MaxwellCC] += value

    print("Change CC in maxwellccs : path =", path, "CC :", FindCC(path), "is now ", gstt.ccs[0][MaxwellCC])
    cc(MaxwellCC, gstt.ccs[0][MaxwellCC] , dest ='to Maxwell 1')
    


def gsteps(value, macroname):
    if value > 90  and gstt.steps -1 > -1:
        gstt.steps -= 1
    else:
        gstt.steps += 1
    
    #macroname = beatstep.macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][beatstep.findMacros('maxwellccs.steps','Z')]["name"]
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/beatstep/'+macroname+'/value', [format(gstt.steps, "03d")])
    #print("steps",gstt.steps,beatstep.findMacros('maxwellccs.steps','Z'), '/beatstep/'+macroname+'/value')

def grate(value, macroname):
    if value > 90 and gstt.rate -1 > -1:
        gstt.rate -= 1
    else:
        gstt.rate += 1
    
    #macroname = beatstep.macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][beatstep.findMacros('maxwellccs.rate','Z')]["name"]
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/beatstep/'+macroname+'/value', [format(gstt.rate, "03d")])
    #print("rate",gstt.rate, beatstep.findMacros('maxwellccs.rate','Z'),'/beatstep/'+macroname+'/value')

def grange(value,macroname):
    #print("grange incoming value", value, "gstt.Range", gstt.Range)
    if value > 90 and gstt.Range -1 > -1:
        gstt.Range -= 1
    if value < 30 and gstt.Range +1 < 65:
        gstt.Range += 1

    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/beatstep/'+macroname+'/value', [format(gstt.Range, "03d")])
    #print("grange",gstt.Range, beatstep.findMacros('maxwellccs.grange','Z'),'/beatstep/'+macroname+'/value')


def ginhib(value,macroname):
    #print("inhib incoming value", value, "gstt.inhib", gstt.inhib)
    if value > 90 and gstt.inhib -1 >-1:
        gstt.inhib -= 1
    if value < 30 and gstt.inhib +1 < 101:
        gstt.inhib += 1

    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/beatstep/'+macroname+'/value', [format(gstt.inhib, "03d")])

# lasermode ON : set duplicator number (CC 87) to 1 and append it to fixedgenes.
# lasermode OFF : remove duplicator number (CC 87) from fixedgenes.
def lasermode(value, macroname):
    #print("lasermode with",value, macroname)
    # switch to ON
    if gstt.lasermode == 0:
        gstt.lasermode = 1
        gstt.fixedgenes.append(87)
        print("Lasermode ON")
        cc(87, 0, dest ='to Maxwell 1')
    
    # switch to OFF
    else: 
        gstt.lasermode = 1
        gstt.fixedgenes.remove(87)
        print("Lasermode OFF")


def rateselect(value, macroname):
    #print(gstt.fixedgenes)
    gstt.fixedgenes.append(gstt.randcc)
    #print(gstt.fixedgenes)

def stepsselect(value, macroname):
    #print(gstt.fixedgenes)
    gstt.fixedgenes.append(gstt.randcc)
    #print(gstt.fixedgenes)

# add a "gene" = cc in list of already selected genes
def gselect(value, macroname):
    #print("gselect", gstt.fixedgenes, gstt.randcc)
    gstt.fixedgenes.append(gstt.randcc)
    print(gstt.randcc, "was added to fixed genes list", gstt.fixedgenes)
    print()

def PlusTenLeft(value):
    if value == 127:
        changeCC(10, current["pathLeft"])

def MinusTenLeft(value):
    if value == 127:
        changeCC(-10, current["pathLeft"])

def PlusOneLeft(value):
    if value == 127:
        changeCC(1, current["pathLeft"])

def MinusOneLeft(value):
    if value == 127:
        changeCC(-1, current["pathLeft"])

def PlusTenRight(value):
    if value == 127:
        changeCC(10, current["pathRight"])

def MinusTenRight(value):
    if value == 127:
        changeCC(-10, current["pathRight"])

def PlusOneRight(value):
    if value == 127:
        changeCC(1, current["pathRight"])

def MinusOneRight(value):
    if value == 127:
        changeCC(-1, current["pathRight"])

def PlusTen(value):
    if value == 127:
        changeCC(10, current["path"])

def MinusTen(value):
    if value == 127:
        changeCC(-10, current["path"])

def PlusOne(value, path =  current["path"]):
    if value == 127:
        changeCC(1, path)

def MinusOne(value, path =  current["path"]):
    if value == 127:
        changeCC(-1, path)


def EncoderPlusOne(value, path =  current["path"]):
    if value < 50:
        changeCC(1, path)

def EncoderMinusOne(value, path =  current["path"]):
    if value > 90:
        changeCC(-1, path)


def EncoderPlusTen(value, path =  current["path"]):
    if value < 50:
        changeCC(10, path)

def EncoderMinusTen(value, path =  current["path"]):
    if value > 90:
        changeCC(-10, path)


def ChangeCurveLeft(value):

    MaxwellCC = FindCC(current["prefixLeft"] + '/curvetype')
    RotarySpecifics(MaxwellCC, value)


def ChangeFreqLimitLeft(value):

    MaxwellCC = FindCC(current["prefixLeft"] + '/freqlimit')
    RotarySpecifics(MaxwellCC, value)


def ChangeATypeLeft(value):

    MaxwellCC = FindCC(current["prefixLeft"] + '/freqlimit')
    RotarySpecifics(MaxwellCC, value)

def ChangePMTypeLeft(value):

    MaxwellCC = FindCC(current["prefixLeft"] + '/phasemodtype')
    RotarySpecifics(MaxwellCC, value)

def ChangePOTypeLeft(value):

    MaxwellCC = FindCC(current["prefixLeft"] + '/phaseoffsettype')
    RotarySpecifics(MaxwellCC, value)


def ChangeAOTypeLeft(value):

    MaxwellCC = FindCC(current["prefixLeft"] + '/ampoffsettype')
    RotarySpecifics(MaxwellCC, value)


def ChangeCurveRight(value):

    MaxwellCC = FindCC(current["prefixRight"] + '/curvetype')
    RotarySpecifics(MaxwellCC, value)


def ChangeCurveLFO(value):

    MaxwellCC = FindCC('/lfo/'+ current["lfo"] +'/curvetype')
    RotarySpecifics(MaxwellCC, value)


def ChangeCurveRot(value):

    MaxwellCC = FindCC('/rotator/'+ current["rotator"] +'/curvetype')
    RotarySpecifics(MaxwellCC, value)


def ChangeCurveTrans(value):

    MaxwellCC = FindCC('/translator/'+ current["translator"] +'/curvetype')
    RotarySpecifics(MaxwellCC, value)

#
# UI functions
#

def Laser0():

    SendOSC(gstt.myIP, 8090, '/laser/0/button', [0])
    gstt.lasernumber = 0

def Laser1():

    SendOSC(gstt.myIP, 8090, '/laser/1/button', [1])
    gstt.lasernumber = 1

def Laser2():

    SendOSC(gstt.myIP, 8090, '/laser/2/button', [2])
    gstt.lasernumber = 2

def Laser3():

    SendOSC(gstt.myIP, 8090, '/laser/3/button', [3])
    gstt.lasernumber = 3



def Beatstep():
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/beatstep', [1])

def Bhoreal():
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/bhoreal', [1])

def Launchpad():
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/pad', [1])

def Maxwell():
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/maxwell', [1])

def c4():
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/C4', [1])

def Bcr():
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/bcr', [1])

def Aurora():
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/aurora', [1])


def PPatch():

    PrevPatch(127)

def NPatch():
    NextPatch(127)

def Reload():
    LoadPatchFile(gstt.PatchFiles[0])
    launchpad.UpdateDisplay()
    bhoreal.DisplayUpdate()


def Load():
    
    #Tk().withdraw()
    #PatchFile =  tkinter.filedialog.askopenfilename()
    PatchFile = easygui.fileopenbox(default='patchs/*.json', filetypes=["*.json"], multiple=False)
    print(PatchFile)
    #LoadPatchFile(gstt.PatchFiles[0])

def L():

    ccnumber = FindCC('/mixer/value')
    print("Incoming Mixer L<->R : CC", ccnumber, "with value", 0)
    if gstt.lasernumber == 0:
        cc(ccnumber, 0,'to Maxwell 1')
    else: 
        SendOSC(gstt.computerIP[gstt.lasernumber], gstt.MaxwellatorPort, '/mixer/value', 0)
    #beatstep.UpdateCC(ccnumber, 0)

def R():
    ccnumber = FindCC('/mixer/value')
    print("Incoming Mixer L<->R : CC", ccnumber, "with value", 127)
    if gstt.lasernumber == 0:
        cc(ccnumber, 127,'to Maxwell 1')
    else: 
        SendOSC(gstt.computerIP[gstt.lasernumber], gstt.MaxwellatorPort, '/mixer/value', 127)
    #beatstep.UpdateCC(ccnumber, 127)


def Empty():

    print ("Empty")

# Beatstep previous layer
def BPLayer():

    beatstep.PLayer()

# Beatstep next layer
def BNLayer():

    beatstep.NLayer()

# LPD8 previous layer
def LPLayer():

    LPD8.PLayer()

# LPD8 Next layer
def LNLayer():

    LPD8.NLayer()

#
# Songs
#

def NSong():

    print(gstt.song + 1, len(gstt.songs))
    if gstt.song + 1< len(gstt.songs):
        gstt.song += 1
        print("New song :",gstt.songs[gstt.song])
        SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/song/status', [gstt.songs[gstt.song]])

def PSong():

    if gstt.song != 0:
        gstt.song -= 1
        print("New song :",gstt.songs[gstt.song])
        SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/song/status', [gstt.songs[gstt.song]])

# Forward incoming sequencer CC changes to local (= on midi channel 16) display i.e BCR 2000
def ELCC(ccnumber,value):
    
    print("ELCC forward CC", ccnumber,":", value, "to TouchOSC and BCR 2000 channel 16")

    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/states/cc/'+str(ccnumber), [value])
    midi3.MidiMsg((CONTROLLER_CHANGE+15, ccnumber, int(value)), mididest = "BCR2000")


# Get BPM from tap tempo or note from a sequencer 
# BPM channel 16 CC 127 
def autotempo(note):
    global lastime

    currentime = datetime.now()
    delta = currentime - lastime 
    lastime = currentime
    gstt.currentbpm = round(60/delta.total_seconds())
    print("length between notes :", delta.total_seconds(),"seconds -> bpm :", gstt.currentbpm)

    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/bpm', [gstt.currentbpm])

    # STUPID : need to find a way to display bpm > 127
    # tell BCR 2000 the new bpm on channel 16 
    if gstt.currentbpm > 127:
        midi3.MidiMsg((CONTROLLER_CHANGE+15, 127, 127), mididest = "BCR2000")
    else:
        midi3.MidiMsg((CONTROLLER_CHANGE+15, 127, gstt.currentbpm), mididest = "BCR2000")


lastime  = datetime.now()
tempotime = lastime
print("Sequencer time", lastime)


LoadPatchFile(gstt.PatchFiles[gstt.lasernumber])


