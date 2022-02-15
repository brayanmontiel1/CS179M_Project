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

#gets full name of user based on username 
def getFullName(username):      ##working
    users_file = open('SAIL_Project/CS179M_Project/users.json')
    users_dict = json.load(users_file)
    full_name = "none"
    for item in users_dict:     #search for matching username to retrieve info
        if item['username'] == username:
            full_name = item['first'] + " " + item['last']
    users_file.close()
    return full_name

#returns time and date in military format-ish
def getTimeandDate():   ##working
    today = datetime.datetime.now()
    date_time = today.strftime("%d-%m-%Y %H:%M:%S") ##military date DD-MM-YYYY clock 24hr
    #print(date_time)
    return date_time

def login(users_array): ##semi working --- need to format
    #currentUser = user that is logged in 
    #loginTime = date and time of login in military format
    global currentUser, loginTime 
    layout = [[sg.Text('Log In', justification='center', size =(15, 1), font=40)],
            [sg.Text("Username", size =(15, 1), font=16), sg.InputText(key='-usrnm-', font=16)],
            [sg.Button('Login'),sg.Button('Cancel')]]

    window = sg.Window("SAIL ENTERPRISE - LOGIN", layout, size=(900, 600), resizable=True)

    while True:
        event,values = window.read()
        if event == "Cancel" or event == sg.WIN_CLOSED:
            break ##change this back to menu page or login page depending if theres existing user
        else:
            if event == "Login":
                if values['-usrnm-'] in users_array:
                    currentUser = values['-usrnm-']
                    fullName = getFullName(currentUser)
                    loginTime = getTimeandDate
                    print(fullName)
                    print(loginTime)
                    sg.popup("Welcome " , fullName)  ##change this to menu page window 
                    break
                elif values['-usrnm-'] not in users_array:
                    sg.popup("Invalid login. Try again")
            break
    window.close()


#code below sourced from [1] in Reference.txt as inspo for layouts
# ----------- Create the 3 layouts this Window will display -----------
layout1 = [[sg.Text('Login Page')],
              [sg.Text('Username: '), sg.Input()]]

layout2 = [[sg.Text('This is layout 2')],
           [sg.Input(key='-IN-')],
           [sg.Input(key='-IN2-')]]

layout3 = [[sg.Text('This is layout 3 - It is all Radio Buttons')],
           *[[sg.R(f'Radio {i}', 1)] for i in range(8)]]

# ----------- Create actual layout using Columns and a row of Buttons
layout = [[sg.Column(layout1, key='-COL1-'), sg.Column(layout2, visible=False, key='-COL2-'), sg.Column(layout3, visible=False, key='-COL3-')],
          [sg.Button('Cycle Layout'), sg.Button('1'), sg.Button('2'), sg.Button('3'), sg.Button('Exit')]]

window = sg.Window('SAIL ENTERPRISE', layout, size=(900, 600), resizable=True)

layout = 1  # The currently visible layout
while True:
    getTimeandDate()
    login(auth_users)
    event, values = window.read()
    print(event, values)
    if event == None or event == 'Exit':     # If user closed window with X or if user clicked "Exit" button then exit
        break
    window.close()  