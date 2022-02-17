import PySimpleGUI as sg
import json
import datetime
import string



sg.theme('DefaultNoMoreNagging') 
#for themes
#https://www.reddit.com/r/Python/comments/dxule8/color_themes_pysimplegui_adds_significantly_more/

#importing users - users.json contains user info and login credentials
# Opening JSON file
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
    global currUser, loginTime, fullName
    #adjust filename if needed for your pc -- Remember to change at production time
    my_img = sg.Image(filename='SAIL_Project/CS179M_Project/img/SaIL.png', key='-sail_logo-')
    
    layout =[
                [sg.Column([[my_img]], justification='center')],
                [sg.Column([[sg.Text('Log In:', font=40)]], justification='center')],   
                [sg.Column([[sg.Input(justification='center', key='-usrnm-')]], justification='center')], 
                [sg.Column([[sg.Button('Login'), sg.Button('Cancel')]], justification='center')],
            ]

    window = sg.Window("SAIL ENTERPRISE - LOGIN", layout, size=(1000, 700), resizable=True, grab_anywhere=True, margins=(0, 0))

    while True:
        event,values = window.read()
        if event == "Cancel" or event == sg.WIN_CLOSED:
            break ##change this back to menu page or login page depending if theres existing user
        else:
            if event == "Login":
                if values['-usrnm-'] in users_array: ##---sucessful login
                    currUser = values['-usrnm-']
                    fullName = getFullName(currUser)
                    loginTime = getTimeandDate
                    print(fullName)
                    print(loginTime)
                    sg.popup("Welcome " , fullName) 
                    break
                elif values['-usrnm-'] not in users_array: ##---invalid login
                    sg.popup("Invalid login. Try again")
            break
    #selectJob(currUser, fullName, loginTime) -- have to figure out how to launch after login
    window.close()

def selectJob(currUser, fullName, loginTime): ##semi working --- need to format
    global selectedJob
    my_img = sg.Image(filename='SAIL_Project/CS179M_Project/img/SaIL.png', key='-sail_logo-')
    
    layout =[
                [sg.Column([[sg.Text('Current User:', fullName)]], justification='left')],  
                [sg.Column([[sg.Text('Login Time:', loginTime)]], justification='left')],  
                [sg.Column([[my_img]], justification='center')],
                [sg.Column([[sg.Text('Select an option below to continue:')]], justification='center')], 
                [sg.Column([[sg.Button('Start New Load/Unload')]], justification='center')],  
                [sg.Column([[sg.Button('Start New Balancing Job')]], justification='center')],
                [sg.Column([[sg.Button('Login')]], justification='center')],
            ]

    window = sg.Window("SAIL ENTERPRISE - Select Job", layout, size=(1000, 700), resizable=True, grab_anywhere=True, margins=(0, 0))

    while True:
        event = window.read()
        #selectedJob : Load/unload = 1, Balancing = 2, Login = 3 
        #  ^will use to know what job is selected at upload manifest layout
        if event == sg.WIN_CLOSED:
            break #exits below
        else:
            if event == "Start New Load/Unload":
                sg.popup("Starting New Load/Unload Job") #Placeholder - forward to upload manifest
            elif event == "Start New Balancing Job":
                sg.popup("Starting New Load/Unload Job") #Placeholder - forward to upload manifest
            elif event == "Login": 
                login(auth_users) #adjust to wait for another choice if login page has cancel(in login)
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
    getTimeandDate()
    login(auth_users) 
    selectJob(currUser, fullName, loginTime)


