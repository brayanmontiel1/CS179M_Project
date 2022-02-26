from fileinput import filename
from tkinter import font
from turtle import heading
import PySimpleGUI as sg
import json
import datetime
import os
import string

from numpy import empty

#THIS IS THE FRONT END CODE FOR CS179 PROJECT IN ARTIFICAL INTELLIGENCE
#WINTER 2022 

sg.theme('DefaultNoMoreNagging') 
#font 
global heading_font, body_font
#selectedJob : None = 0, Load/unload = 1, Balancing = 2 
global selectedJob
#global variables incudes current user username, full name-
#login time and manifest name
global currUser, loginTime, fullName , manifest

heading_font = ("Arial, 24")
body_font = ("Arial, 14")
users_file = open('CS179M_Project/users.json')
# returns JSON object as 
# a dictionary
users_dict = json.load(users_file)
auth_users = []
for item in users_dict:     #append usernames to auth_user array
    credentials = item['username']
    auth_users.append(credentials)
users_file.close()
print(auth_users)

#---------------RETURNS USER FULL NAME METHOD------------------------
def getFullName(username):      ##working
    users_file = open('CS179M_Project/users.json')
    users_dict = json.load(users_file)
    full_name = "none"
    for item in users_dict:     #search for matching username to retrieve info
        if item['username'] == username:
            full_name = item['first'] + " " + item['last']
    users_file.close()
    return full_name

#---------------MILITARY TIME AND DATE METHOD------------------------
def getTimeandDate():   ##working
    today = datetime.datetime.now()
    date_time = today.strftime("%d-%m-%Y %H:%M:%S") ##military date DD-MM-YYYY clock 24hr
    #print(date_time)
    return date_time

#---------------INITIAL LOGIN USER METHOD------------------------------------
def login(): 
    #currUser : user that is logged in 
    #loginTime : date and time of login in military format
    #center items using columns : [sg.Column([ ], justification='center')]
    #adjust filename if needed for your pc -- Remember to change at production time
    my_img = sg.Image(filename='CS179M_Project/img/SaIL.png', key='-sail_logo-')
    
    layout =[
                [sg.Column([[my_img]], justification='center')],
                [sg.Column([[sg.Text('Enter username: ', font=body_font)]], justification='center')],  
                [sg.Column([[sg.Input(justification='center', key='-usrnm-')]], justification='center')], 
                [sg.Column([[sg.Button('Login'), sg.Button('Exit')]], justification='center')],
            ]
    return sg.Window("SAIL ENTERPRISE - Initial Login", layout, size=(1000, 700), resizable=True, grab_anywhere=True, margins=(0, 0), finalize=True)

#---------------SIGN OFF->ON NEW USER METHOD------------------------------------
def loginNew(): 
    #currUser : user that is logged in 
    #loginTime : date and time of login in military format
    #center items using columns : [sg.Column([ ], justification='center')]
    #adjust filename if needed for your pc -- Remember to change at production time
    my_img = sg.Image(filename='CS179M_Project/img/SaIL.png', key='-sail_logo-')
    
    layout =[
                [sg.Column([[sg.Text('Current User: ' + fullName ,font=body_font)]], justification='left')],  
                [sg.Column([[sg.Text('Login Time: ' + str(loginTime), font=body_font)]], justification='left')],  
                [sg.Column([[my_img]], justification='center')],
                [sg.Column([[sg.Text('Enter username: ', font=body_font)]], justification='center')],  
                [sg.Column([[sg.Input(justification='center', key='-usrnm-')]], justification='center')], 
                [sg.Column([[sg.Button('Login'), sg.Button('Go Back')]], justification='center')],
            ]
    return sg.Window("SAIL ENTERPRISE - New Login", layout, size=(1000, 700), resizable=True, grab_anywhere=True, margins=(0, 0), finalize=True)

#---------------JOB SELECTION METHOD------------------------------------
def selectJob(): 
    my_img = sg.Image(filename='CS179M_Project/img/SaIL.png', key='-sail_logo-')
    layout1 =[
                [sg.Column([[sg.Text('Current User: ' + fullName ,font=body_font)]], justification='left')],  
                [sg.Column([[sg.Text('Login Time: ' + str(loginTime), font=body_font)]], justification='left')],  
                [sg.Column([[my_img]], justification='center')],
                [sg.Column([[sg.Text('\n\nSelect an option below to continue: ', font=body_font)]], justification='center')],   
                [sg.Column([[sg.Button('Start New Load/Unload')]], justification='center')],  
                [sg.Column([[sg.Button('Start New Balancing Job')]], justification='center')],
                [sg.Column([[sg.Button('Login Another User')]], justification='center')],
            ]
    return sg.Window("SAIL ENTERPRISE - Select Job", layout1, size=(1000, 700), resizable=True, grab_anywhere=True, margins=(0, 0), finalize=True)

#---------------UPLOAD MANIFEST METHOD------------------------------------
def uploadManifest(): 
    layout =[
                [sg.Column([[sg.Text('Current User: ' + fullName ,font=body_font)]], justification='left')],  
                [sg.Column([[sg.Text('Login Time: ' + str(loginTime), font=body_font)]], justification='left')],  
                [sg.Column([[sg.Text('\n\n Upload Manifest: ', font=heading_font)]], justification='center')],   
                [sg.Column([[sg.Text("Choose a file: "), sg.Input(), sg.FileBrowse(key="-manifest-")]], justification='center')],  
                [sg.Column([[sg.Button('Submit Manifest')]], justification='center')],
                [sg.Column([[sg.Button('Cancel Upload')]], justification='center')],
            ]
    return sg.Window("SAIL ENTERPRISE - Upload Manifest", layout, size=(1000, 700), resizable=True, grab_anywhere=True, margins=(0, 0), finalize=True)

#---------------INTERACTIVE GRID METHOD------------------------------------
def gridSelection(): #NOT FINISHED 
    layout =[
                [sg.Column([[sg.Text('Current User: ' + fullName ,font=body_font)]], justification='left')],  
                [sg.Column([[sg.Text('Login Time: ' + str(loginTime), font=body_font)]], justification='left')],  
                [sg.Column([[sg.Text('Manifest: ' + str(manifest), font=body_font)]], justification='left')],  
                [sg.Column([[sg.Text('\nSelect Containers to Load/Unload: ', font=heading_font)]], justification='center')],   
                [sg.Column([[sg.Button(f'{row}, {col}') for col in range(12)] for row in range(8)], justification='center')],
                [sg.Column([[sg.Button('LOAD NEW CONTAINER')]], justification='center')],
                [sg.Column([[sg.Button('START PROCESS')]], justification='center')],
                [sg.Column([[sg.Button('BACK TO MENU')]], justification='center')],
            ]
    return sg.Window("SAIL ENTERPRISE - Grid View", layout, size=(1000, 700), resizable=True, grab_anywhere=True, margins=(0, 0), finalize=True)



###START OF WINDOW SELECTIONS ---------------------------------------------------------
window1, selectJobWindow, uploadWindow, gridWindow = login(), None, None, None   # start off with login window open (window 1)

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

    ##LOGIN process for initial and new user     
    if event == "Login":
        if values['-usrnm-'] in auth_users: ##---sucessful login
            currUser = values['-usrnm-']
            fullName = getFullName(currUser)
            loginTime = getTimeandDate()
            print("Full Name: ", fullName)
            print("Username: ", currUser)
            print("Login Time: ",loginTime)
            print('Login Successful - Foward to JOB SELECTION')
            sg.popup("Welcome!" , fullName) 
            window1.Hide()
            selectJobWindow = selectJob()       #REDIRECT to job selection window
        elif values['-usrnm-'] not in auth_users: ##---invalid login
            sg.popup("Invalid Login. Try again")  
    ##goes back if dont want to sign in new user
    elif event == 'Go Back':
        print('Login Canceled - Return to JOB SELECTION')
        window1.Hide()
        selectJobWindow.UnHide() ##show job selection window for current user again
    
    ##JOB SELECTION process
    elif event == 'Start New Load/Unload':
        selectedJob = 1
        selectJobWindow.Hide() #closes job selection window
        print('LOAD/UNLOAD -- Forward to UPLOAD MANIFEST/n')
        selectJobWindow.Hide() 
        uploadWindow = uploadManifest()
    elif event == 'Start New Balancing Job':
        selectedJob = 2
        print('BALANCING -- Forward to UPLOAD MANIFEST/n')
        selectJobWindow.Hide()
        uploadWindow = uploadManifest()
    elif event == 'Login Another User':     ##REDIRECT to main login
        print('Forward to LOGIN screen')
        selectJobWindow.Hide() 
        window1 = loginNew()   #load login window

    ##UPLOAD manifest process
    elif event == "Submit Manifest":
        manifest = values['-manifest-'] #save manifest name
        if(manifest == ''):
            print("INVALID MANIFEST - Pop message to try again.")
            sg.popup("Empty selection, try again.") #Error message if empty
        else:
            manifest = os.path.basename(manifest)
            print('SELECTED MANIFEST : ', manifest)
            if selectedJob == 1:
                sg.popup("Starting new Loading Job") #Placeholder - forward to load/unload layout
                fileM = open(values['-manifest-'])
                line = fileM.read()      
                fileM.close()
                print(line)  
                gridWindow = gridSelection()
                uploadManifest().Hide()
            elif selectedJob == 2: 
                sg.popup("Start new Balancing Job") #Placeholder - forward to balancing layout 
    elif event == "Cancel Upload":
        print("CANCLED Manifest upload - RETURN to Job Selection")
        selectedJob = 0 #restore job selection
        uploadWindow.Hide()
        selectJobWindow.UnHide()

    ##GRID WINDOW process
    elif event == 'LOAD NEW CONTAINER':
        sg.popup("new cont. placeholder")        
        print('ADD NEW CONTAINER -- Forward to load new container layout/n')
    elif event == 'Start New Balancing Job':
        sg.popup("new cont. placeholder")        
        print('STARTING ALGORITHM -- Forward to algorithm loading screen/n')
    elif event == 'BACK TO MENU':     ##REDIRECT to main login
        print('RETURN TO JOB SELECTION -- Forward to job selection menu')
        gridWindow.Hide() 
        selectJobWindow.UnHide()

window.close()
