#!/usr/bin/python3
# -*- coding: utf-8 -*-
# -*- mode: Python -*-

'''
ccsliders

Midi fader sending cc messages 

'''


from tkinter import *

import time
import rtmidi
from rtmidi.midiutil import open_midiinput 
from rtmidi.midiconstants import (CHANNEL_PRESSURE, CONTROLLER_CHANGE, NOTE_ON, NOTE_OFF,
                                  PITCH_BEND, POLY_PRESSURE, PROGRAM_CHANGE)

from mido import MidiFile
import mido
import sys
sys.path.append('libs/')
import midi3
midi3.check()

#mididest = 'to Maxwell 1'
mididest =  'electribe2 SOUND'
mididest =  'BCR2000'
cc0 = 0
cc1 = 82
cc2 = 83
cc3 = 84
midichannel = 1

ccs = [0,0,0,0]

# /cc cc number value
def sendcc(ccnumber, value, dest):

    print("Sending Midi channel", midichannel, "cc", ccnumber, "value", value, "to", dest)
    midi3.MidiMsg([CONTROLLER_CHANGE+midichannel-1, ccnumber, value], dest)


class Interface(Frame):
    
    """Notre fenêtre principale.
    Tous les widgets sont stockés comme attributs de cette fenêtre."""
    
    def __init__(self, myframe, **kwargs):
        Frame.__init__(self, myframe, width=768, height=576, bg="black", **kwargs)
        self.pack(fill=NONE)
        self.nb_clic = 0
        
        # Création de nos widgets
        self.message = Label(self, text="Maxwellator",  bg="black", foreground="white")
        self.message.place(x = 0, y = 25)
        self.message.pack()
        #self.message.config(bg="black", foreground="white")

        self.w1 = Scale(self, from_=127, to=0,  bg="black", foreground="white")
        self.w1.pack(side="left")
        self.w2 = Scale(self, from_=127, to=0, bg="black", foreground="white")
        self.w2.pack(side="left")
        self.w3 = Scale(self, from_=127, to=0,  bg="black", foreground="white")
        self.w3.pack(side="left")
        self.w4 = Scale(self, from_=127, to=0,  bg="black", foreground="white")
        self.w4.pack(side="left")

        self.w5 = Scale(self, from_=127, to=0,  bg="black", foreground="white")
        self.w5.pack(padx =1, pady=30)
        
        self.quit_button = Button(self, text="Quit", command=self.quit)
        #self.quit_button.configure(background = "green")  
        self.quit_button.pack(side="bottom")
        self.update_cc()
        '''
        self.bouton_cliquer = Button(self, text="Cliquez ici", fg="red",
                command=self.cliquer)
        self.bouton_cliquer.pack(side="right")
        '''



    def update_cc(self):

        cc0value = int(self.w1.get())
        cc1value = int(self.w2.get())
        cc2value = int(self.w3.get())
        cc3value = int(self.w4.get())

        if cc0value !=  ccs[0]:
            sendcc(cc0, cc0value, mididest)
            ccs[0] = cc0value 
            newcc = "CC", cc0, ":", str(cc0value)
            #print(newcc)
            self.message.configure(text = newcc)

        if cc1value !=  ccs[1]:
            sendcc(cc1, cc1value, mididest)
            ccs[1] = cc1value 
            newcc = "CC", cc1, ":", str(cc1value)
            #print(newcc)
            self.message.configure(text = newcc)

        if cc2value !=  ccs[2]:
            sendcc(cc2, cc2value, mididest)
            ccs[2] = cc2value 
            newcc = "CC", cc2, ":", str(cc2value)
            #print(newcc)
            self.message.configure(text = newcc)

        if cc3value !=  ccs[3]:
            sendcc(cc3, cc3value, mididest)
            ccs[3] = cc3value 
            newcc = "CC", cc3, ":", str(cc3value)
            print(newcc)
            self.message.configure(text = newcc)

        #print( 'CC', cc0,':', PrettyFloat(cc1value), ' CC', cc1, ":", PrettyFloat(cc1value),' CC', cc2, ":", PrettyFloat(cc2value)," CC",cc3,":",PrettyFloat(cc3value))
        '''
        with open('/tmp/ws.json', 'w') as outfile:
            json.dump(data, outfile)
        '''

        self.after(100, self.update_cc)
    '''
    def cliquer(self):
        """Il y a eu un clic sur le bouton.
        
        On change la valeur du label message."""
        
        self.nb_clic += 1
        self.message["text"] = "Vous avez cliqué {} fois.".format(self.nb_clic)
    '''

myframe = Tk()
interface = Interface(myframe)
interface.mainloop()
interface.destroy()


