# Define all of my import....
import serial
import time
from keyboard_alike import reader
import usb.core
import usb.util
from transitions import Machine
import timeit
from threading import Timer
import datetime

path = 'log.txt'

#initialize arduino object
arduino1 = serial.Serial('/dev/ttyACM1', 9600)
arduino2 = serial.Serial('/dev/ttyACM0', 9600)

#initialize list of RFidReaders connected to computer
device = list(usb.core.find(find_all=True, idVendor=0x16c0, idProduct = 0x27db))
reader1 = reader.Reader(0x16c0, 0x27db, 36, 3, should_reset=False)
reader2 = reader.Reader(0x16c0, 0x27db, 36, 3, should_reset=False)

#initialize open and close gate values
openGate = 160
closeGate = 70
#initialize empty string for RFid value to be stored in
code1 = ''
code2 = ''
code3 = ''
code4 = ''

#initialize boolean variable to determine which stage a mice is in
miceOneIsEntering = True

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
    
    def __init__(self, code, isAllowed):
        self.code = code
        self.isAllowed = isAllowed
        self.machine = Machine(model=self, states=Mice.states, initial='left')
        self.machine.add_transition(trigger = 'leftToCenter', source='left', dest = 'centerOut')
        self.machine.add_transition(trigger = 'centerToRight', source='centerOUt', dest = 'right')        
        self.machine.add_transition(trigger = 'rightToCenter', source='right', dest = 'centerIn')        
        self.machine.add_transition(trigger = 'centerToLeft', source='centerIn', dest = 'left')
        self.machine.add_ordered_transitions(['left', 'centerOut', 'right', 'centerIn'])

#instantiate mice
miceID = [None] * 3
miceID[0] = Mice(6164996, True)
miceID[1] = Mice(8657565, True)
miceID[2] = Mice(12919161, True)

def readReader1():
    reader1.initialize(device[0])
    global code1
    code1 = reader1.read()
    if code1 != '': 
        code1 = int(code1)
    reader1.disconnect()
    return code1

def readReader2():
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

file = open(path, 'w')
# Variable globalState
# Which is 1, 2, 3, or 4 depending on which state you are in
globalState = 1
while 1:
    if globalState == 1:
        #Once we check globalState and pass, we enter another while True loop.
        while True: 
            #readReader1() is in a while loop because RF id sensors have a 5 second window to detect keys
            readReader1()
            if code1 != '': #At the end of that 5 second window we check to see of code1 is asinged a value.
                file.write('* read key: ' + str(code1) + ' .... ' + str(datetime.datetime.now()) + '\n')
                break # break out of the infinite loop once we have a code.
                
        for i in miceID: # Then we loop through all the mice in array miceID
            if code1 == i.code and i.isAllowed == True: # We check which mouse matches the code we recieve and check if it is allowed
                gate1()# Open Gate
                file.write('* Mouse is allowed to enter; open gate 1; state = 2 ' + str(datetime.datetime.now())+ '\n')
                globalState = 2 # Chance globalState to 2

    elif globalState == 2:
        # Listen to RFid 2
        # If nothing happens on RFid 2 for >60s that is because mouse is not in center, return to state 1....
        # If RFid matches on RFid 2 of mouse in RFid state 1
        # Open gate. and proceed to globalState = 3
        repeat = 12
        while repeat > 0: # While 60 seconds
            readReader2() # listen to RFid 2
            file.write('* reader 2 is listening to RFid key ' + str(datetime.datetime.now())+ '\n')
            if code2 != '':
                file.write('* break out of 60 second listening window ' + str(datetime.datetime.now())+ '\n')
                break # break once we recieved a code
            repeat = repeat - 1

        if code2 == '': # check if mice is in center tube
            file.write('* No mice is tube, set state to 1 ' + str(datetime.datetime.now())+ '\n')
            globalState = 1 # set globalState to 1
        elif code1 == code2: # if we did recieve a code
                gate2() # open gate 2
                file.write('* open gate 2; set sate to ' + str(datetime.datetime.now())+ '\n')
                globalState = 3 # set globalState to 3
        
    elif globalState == 3:
        # Stay i global State = 3
        # Until you receive signal from behavior box that session is terminated.....
        # For troubleshooting puproses, just assume you stay in here for < 900s
        #time.sleep(5)
        while True: # listen to RFid reader 2 for an infinite amount of time...
            code3 = readReader2()
            file.write('* reader 2 just listened to key ' + str(datetime.datetime.now())+ '\n')
            if code3 != '': # ... until we recieve the code and break
                break
        gate2() # open gate 2
        file.write('* open gate 2; set sate to 4 ' + str(datetime.datetime.now())+ '\n')
        globalState = 4 # set globalState to 4
        
        pass
    elif globalState == 4:
        # If RFid 1 matches the mouse that is returning, then open the gate.....
        if code3 == code1: # checking if the same mouse is returning
            while True:
                code4 = readReader1() 
                file.write('* reader 1 just listened to returning mouse ' + str(datetime.datetime.now())+ '\n')
                if code4 != '':
                    break # breaking once we recieved a code from RFid reader 1
            
            for i in range(len(miceID)): # looping through all mice in miceID array
                if code4 == miceID[i].code: # checking which mice has the same code
                    file.write('* checking which mice has the same code ' + str(datetime.datetime.now())+ '\n')
                    miceID[i] = Mice(code4, False) # set the isAllowed attribute to False
                    file.write('* set the isAllowed attribute to False ' + str(datetime.datetime.now())+ '\n')
                    gate1() 
                    file.write('* open gate 1 and set state to 1; repeat process with new mouse ' + str(datetime.datetime.now())+ '\n')
                    globalState = 1 # set globalState = 1 to repeat loop with another mouse.
    else:
            print 'something is wrong...'
            file.write('* Something is wrong ' + str(datetime.datetime.now())+ '\n')