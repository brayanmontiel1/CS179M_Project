from fileinput import filename
from tkinter import font
from turtle import heading
import PySimpleGUI as sg
import json
import datetime
import string



sg.theme('DefaultNoMoreNagging') 
#font 
global heading_font, body_font
#selectedJob : None = 0, Load/unload = 1, Balancing = 2 
global selectedJob
#global variables cor user, login time, and full name
global currUser, loginTime, fullName

#for themes
#https://www.reddit.com/r/Python/comments/dxule8/color_themes_pysimplegui_adds_significantly_more/

#importing users - users.json contains user info and login credentials
# Opening JSON file
heading_font = ("Arial, 24")
body_font = ("Arial, 14")
users_file = open('SAIL_Project/CS179M_Project/users.json')
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
    users_file = open('SAIL_Project/CS179M_Project/users.json')
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

#---------------LOGIN PAGE LAYOUT METHOD------------------------------
def login(users_array): #working --- needs touch up
    #currentUser : user that is logged in 
    #loginTime : date and time of login in military format
    #center items using columns : [sg.Column([ ], justification='center')]
    #adjust filename if needed for your pc -- Remember to change at production time
    my_img = sg.Image(filename='SAIL_Project/CS179M_Project/img/SaIL.png', key='-sail_logo-')
    
    layout =[
                [sg.Column([[my_img]], justification='center')],
                [sg.Column([[sg.Text('Enter username: ', font=body_font)]], justification='center')],  
                [sg.Column([[sg.Input(justification='center', key='-usrnm-')]], justification='center')], 
                [sg.Column([[sg.Button('Login'), sg.Button('Exit')]], justification='center')],
            ]

    window = sg.Window("SAIL ENTERPRISE - LOGIN", layout, size=(1000, 700), resizable=True, grab_anywhere=True, margins=(0, 0))

    while True:
        event,values = window.read()
        if event == "Exit" or event == sg.WIN_CLOSED:
            print('Exit message -- window closed')
            break ##change this back to menu page or login page depending if theres existing user
        else:
            if event == "Login":
                if values['-usrnm-'] in users_array: ##---sucessful login
                    currUser = values['-usrnm-']
                    fullName = getFullName(currUser)
                    loginTime = getTimeandDate()
                    print(fullName)
                    print(loginTime)
                    sg.popup("Welcome " , fullName) 
                    window.close()  ##close current window and start selectJob process
                    selectJob(currUser, fullName, loginTime)
                elif values['-usrnm-'] not in users_array: ##---invalid login
                    sg.popup("Invalid login. Try again")
            #break
    #selectJob(currUser, fullName, loginTime) -- have to figure out how to launch after login
    window.close()

#---------------JOB SELECTION LAYOUT METHOD------------------------------
def selectJob(currUser, fullName, loginTime): ##semi working --- need to format
    my_img = sg.Image(filename='SAIL_Project/CS179M_Project/img/SaIL.png', key='-sail_logo-')
    layout =[
                [sg.Column([[sg.Text('Current User: ' + fullName ,font=body_font)]], justification='left')],  
                [sg.Column([[sg.Text('Login Time: ' + str(loginTime), font=body_font)]], justification='left')],  
                [sg.Column([[my_img]], justification='center')],
                [sg.Column([[sg.Text('\n\nSelect an option below to continue: ', font=body_font)]], justification='center')],   
                [sg.Column([[sg.Button('Start New Load/Unload')]], justification='center')],  
                [sg.Column([[sg.Button('Start New Balancing Job')]], justification='center')],
                [sg.Column([[sg.Button('Login Another User')]], justification='center')],
            ]

    window = sg.Window("SAIL ENTERPRISE - Select Job", layout, size=(1000, 700), resizable=True, grab_anywhere=True, margins=(0, 0))
    trigger1 = 0
    while True:
        event = window.read()
        #selectedJob : Load/unload = 1, Balancing = 2
        # login just goes back to login screen 
        #  ^will use to know what job is selected at upload manifest layout
        if event == 'Start New Load/Unload':
            selectedJob = 1
            trigger1 = 1
            print('Start new load/unload -- forward to upload manifest/n')
            break
        elif event == 'Start New Balancing Job':
            selectedJob = 2
            trigger1 = 1
            print('Start new balancing job -- forward to upload manifest/n')
            break
        elif event == 'Login Another User': 
            print('forward to login screen')
            trigger1 = 2
            login(auth_users)  ##once user clicks cant go back unless login
        elif event == sg.WIN_CLOSED:
            print('Exit message -- window closed')
            break #exits below
    if trigger1 == 1:
        window.close()
        uploadManifest()
    elif trigger1 == 2:
        window.close()
        login(auth_users)
    elif trigger1 == 0:
        window.close()

    
    
    

#---------------JOB SELECTION LAYOUT METHOD------------------------------
def uploadManifest(): ##semi working --- need to format
    layout =[
                [sg.Column([[sg.Text('Current User: ' + fullName ,font=body_font)]], justification='left')],  
                [sg.Column([[sg.Text('Login Time: ' + str(loginTime), font=body_font)]], justification='left')],  
                [sg.Column([[sg.Text('\n\n Upload Manifest: ', font=heading_font)]], justification='center')],   
                [sg.Column([[sg.Text("Choose a file: "), sg.Input(), sg.FileBrowse(key="-manifest-")]], justification='center')],  
                [sg.Column([[sg.Button('Submit')]], justification='center')],
                [sg.Column([[sg.Button('Cancel')]], justification='center')],
            ]

    window = sg.Window("SAIL ENTERPRISE - Select Job", layout, size=(1000, 700), resizable=True, grab_anywhere=True, margins=(0, 0))

    while True:
        event = window.read()
        #selectedJob : Load/unload = 1, Balancing = 2, Login = 3 
        #  ^will use to know what job is selected at upload manifest layout
        if event == sg.WIN_CLOSED:
            break #exits below
        else:
            if event == "Submit":
                if selectedJob == 1:
                    sg.popup("Start balance loading job") #Placeholder - forward to load/unload layout
                elif selectedJob == 2: 
                    sg.popup("Start transfer job") #Placeholder - forward to balancing layout 
                break
            elif event == "Cancel":
                selectedJob = 0 #restore job selection
                window.close()  ##close current window and go back to selectJob layout
                selectJob(currUser, fullName, loginTime)
            break
    window.close()

#infinte running window -- have to CTRL+C then ENTER to exit program in terminal
""" while True:
    getTimeandDate()
    login(auth_users)
    #event, values = window.read()
    #print(event, values)
    #if event == None or event == 'Exit':     # If user closed window with X or if user clicked "Exit" button then exit
    #    break
    #window.close()   """

#REGULAR MAIN()
if __name__ == "__main__":
    login(auth_users)


