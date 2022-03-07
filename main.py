from audioop import add
from email import message
from fileinput import filename
from tkinter import font
from turtle import heading
import PySimpleGUI as sg
import json
import datetime
import os
import string
import heapq
import io, sys
import numpy as np
from numpy import empty

sg.theme('DefaultNoMoreNagging') 

global heading_font, body_font # fonts
heading_font = ("Arial, 24")
body_font = ("Arial, 14")

global entryCount # tie breaker for states with equal priority
global containerNum # tracks unique containers
global loads, unloads # tracks loads unloads before job starts
global loadedMsg, manifestCont #tracks what has been selected / deselected and manifest content
global currUser # Global variable to store currently logged in user
#file = open("CS179M_Project/.saved/currentUser.txt", "r") # saved file holds currently logged in user (for power failure)
file = open((os.path.join(os.path.dirname(os.path.abspath(__file__)), '.saved', 'currentUser.txt')),'r')
currUser = file.read()
loadedMsg = ''
manifestCont = ''
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
    #logFile = "CS179M_Project/logs/" + year + "LOG.txt"
    file = open((os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs', '{}LOG.txt'.format(year))),'a')
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
    #file = open("CS179M_Project/.saved/currentUser.txt", "w")
    file = open((os.path.join(os.path.dirname(os.path.abspath(__file__)), '.saved', 'currentUser.txt')),'w')
    file.write(currUser)
    file.close()

def loadManifest(filename): # loads 2D array with manifest
    # track container numbers
    global containerNum
    containerNum = 1
    # make 2D array (10 row x 12 col)
    manifest = np.empty([10, 12], dtype = Container)
    try:
        # open the file
        file = open(filename, 'r')
        f = file.readlines()
        # for each line in the file
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
                c.num = 0
                manifest[col][row] = c

    except:
        return np.empty([10, 12], dtype = Container)

    # return array
    return manifest

def grid2Manifest(ship, filename): # uploads 2D array into manifest format

    # Format ship object into list
    manifestList = []
    for i in range(len(ship) - 2):
        for j in range(len(ship[0])):

            item_num = ''
            mynum = ship[i][j].num
            if mynum == 0:
                item_num = 'UNUSED'

            elif mynum == -1:
                item_num = 'NAN'

            elif mynum > 0:
                item_num = ship[i][j].desc

            manifestList.append(([i+1, j+1], (ship[i][j]).weight,item_num))

    # Write each list row to text file
    textfile = open(filename, "w")
    for element in manifestList:
        if element[0][0] == 8 and element[0][1] == 12:
            textfile.write('[{:02d},{:02d}], {{{:05d}}}, {}'.format(element[0][0], element[0][1], element[1], element[2]))
        else:
            textfile.write('[{:02d},{:02d}], {{{:05d}}}, {}\n'.format(element[0][0], element[0][1], element[1], element[2]))
    textfile.close()
    print('NEW MANIFEST DOWNLOAD READY : {}'.format(filename))

#---------------LU MAIN FUNCTIONS------------------------------------
def LUjob(ship,loads,unloads): # initalizes state and computes the goal for LU
    initState = LUstate()
    initState.ship = ship
    initState.loads = loads
    initState.unloads = unloads
    initState.cranePos = (-1,-1) # crane starts on dock by truck
    LUheuristic(initState)
    initState.g = 0
    initState.moves = []
    return LUsearch(initState)

def LUsearch(initState): # A* search for LU jobs
    global entryCount
    entryCount = 0
    q = [] # priority queue
    heapq.heappush(q, ((initState.g + initState.h), entryCount, initState)) # push initial state onto queue
    entryCount+=1

    checkedStates = [] # hold checked states

    while (len(q) > 0): # Loop while queue is not empty
        item = heapq.heappop(q)
        curState = item[2] # get current state

        if(LUstateCheck(curState, checkedStates)): # so we dont expand states we already expanded
            continue

        if (curState.h == 0): # Test if state is the goal (all unloads gone, no loads left, no containers in temp space)
            return curState # return state as solution if true
        else:
            LUexpand(curState, q) # expand state if false

        checkedStates.append(curState) # add state to checked states

    print("No Solution") # print error if no solution
    return

def LUexpand(state, q): # expands given state for LU job
    global entryCount
    tops = findTops(state)
    for j in range(12): # for each column
        i = tops[j] # get row of container to move
        if(i < 0): # no containers in that column
            continue
        if((i,j) in state.unloads): # container is an unload
            copy = LUstateCopy(state)
            copy.unloads.remove((i,j)) # remove container from unloads
            if(copy.cranePos == (-1,-1)): # check if crane is by truck
                copy.g += (abs(i-8) + abs(j-0) + 2)
            else: # move crane to container position
                copy.g += manhattenDist(copy.cranePos[0],copy.cranePos[1],i,j,tops)
            copy.g += (abs(i-8) + abs(j-0) + 2) # add distance to unload container to g
            copy.cranePos = (-1,-1) # leave cranePos at the truck
            copy.ship[i][j].weight = 0 # move container
            copy.ship[i][j].desc = "UNUSED"
            copy.ship[i][j].num = -1
            copy.moves.append((i,j,"Truck")) # track move
            LUheuristic(copy) # calculate new heuristic
            heapq.heappush(q, ((copy.g + copy.h), entryCount, copy)) # push copy to queue
            entryCount+=1
        else: # container is not an unload
            for c in range(12): # for every other column
                if (c != j):
                    r = tops[c]+1 # get row location of move (1 above the top)
                    if((r < 10) and (state.ship[i][j].desc != "NAN")): # Check that the col is not the max col height or top container is NAN
                        copy = LUstateCopy(state)
                        if(copy.cranePos == (-1,-1)): # check if crane is by truck
                            copy.g += (abs(i-8) + abs(j-0) + 2)
                        else: # move crane to container position
                            copy.g += manhattenDist(copy.cranePos[0],copy.cranePos[1],i,j,tops)
                        copy.g += manhattenDist(i,j,r,c,tops) # add cost of move to g
                        copy.cranePos = (r,c) # leave crane at dropoff position
                        copy.ship[r][c].weight = copy.ship[i][j].weight # move container
                        copy.ship[r][c].desc = copy.ship[i][j].desc
                        copy.ship[r][c].num = copy.ship[i][j].num
                        copy.ship[i][j].weight = 0
                        copy.ship[i][j].desc = "UNUSED"
                        copy.ship[i][j].num = -1
                        copy.moves.append((i,j,r,c))
                        LUheuristic(copy) # calculate new heuristic
                        heapq.heappush(q, ((copy.g + copy.h), entryCount, copy)) # push copy to queue
                        entryCount+=1
    if (len(copy.loads) > 0): # load a container to every column
        for c in range(12): # for every column
            r = tops[c]+1 # get placement location (1 above top)
            if(r < 10): # Check that the col is not the max col height
                copy = LUstateCopy(state)
                if(copy.cranePos != (-1,-1)): # check if crane is not by truck
                    copy.g += (abs(copy.cranePos[0]-8) + abs(copy.cranePos[1]-0) + 2) # move crane to truck position
                copy.g += (abs(r-8) + abs(c-0) + 2) # add cost of load to g
                copy.cranePos = (r,c) # leave crane at dropoff position
                copy.ship[r][c].weight = copy.loads[-1].weight # move container
                copy.ship[r][c].desc = copy.loads[-1].desc
                copy.ship[r][c].num = copy.loads[-1].num
                copy.loads = copy.loads[:-1] # remove container from loads
                copy.moves.append(("Truck",r,c)) # track move   
                LUheuristic(copy) # calculate new heuristic
                heapq.heappush(q, ((copy.g + copy.h), entryCount, copy)) # push copy to queue
                entryCount+=1

def LUheuristic(state): # COMPLETE: find h(n) of a given LUstate, store in state parameter automatically
    tops = findTops(state)
    ship = state.ship
    tempPos = state.cranePos
    h = 0
    for j in range(12): # for each col
        for i in range(tops[j]+1): # for each row with filled containers
            if((i,j) in state.unloads): # check if container needs to be unloaded
                for k in range(tops[j],i-1,-1): # for the rest of the containers from top to found unload
                    if(tempPos == (-1,-1)):
                        h+=(abs(k-8) + abs(j-0) + 2) # move crane from truck to container
                    else:
                        h+=(abs(k-tempPos[0]) + abs(j-tempPos[1])) # move crane to container

                    if((k,j) in state.unloads): # if container is unload, add unload dist
                        h+=(abs(k-8) + abs(j-0) + 2) # move container to truck
                        tempPos = (-1,-1) # set crane position at truck
                    else: # if not, add nearest distance that does not overestimate
                        pos = nearestDistPos(k,j,tops)
                        h+=(abs(pos[0]-tempPos[0]) + abs(pos[1]-tempPos[1]))
                        tempPos = pos
                break

    for i in range(8,10):
        for j in range(12):
            if(ship[i][j].desc != "UNUSED"):
                h+=nearestTempRemoval(i,j,tops) # add nearest distance to column not reaching into temp rows

    h+=(len(state.loads)*nearestLoadDist(tops)) # add nearest distance to load container for each container in loads

    state.h = h

#---------------LU HELPER FUNCTIONS------------------------------------
def nearestDistPos(r,c,tops): # finds nearest distance to remove container without overestimating
    if(c == 0): # first column
        if(tops[c+1]+1 >= r): # if column 2 on par or above, nearest is on top of that column
            return (tops[c+1]+1,c+1)
        else: # else, just move one over (estimating on columns lower may overestimate)
            return (r,c+1)
    if(c == 11): # last column
        if(tops[c-1]+1 >= r): # if column 11 on par or above, nearest is on top of that column
            return (tops[c-1]+1,c-1)
        else: # else, just move one over (estimating on columns lower may overestimate)
            return (r,c-1)
    if((tops[c+1]+1 >= r) and (tops[c-1]+1 >= r)): # if both columns taller, estimate by top of shorter column
        if(tops[c-1] >= tops[c+1]): # find shorter column, return that position
            return (tops[c+1]+1,c+1)
        else: 
            return (tops[c-1]+1,c-1)
    else: # if not, just move one over so we dont overestimate
        return (r,c+1)

def nearestTempRemoval(i,j,tops): # finds nearest distance to column position not in temp row
    min = float('inf')
    for k in range(12):
        if(tops[k]+1 < 8): # column has an empty space not in temp row
            val = (abs(7-i) + abs(k-j)) # place in top space (so we dont overestimate)
            if val < min:
                min = val
    return min # return which column provides minimum

def nearestLoadDist(tops): # finds nearest manhatten to place container being loaded
    min = float('inf')
    for j in range(12):
        val = ((abs((tops[j]+1)-8)) + abs(j-0) + 2)
        if val < min:
            min = val
    return min

def LUstateCopy(state): # Copies an LU state
    copy = LUstate() # set up copy state
    copy.h = state.h
    copy.g = state.g

    copy.ship = [] # copies ship state with container copy
    for i in range(10):
        row = []
        for j in range(12):
            row.append(containerCopy(state.ship[i][j]))
        copy.ship.append(row)

    copy.loads = [] # copies containers in the load array with container copy
    for i in range(len(state.loads)):
        copy.loads.append(containerCopy(state.loads[i]))
    
    copy.unloads = state.unloads.copy() # unload array is tuples, so this works
    copy.moves = state.moves.copy() # moves array is tuples, so this works
    copy.cranePos = state.cranePos

    return copy

def LUstateCheck(state, checkedStates): # checks if state and states in list are equivolent (ignoring h and g values)
    ship = state.ship
    for i in range(len(checkedStates)): # for all checked states
        curState = checkedStates[i]
        if(len(state.loads) != len(curState.loads)): # states have unequal loads, not equivolent
            continue
        if(len(state.unloads) != len(curState.unloads)): # states have unequal unloads, not equivolent
            continue
        curShip = curState.ship
        same = True
        for j in range(10):
            for k in range(12): # for every container on the ship
                if(ship[j][k].num != curShip[j][k].num): # containers are not equivolent, so state is not the same
                    same = False
        if(same): # if same, return true
            return True
        else: # else keep checking
            continue
    return False # return false if all checked states are different from states

#---------------GENERAL HELPER FUNCTIONS------------------------------------
def manhattenDist(r1,c1,r2,c2,tops): # Manhatten distance between inital indexes and final indexs, taking into account you cant pass through containers
    maxHeight = -1
    if(c1 > c2):
        for c in range(c2,c1):
            if(tops[c]+1 > maxHeight):
                maxHeight = tops[c]+1 # find max height in between columns
    else:
        for c in range(c1+1,c2+1):
            if(tops[c]+1 > maxHeight):
                maxHeight = tops[c]+1 # find max height in between columns
    if(maxHeight <= r1): # dont need to go up to max height, just over and down
        return (abs(r1-r2) + abs(c1-c2))
    else:
        d = 0
        d+=(maxHeight-r1) # go up to max height
        d+=abs(c1-c2) # go over to correct column
        d+=(maxHeight-r2) # go down to correct row
        return d

def findTops(state): # find the top containers of every row (includes NAN containers if applicable)
    ship = state.ship
    tops = []
    for j in range(12): # for each col
        for i in range(9,-1,-1): # for each row top down
            if (ship[i][j].desc != "UNUSED"):
                tops.append(i) # append the first actual container and break
                break
        if(len(tops) != (j+1)): # if the whole column is empty, -1 index
            tops.append(-1)
    return tops

def containerCopy(container): # Copies a Container
    copy = Container()
    copy.weight = container.weight
    copy.desc = container.desc
    copy.num = container.num
    return copy

def movesList(state): # Prints a states move list
    moves = state.moves
    for i in range(len(moves)):
        if(len(moves[i]) == 4):
            print("[%d,%d] to [%d,%d]"%(moves[i][0]+1,moves[i][1]+1,moves[i][2]+1,moves[i][3]+1))
            continue
        if(moves[i][0] == "Truck"):
            print("%s to [%d,%d]"%(moves[i][0],moves[i][1]+1,moves[i][2]+1))
        else:
            print("[%d,%d] to %s"%(moves[i][0]+1,moves[i][1]+1,moves[i][2]))
    print(state.g,"minutes")

def retrieveInds(moves,currMove): # turns tuples of moves into useable indexes
    tup = moves[currMove]
    if len(tup) == 4:
        return tup[0],tup[1],tup[2],tup[3]
    elif len(tup) == 3 and tup[0] == "Truck":
        return -1,-1,tup[1],tup[2]
    else:
        return tup[0],tup[1],-1,-1

#---------------LOGIN WINDOW------------------------------------
def loginWindow(): 
    #currUser : user that is logged in 
    #center items using columns : [sg.Column([ ], justification='center')]
    #adjust filename if needed for your pc -- Remember to change at production time
    #my_img = sg.Image(filename='CS179M_Project/img/SaIL.png', key='-sail_logo-')
    my_img = sg.Image(filename=(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img', 'SaIL.png')), key='-sail_logo-')
    
    layout =[
                [sg.Column([[my_img]], justification='center')],
                [sg.Column([[sg.Text('Enter username: ', font=body_font)]], justification='center')],  
                [sg.Column([[sg.Input(justification='center', key='-usrnm-')]], justification='center')], 
                [sg.Column([[sg.Button('Login'), sg.Button('Cancel')]], justification='center')],
            ]
    return sg.Window("SAIL ENTERPRISE - Login", layout, size=(1000, 700), resizable=True, grab_anywhere=True, margins=(0, 0), finalize=True)

#---------------JOB SELECTION METHOD------------------------------------
def selectJob(): 
    #my_img = sg.Image(filename='CS179M_Project/img/SaIL.png', key='-sail_logo-')
    my_img = sg.Image(filename=(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img', 'SaIL.png')), key='-sail_logo-')
    layout1 =[
                [sg.Column([[sg.Text('Current User: ' + currUser ,font=body_font)]], justification='left')],   
                [sg.Column([[my_img]], justification='center')],
                [sg.Column([[sg.Text('\n\nSelect an option below to continue: ', font=body_font)]], justification='center')],   
                [sg.Column([[sg.Button('Start New Load/Unload')]], justification='center')],  
                [sg.Column([[sg.Button('Start New Balancing Job')]], justification='center')],
                [sg.Column([[sg.Button('Login')]], justification='center')],
            ]
    return sg.Window("SAIL ENTERPRISE - Select Job", layout1, size=(1000, 700), resizable=True, grab_anywhere=True, margins=(0, 0), finalize=True)

#---------------UPLOAD MANIFEST METHOD------------------------------------
def uploadManifest(): 
    layout =[
                [sg.Column([[sg.Text('Current User: ' + currUser ,font=body_font)]], justification='left')],    
                [sg.Column([[sg.Text('\n\n Upload Manifest: ', font=heading_font)]], justification='center')],   
                [sg.Column([[sg.Text("Choose a file: "), sg.Input(), sg.FileBrowse(key="-manifest-")]], justification='center')],  
                [sg.Column([[sg.Button('Submit Manifest')]], justification='center')],
                [sg.Column([[sg.Button('View Manifest')]], justification='center')],
                [sg.Column([[sg.Button('Cancel')]], justification='center')],
                [sg.Column([[sg.Multiline('', size=(200, 100), font=body_font, key = '_text2_', visible = True)]], key='window-col', justification='center')],
            ]
    return sg.Window("SAIL ENTERPRISE - Upload Manifest", layout, size=(1000, 700), resizable=True, grab_anywhere=True, margins=(0, 0), finalize=True)

#---------------INTERACTIVE GRID METHOD------------------------------------
def gridSelection(ship):
    layout =[
                [sg.Column([[sg.Text('Current User: ' + currUser ,font=body_font)]], justification='left')],  
                [sg.Column([[sg.Text('Ship: ' + str(shipName), font=body_font)]], justification='left')],  
                [sg.Column([[sg.Text('\nSelect Containers to Load/Unload: ', font=heading_font)]], justification='center')],   
                [sg.Column([[sg.Button(f'{row},{col}') for col in range(1,13)] for row in range(8,0,-1)], justification='center')],
                [sg.Column([[sg.Button('LOAD NEW CONTAINER')]], justification='center')],
                [sg.Column([[sg.Button('START')]], justification='center')],
                [sg.Column([[sg.Text('\n' + loadedMsg, font=body_font, key = '_text1_', visible = True)]], justification='center')],   
            ]
    window = sg.Window("SAIL ENTERPRISE - Load/Unload Selection", layout, size=(1000, 700), resizable=True, grab_anywhere=True, margins=(0, 0), finalize=True)
    for field in window.element_list(): # loop updates the button colors on grid to match manifest given
        if (type(field) == type(sg.Button())) and (str(field.Key).find(',') >= 0):
            s = str(field.Key)
            ind = s.find(',')
            row = int(s[0:ind])-1
            col = int(s[ind+1:])-1
            if(ship[row][col].num > 0):
                field.update(button_color = "grey")
            elif(ship[row][col].num == 0):
                field.update(button_color = "white")
            else:
                field.update(button_color=("black","black"))
    return window

#---------------ADD NEW CONTAINER METHOD------------------------------------
def addContainer():
    layout =[
                [sg.Column([[sg.Text('Current User: ' + currUser ,font=body_font)]], justification='left')],  
                [sg.Column([[sg.Text('Ship: ' + str(shipName), font=body_font)]], justification='left')],
                [sg.Column([[sg.Text('Enter the container description (max 256 characters)',font=body_font)]], justification='Center')],   
                [sg.Column([[sg.Input(justification='center', key='-dsc-')]], justification='center')],
                [sg.Column([[sg.Text('Enter the container weight (0-99999 kilograms)',font=body_font)]], justification='Center')],
                [sg.Column([[sg.Input(justification='center', key='-wgt-')]], justification='center')], 
                [sg.Column([[sg.Button('Add Container'), sg.Button('Cancel')]], justification='center')],
                [sg.Column([[sg.Text('WARNING: You will not be able to change a container once it is added to the loading list',font=body_font)]], justification='Center')],
            ]
    return sg.Window("SAIL ENTERPRISE - Add New Container", layout, size=(1000, 700), resizable=True, grab_anywhere=True, margins=(0, 0), finalize=True)

#---------------MOVEMENT METHOD------------------------------------
def LUmovement(ship,r1,c1,r2,c2):
    # gets correct move message and container we are moving
    if r1 == -1 and c1 == -1: # load
        c = loads[-1]
        moveMsg = "Truck to [" + str(r2+1).zfill(2) + "][" + str(c2+1).zfill(2) + "]"
        r1 = 8
        c1 = 0
    else:
        c = ship[r1][c1]
        if r2 == -1 and c2 == -1: # unload
            moveMsg = "[" + str(r1+1).zfill(2) + "][" + str(c1+1).zfill(2) + "] to Truck"
            r2 = 8
            c2 = 0
        else: # internal move
            moveMsg = "[" + str(r1+1).zfill(2) + "][" + str(c1+1).zfill(2) + "] to [" + str(r2+1).zfill(2) + "][" + str(c2+1).zfill(2) + "]"
    layout =[
                [sg.Column([[sg.Text('Current User: ' + currUser ,font=body_font)]], justification='left')],  
                [sg.Column([[sg.Text('Ship: ' + str(shipName), font=body_font)]], justification='left')],
                [sg.Column([[sg.Text('Move: ' + moveMsg, font=body_font)]], justification='center')],
                [sg.Column([[sg.Text('Description: ' + c.desc, font=body_font)]], justification='center')],
                [sg.Column([[sg.Text('Weight: ' + str(c.weight), font=body_font)]], justification='center')],   
                [sg.Column([[sg.Button(f'{str(row).zfill(2)},{str(col).zfill(2)}') for col in range(1,13)] for row in range(11,0,-1)], justification='center')],
                [sg.Column([[sg.Button('Add Log'), sg.Button('NEXT'), sg.Button('Login')]], justification='center')],
            ]
    window = sg.Window("SAIL ENTERPRISE - Move", layout, size=(1000, 700), resizable=True, grab_anywhere=True, margins=(0, 0), finalize=True)
    for field in window.element_list(): # loop updates the button colors on grid to match manifest given
        if (type(field) == type(sg.Button())) and (str(field.Key).find(',') >= 0):
            s = str(field.Key)
            ind = s.find(',')
            row = int(s[0:ind])-1
            col = int(s[ind+1:])-1
            if row == r1 and col == c1: # this is the container we are moving, so green
                field.update(button_color = "green")
            elif row == r2 and col == c2: # this is the end location, so red
                field.update(button_color = "red")
            else:
                if row == 10:
                    field.update(button_color = "white")
                else:
                    if(ship[row][col].num > 0):
                        field.update(button_color = "grey")
                    elif(ship[row][col].num == 0):
                        field.update(button_color = "white")
                    else:
                        field.update(button_color=("black","black"))
    return window
#--------------------MAIN EVENT LOOP---------------------------------------------------------
window1, selectJobWindow, uploadWindow, gridWindow, addWindow, LUmoveWindow = None, selectJob(), None, None, None, None   # start off with main window open (fix to be with whatever is saved)

while True:             # Event Loop
    window, event, values = sg.read_all_windows()
    if event == sg.WIN_CLOSED:
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
        elif window == addWindow:
            addWindow = None
            break
        elif window == LUmoveWindow:
            addWindow = None
            break
        elif window == window1:     # if closing win 1, exit program
            break
   
    # LOGIN Process
    if window == window1:
        if event == "Login": # login button on login window
            login(values['-usrnm-']) # updates currUser and logs sign in/off
            print("Username:", currUser)
            print('Login Successful - Foward to JOB SELECTION')
            selectJobWindow = selectJob() # REDIRECT to job selection window
            window1.Hide()

        elif event == 'Cancel': # Go back button on login window
            print('Login Canceled - Return to JOB SELECTION')
            selectJobWindow.UnHide() # show job selection window for current user again
            window1.Hide()
    
    # JOB SELECTION process
    if window == selectJobWindow:
        if event == 'Start New Load/Unload': # LU job select button on main window
            selectedJob = 1
            print('LOAD/UNLOAD -- Forward to UPLOAD MANIFEST/n')
            selectJobWindow.Hide() #closes job selection window
            uploadWindow = uploadManifest()

        elif event == 'Start New Balancing Job': # Balance job select button on main window
            selectedJob = 2
            print('BALANCING -- Forward to UPLOAD MANIFEST/n')
            selectJobWindow.Hide()
            uploadWindow = uploadManifest()

        elif event == 'Login': # Login button on main window
            print('Forward to LOGIN screen')
            selectJobWindow.Hide()
            window1 = loginWindow()   #load login window

    # UPLOAD manifest process
    if window == uploadWindow:
        if event == "View Manifest": # view manifest contentes before submitting
            if('' == values['-manifest-']): #see if file is selected
                sg.popup("No file selected. Select file to view.",title="File Read Error") # Error message if mainfest file invalid  
            else:
                print("VIEWING manifest contents")
                fileM = open(values['-manifest-'])
                line = fileM.read()      
                fileM.close()
                manifestCont = '\nManifest Contents: \n' + line
                uploadWindow['_text2_'].update(manifestCont)
        elif event == "Submit Manifest": # submit manifest button on upload window
            manifest = values['-manifest-'] # get input
            #outputting manifest to window
            #updating window to print manifest
            ship = loadManifest(manifest) # load manifest into array
            if(ship[0][0] == None):
                sg.popup("Invalid manifest file, try again.",title="File Read Error") # Error message if mainfest file invalid            
            else:
                manifest = os.path.basename(manifest) # get manifest file name
                addLog("Manifest " + manifest + " is opened, there are " + str(containerNum-1) + " containers on the ship") # push log                
                shipName = manifest[:-4] # remove ".txt" from manifest to get ship name
                print('SELECTED MANIFEST : ', manifest)
                manifestCont = ''
                if selectedJob == 1:
                    loads = [] # reset loads
                    unloads = [] # reset unloads
                    uploadWindow.Hide()
                    gridWindow = gridSelection(ship) # open grid slection if LU job
                elif selectedJob == 2: 
                    sg.popup("Start new Balancing Job") #Placeholder - forward to balancing layout 

        elif event == "Cancel": # cancel upload button on upload window
            print("CANCLED Manifest upload - RETURN to Job Selection")
            manifestCont = ''
            selectedJob = 0 # restore job selection
            selectJobWindow.UnHide()
            uploadWindow.Hide()            

    # GRID WINDOW process
    if window == gridWindow:
        if event == 'LOAD NEW CONTAINER':       
            print('ADD NEW CONTAINER -- Forward to load new container layout/n')
            gridWindow.Hide()
            addWindow = addContainer()

        elif event.find(',') >= 0: # When a user clicks a grid button
            ind = event.find(',')
            row = int(event[0:ind])-1
            col = int(event[ind+1:])-1
            if(ship[row][col].num > 0): # find container they select and check if its a valid container
                for field in gridWindow.element_list():
                    if str(field.Key) == event: # find corresponding button
                        if (row,col) not in unloads:
                            unloads.append((row,col)) # add to loads if not already selected
                            field.update(button_color=("white","green"))
                            loadedMsg= "Selected container \"" + ship[row][col].desc + "\" Click button again to de-select it."
                            gridWindow['_text1_'].update("\nAction: " + loadedMsg)
                            #sg.popup(msg,title="Confirm Selection") # output confirm selection
                        else:
                            unloads.remove((row,col)) # remove from loads if button was already selected
                            field.update(button_color=("white","grey"))
                            loadedMsg= "De-select container \"" + ship[row][col].desc + "\" Click button again to select it."
                            gridWindow['_text1_'].update("\nAction: " + loadedMsg)
                        break

        elif event == 'START': # NOT FINISHED
            loadedMsg = ''
            if not loads and not unloads:
                # Go to finish screen, no algorithm needs to be run
                fileName = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop', '{}OUTBOUND.txt'.format(shipName))
                grid2Manifest(ship,fileName)
                sg.popup("Job Complete! The updated manifest has been downloaded to the desktop as " + shipName + "OUTBOUND.txt. Remember to email it to the captain!",title="Success")
                addLog("Finished a Cycle. Manifest " + shipName + "OUTBOUND.txt was written to desktop, and a reminder pop-up to operator to send file was displayed.")
                gridWindow.Hide()
                selectJobWindow = selectJob() # REDIRECT to job selection window
                pass
            else:
                sg.popup("The algorithm will now run after you hit OK. This may take some time.",title="Starting Algorithm")
                goal = LUjob(ship,loads,unloads) # run job
                estimatedTime = goal.g # get estimated time
                moves = goal.moves # get move list
                currMove = 0 # index of current move
                r1,c1,r2,c2 = retrieveInds(moves,currMove)
                currMove+=1
                gridWindow.Hide()
                LUmoveWindow = LUmovement(ship,r1,c1,r2,c2) # generate window based off move and initial ship state

    # ADD CONTAINER PROCESS
    if window == addWindow:
        if event == 'Add Container': # add container button on add window
            description = str(values['-dsc-'])
            weight = int(values['-wgt-'])
            if(len(description) > 256) or (weight < 0) or (weight > 99999): # check validity of inputs
                sg.popup("Invalid weight or description length",title="Input Error")
            else:
                c = Container() # create new container
                c.weight = weight
                c.desc = description
                c.num = containerNum
                containerNum+=1
                loads.append(c) # add to loads
                sg.popup("Successfully added container to load list.",title="Success")
                print("ADDED new container to load list: ", description, " weight: ", weight)
                gridWindow.UnHide()
                addWindow.Hide()

        elif event == 'Cancel': # Cancel Button on add window
            gridWindow.UnHide()
            addWindow.Hide()

    # MOVEMENT PROCESS
    if window == LUmoveWindow:
        if event == "Add Log":
            pass
        elif event == "NEXT": # NEXT button in move Window
            r1,c1,r2,c2 = retrieveInds(moves,currMove-1)
            # make sure ship is updated with the move (since they hit next confirming they made the move)
            if r1 == -1 and c1 == -1: # load
                c = loads[-1]
                loads = loads[:-1]
                ship[r2][c2] = c
                addLog("\"" + c.desc + "\" is onloaded.") # push log if onload
            else:
                c = ship[r1][c1]
                if r2 == -1 and c2 == -1: # unload
                    addLog("\"" + c.desc + "\" is offloaded.") # push log if offload
                    ship[r1][c1].desc = "UNUSED"
                    ship[r1][c1].weight = 0
                    ship[r1][c1].num = 0
                else: # internal move
                    ship[r1][c1] = ship[r2][c2]
                    ship[r2][c2] = c
            if currMove == len(moves): # last move was completed, so we are done and can download new manifest
                fileName = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop', '{}OUTBOUND.txt'.format(shipName))
                grid2Manifest(ship,fileName)
                sg.popup("Job Complete! The updated manifest has been downloaded to the desktop as " + shipName + "OUTBOUND.txt. Remember to email it to the captain!",title="Success")
                addLog("Finished a Cycle. Manifest " + shipName + "OUTBOUND.txt was written to desktop, and a reminder pop-up to operator to send file was displayed.")
                LUmoveWindow.Hide()
                selectJobWindow = selectJob() # REDIRECT to job selection window
            else:
                r1,c1,r2,c2 = retrieveInds(moves,currMove)
                currMove+=1
                LUmoveWindow.Hide()
                LUmoveWindow = LUmovement(ship,r1,c1,r2,c2) # else, generate new window based on new ship and next move
        elif event == "Login":
            pass
        
window.close()