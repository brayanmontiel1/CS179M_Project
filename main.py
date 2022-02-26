from fileinput import filename
from tkinter import font
from turtle import heading
import PySimpleGUI as sg
import json
import datetime
import os
import string
import heapq
import datetime
import numpy as np
from numpy import empty

sg.theme('DefaultNoMoreNagging') 

global heading_font, body_font # fonts
heading_font = ("Arial, 24")
body_font = ("Arial, 14")

global entryCount # tie breaker for states with equal priority
global containerNum # tracks unique containers

global currUser # Global variable to store currently logged in user
file = open(".saved/currentUser.txt", "r") # saved file holds currently logged in user (for power failure)
currUser = file.read()

#---------------CLASSES------------------------------------
class Container(object):
    # container.weight
    # container.desc
    pass

class LUstate(object):
    # state.ship
    # state.g
    # state.h
    # state.cranePos
    # state.loads
    # state.unloads
    # state.moves
    pass

#---------------GENERAL PROGRAM FUNCTIONS------------------------------------
def addLog(logText): # Appends whatever is in logText to appropriate text file, automatic timestamp
    time = datetime.datetime.now()
    time = time.strftime("%H:%M:%S")
    date = datetime.date.today()
    monthDay = date.strftime("%m-%d")
    year = date.strftime("%Y")
    text = monthDay + "-" + year + ": " + time + " " + logText + "\n"
    logFile = "logs/" + year + "LOG.txt"
    file = open(logFile, "a")
    file.write(text)
    file.close()

def login(userName): # Updates global variable 'currUser' with userName, adds logs
    global currUser
    if currUser == userName:
        return
    if currUser != "":
        addLog(currUser + " signs out")
    addLog(userName + " signs in")
    currUser = userName
    file = open(".saved/currentUser.txt", "w")
    file.write(currUser)
    file.close()

def loadManifest(filename): # COMPLETE: loads 2D array with manifest
    # track container numbers
    global containerNum
    containerNum = 1
    # make 2D array (10 row x 12 col)
    manifest = np.empty([10, 12], dtype = Container)
    # open the file
    file = open(filename, 'r')
    f = file.readlines()
    # for each line in the file
    try:
        for line in f:
            # get attributes in a container struct
            c = Container()
            c.weight = int(line[10:15])
            #making sure we do not take in new line characters in the description
            if(line[-1] == '\n'):
                c.desc = line[18:-1]
            else:
                #the last line in the file will not have a new line character
                c.desc = line[18:]

            # assign unique num to containers
            if(c.desc != "UNUSED" and c.desc != "NAN"):
                c.num = containerNum
                containerNum+=1
            elif(c.desc == "NAN"):
                c.num = -1
            else:
                c.num = 0

            # use position in file to fill in array with the container you just made
            #row = int(line[4:6])
            #col = int(line[1:3])
            manifest[int(line[1:3]) - 1][int(line[4:6]) - 1] = c

        #populate virtual area with unused container spaces
        for col in range(8, 10):
            for row in range(0, 12):
                c = Container()
                c.weight = 0
                c.desc = "UNUSED"
                c.num = -1
                manifest[col][row] = c

    except:
        return np.empty([10, 12], dtype = Container)

    # return array
    return manifest

#---------------LOGIN WINDOW------------------------------------
def loginWindow(): 
    #currUser : user that is logged in 
    #center items using columns : [sg.Column([ ], justification='center')]
    #adjust filename if needed for your pc -- Remember to change at production time
    my_img = sg.Image(filename='img/SaIL.png', key='-sail_logo-')
    
    layout =[
                [sg.Column([[my_img]], justification='center')],
                [sg.Column([[sg.Text('Enter username: ', font=body_font)]], justification='center')],  
                [sg.Column([[sg.Input(justification='center', key='-usrnm-')]], justification='center')], 
                [sg.Column([[sg.Button('Login'), sg.Button('Exit')]], justification='center')],
            ]
    return sg.Window("SAIL ENTERPRISE - Initial Login", layout, size=(1000, 700), resizable=True, grab_anywhere=True, margins=(0, 0), finalize=True)

#---------------JOB SELECTION METHOD------------------------------------
def selectJob(): 
    my_img = sg.Image(filename='img/SaIL.png', key='-sail_logo-')
    layout1 =[
                [sg.Column([[sg.Text('Current User: ' + currUser ,font=body_font)]], justification='left')],   
                [sg.Column([[my_img]], justification='center')],
                [sg.Column([[sg.Text('\n\nSelect an option below to continue: ', font=body_font)]], justification='center')],   
                [sg.Column([[sg.Button('Start New Load/Unload')]], justification='center')],  
                [sg.Column([[sg.Button('Start New Balancing Job')]], justification='center')],
                [sg.Column([[sg.Button('New Login')]], justification='center')],
            ]
    return sg.Window("SAIL ENTERPRISE - Select Job", layout1, size=(1000, 700), resizable=True, grab_anywhere=True, margins=(0, 0), finalize=True)

#---------------UPLOAD MANIFEST METHOD------------------------------------
def uploadManifest(): 
    layout =[
                [sg.Column([[sg.Text('Current User: ' + currUser ,font=body_font)]], justification='left')],    
                [sg.Column([[sg.Text('\n\n Upload Manifest: ', font=heading_font)]], justification='center')],   
                [sg.Column([[sg.Text("Choose a file: "), sg.Input(), sg.FileBrowse(key="-manifest-")]], justification='center')],  
                [sg.Column([[sg.Button('Submit Manifest')]], justification='center')],
                [sg.Column([[sg.Button('Cancel Upload')]], justification='center')],
            ]
    return sg.Window("SAIL ENTERPRISE - Upload Manifest", layout, size=(1000, 700), resizable=True, grab_anywhere=True, margins=(0, 0), finalize=True)

#---------------INTERACTIVE GRID METHOD------------------------------------
def gridSelection(): #NOT FINISHED 
    layout =[
                [sg.Column([[sg.Text('Current User: ' + currUser ,font=body_font)]], justification='left')],  
                [sg.Column([[sg.Text('Ship: ' + str(shipName), font=body_font)]], justification='left')],  
                [sg.Column([[sg.Text('\nSelect Containers to Load/Unload: ', font=heading_font)]], justification='center')],   
                [sg.Column([[sg.Button(f'{row}, {col}') for col in range(1,13)] for row in range(8,0,-1)], justification='center')],
                [sg.Column([[sg.Button('LOAD NEW CONTAINER')]], justification='center')],
                [sg.Column([[sg.Button('START')]], justification='center')],
            ]
    return sg.Window("SAIL ENTERPRISE - Grid View", layout, size=(1000, 700), resizable=True, grab_anywhere=True, margins=(0, 0), finalize=True)

#--------------------MAIN EVENT LOOP---------------------------------------------------------
window1, selectJobWindow, uploadWindow, gridWindow = None, selectJob(), None, None   # start off with main window open (fix to be with whatever is saved)

while True:             # Event Loop
    window, event, values = sg.read_all_windows()
    if event == sg.WIN_CLOSED or event == 'Exit':
        window.close()
        if window == selectJobWindow:       # if closing selectJobWindow, mark as closed
            selectJobWindow = None
            break
        elif window == uploadWindow:       
            uploadWindow = None
            break
        elif window == gridWindow:       
            gridWindow = None
            break
        elif window == window1:     # if closing win 1, exit program
            break
   
    # LOGIN Process
    if event == "Login": # login button on login window
        login(values['-usrnm-']) # updates currUser and logs sign in/off
        print("Username:", currUser)
        print('Login Successful - Foward to JOB SELECTION')
        window1.Hide()
        selectJobWindow = selectJob() # REDIRECT to job selection window

    elif event == 'Go Back': # Go back button on login window
        print('Login Canceled - Return to JOB SELECTION')
        window1.Hide()
        selectJobWindow.UnHide() # show job selection window for current user again
    
    # JOB SELECTION process
    elif event == 'Start New Load/Unload': # LU job select button on main window
        selectedJob = 1
        print('LOAD/UNLOAD -- Forward to UPLOAD MANIFEST/n')
        selectJobWindow.Hide() #closes job selection window
        uploadWindow = uploadManifest()

    elif event == 'Start New Balancing Job': # Balance job select button on main window
        selectedJob = 2
        print('BALANCING -- Forward to UPLOAD MANIFEST/n')
        selectJobWindow.Hide()
        uploadWindow = uploadManifest()

    elif event == 'New Login': # Login button on main window
        print('Forward to LOGIN screen')
        selectJobWindow.Hide() 
        window1 = loginWindow()   #load login window

    # UPLOAD manifest process
    elif event == "Submit Manifest": # submit manifest button on upload window
        manifest = values['-manifest-'] # get input
        if(manifest == ''):
            print("INVALID MANIFEST - Pop message to try again.")
            sg.popup("Empty Selection, try again.") # Error message if empty
        else:
            ship = loadManifest(manifest) # load manifest into array
            if(ship[0][0] == None):
                sg.popup("Invalid manifest file, try again.") # Error message if mainfest file invalid
            else:
                manifest = os.path.basename(manifest) # get manifest file name
                addLog("Manifest " + manifest + " is opened, there are " + str(containerNum-1) + " containers on the ship") # push log
                shipName = manifest[:-4] # remove ".txt" from manifest to get ship name
                print('SELECTED MANIFEST : ', manifest)
                if selectedJob == 1:
                    gridWindow = gridSelection() # open grid slection if LU job
                    uploadManifest().Hide()
                elif selectedJob == 2: 
                    sg.popup("Start new Balancing Job") #Placeholder - forward to balancing layout 

    elif event == "Cancel Upload": # cancel upload button on upload window
        print("CANCLED Manifest upload - RETURN to Job Selection")
        selectedJob = 0 # restore job selection
        uploadWindow.Hide()
        selectJobWindow.UnHide()

    # GRID WINDOW process
    elif event == 'LOAD NEW CONTAINER':
        sg.popup("new cont. placeholder")        
        print('ADD NEW CONTAINER -- Forward to load new container layout/n')
    elif event == 'Start New Balancing Job':
        sg.popup("new cont. placeholder")        
        print('STARTING ALGORITHM -- Forward to algorithm loading screen/n')

window.close()