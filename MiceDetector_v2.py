
# coding: utf-8

                ## THis is a notebook for troubleshooting things

1. Will connect to arduino
2. Move the servo motor
3. Check if RFid works......
4. Write to the arduino
                
# In[1]:

# Define all of my import....
import serial
import time
from keyboard_alike import reader
import usb.core
import usb.util
from multiprocessing import Process
from transitions import Machine
import timeit
from threading import Timer
import time


# In[18]:

get_ipython().magic(u'pinfo Machine')


# In[2]:

#initialize arduino object
arduino1 = serial.Serial('/dev/ttyACM0', 9600)
arduino2 = serial.Serial('/dev/ttyACM1', 9600)

#initialize RFidReader1

#initialize list of RFidReaders connected to computer

# #initialize reader1 to the RFidReader at position 0 in device list
#reader1.initialize(device[0])
#reader2.initialize(device[1])

#reader2.initialize(device[1])

#initialize open and close gate values
openGate = 160
closeGate = 70
#initialize empty string for RFid value to be stored in
code1 = ''
code2 = ''
code3 = ''

#initialize boolean variable to determine which stage a mice is in
miceOneIsEntering = True


# In[3]:

class Mice:
    '''Mice class; this class will keep track of which mice is at each stage'''         
    # The states
    states=['left', 'centerOut', 'right', 'centerIn']

    # The transitions
    transitions = [
        {'trigger': 'leftToCenter', 'source': 'left', 'dest': 'center'},
        {'trigger': 'centerToRight', 'source': 'center', 'dest': 'right'},
        {'trigger': 'rightToCenter', 'source': 'right', 'dest': 'center'},
        {'trigger': 'centerToLeft', 'source': 'center', 'dest': 'left'}
    ]
    
    def __init__(self, code):
        self.code = code
        
        self.machine = Machine(model=self, states=Mice.states, initial='left')
        
        self.machine.add_transition(trigger = 'leftToCenter', source='left', dest = 'centerOut')
        
        self.machine.add_transition(trigger = 'centerToRight', source='centerOUt', dest = 'right')
        
        self.machine.add_transition(trigger = 'rightToCenter', source='right', dest = 'centerIn')
        
        self.machine.add_transition(trigger = 'centerToLeft', source='centerIn', dest = 'left')
        
        self.machine.add_ordered_transitions(['left', 'centerOut', 'right', 'centerIn'])
        
#instantiate mice
miceID = [None] * 3
miceID[0] = Mice(6164996)
miceID[1] = Mice(8657565)
miceID[2] = Mice(12919161)

miceID[0].leftToCenter()

print miceID[0].state


# In[4]:

def readReader1():
    reader1 = reader.Reader(0x16c0, 0x27db, 36, 3, should_reset=False)
    device = list(usb.core.find(find_all=True, idVendor=0x16c0, idProduct = 0x27db))
    reader1.initialize(device[0])
    global code1
    code1 = reader1.read()
    if code1 != '':
        code1 = int(code1)
    reader1.disconnect()
    return code1

def readReader2():
    reader2 = reader.Reader(0x16c0, 0x27db, 36, 3, should_reset=False)
    device = list(usb.core.find(find_all=True, idVendor=0x16c0, idProduct = 0x27db))
    reader2.initialize(device[1])
    global code2
    code2 = reader2.read()
    if code2 != '':
        code2 = int(code2)
    reader2.disconnect()
    return code2

def gate1():
    arduino1.write(str(openGate))
    time.sleep(2)
    arduino1.write(str(closeGate))

def gate2():
    arduino2.write(str(openGate))
    time.sleep(2)
    arduino2.write(str(closeGate))


# ## Current state of the code....
# 
# Currently we have Loaded all of the RFid tags of 3 mice into miceID as a list, and we have the states of all those mice in miceState as a list of PyTransition objects.
# 
# Now, we want to write code, to start and stop listening on certain RFid readers depending on the current states of all the animals.
# 
# First thing to do is determine the state that the current paradigm is in.....
# 
# Note: We have to act on the miceID class instead of on the transition machine object....

# In[ ]:

# Variable globalState
# Which is 1, 2, 3, or 4 depending on which state you are in
globalState = 1

while 1:
    if globalState == 1:
        # Listening to RFid 1
        #if MouseAllowed
            # do something, 
            # Open gate
            # Close Gate
            # Switch to globalState = 2
        #else: # Mouse is not allowed...
        #    continue
        while True: 
            readReader1() #readReader1() is in a while loop because RF id sensors have a 5 second window to detect keys
            if code1 != '': # Break out once we have read a key
                break
        gate1() # Open Gate
        globalState = 2
        
    elif globalState == 2:
        # Listen to RFid 2
        # If nothing happens on RFid 2 for >60s that is because mouse is not in center, return to state 1....
        # If RFid matches on RFid 2 of mouse in RFid state 1
        # Open gate. and proceed to globalState = 3
        repeat = 12
        while repeat > 0:
            readReader2()
            if code2 != '':
                break
            repeat = repeat - 1

        if code2 == '':
            print 'No mice in the center returning to state 1'
            globalState = 1
        elif code1 == code2:
                gate2()
                globalState = 3
                print globalState
        
    elif globalState == 3:
        print 'We made it to state 3'
        # Stay i global State = 3
        # Until you receive signal from behavior box that session is terminated.....
        # For troubleshooting puproses, just assume you stay in here for < 900s
        #time.sleep(5)
        while True:
            readReader2()
            if code3 != '':
                break
        gate2()
        global state
        
        pass
    elif globalState == 4:
        # If RFid 1 matches the mouse that is returning, then open the gate.....
        pass
    
    else:
            print 'something is wrong...'
