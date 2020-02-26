# coding=UTF-8
'''

Global states variables
v0.8.0



LICENCE : CC NC


'''
BhorealLayer = 0
BhorealLayers = ['Maxwell1','Maxwell2','Maxwell3']

LaunchpadLayer = 0
LaunchpadLayers = ['Maxwell1','Maxwell2','Maxwell3','OS']

BeatstepLayer = 0
BeatstepLayers = ['XY','TraRot',"HueInt","Zregulators"]

SequencerLayer = 3
SequencerLayers = ['XY','TraRot',"HueInt","Zregulators"]

lpd8Layer = 0
lpd8Layers = ['Maxwell1','Maxwell2','Maxwell3','OS']

C4Layer = 0
C4Layers = ['Midi1','Midi2','Maxwell3','OS']

debug = 0

MaxwellatorPort = 8090

TouchOSCPort = 8101

#TouchOSCIP = '192.168.1.67' 	# iPad 1 for Laser network
#TouchOSCIP = '192.168.2.67' 	# iPad 1
TouchOSCIP = '192.168.2.156' 	# iPad mini
#TouchOSCIP = '192.168.43.146' 	# iPad mini @ fuzz
#TouchOSCIP = '192.168.151.213' # CCN

myIP= '127.0.0.1'
computerIP = ['127.0.0.1','192.168.2.42','192.168.2.52','127.0.0.1',
              '127.0.0.1','127.0.0.1','127.0.0.1','127.0.0.1']
basemidichannel = 1
lasernumber = 0
patchnumber = [0,0,0,0]
ccs =[[0] * 140] * 4
#PatchFiles = ["3d.json","3d.json","3d.json","3d.json"]
PatchFiles = ["rands.json","rands.json","rands.json","rands.json"]
Midikeyboards = ["midikeys","Samson Carbon49"]

songs = ["song1", "song2"]
song = 0

SequencerNameIN = "sequencer Bus 1"
SequencerNameOUT = "sequencer Bus 1"
#SequencerNameIN = 'electribe2 SOUND'
#SequencerNameOUT = 'electribe2 PAD/KNOB'

MidiSplitNote = 64
steps = 90
rate = 90
Range = 32
inhib = 0
fixedgenes = [200]
lasermode = 0

#songname = "song1"
