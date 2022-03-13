import PySimpleGUI as sg
import datetime
import os
import heapq
import numpy as np
import pickle
import copy

sg.theme('DefaultNoMoreNagging') 

# globals
heading_font = ("Arial, 24") # Fonts
body_font = ("Arial, 14")
entryCount = 0 # tie breaker for states with equal priority
containerNum = 1 # tracks unique containers
loads = [] # tracks loads before job starts
unloads = [] # tracks unloads before job starts
loadedMsg = '' # # tracks what has been selected
manifestCont = '' # tracks deselected and manifest content
currUser = '' # Global variable to store currently logged in user
selectedJob = 0 # tracks the currently selected job
jobOngoing = False # tracks if a job is ongoing
animationList = [] # stroes the list for the animation
animationInd = -1 # stores the index for the animation
animationLen = 0 # stores length of aniation
estimatedTimeTotal = '' # stores estimated time of entire job
estimatedTimeMove = '' # stores estimated time of particular move (crane move time + container move time)
numContainers = 0
numNAN = 0

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
    # state.hasContainer
    # state.times
    # state.loads
    # state.unloads
    # state.moves
    pass

class Bstate(object):
    # state.ship
    # state.g
    # state.h
    # state.cranePos
    # state.moves
    # state.cost
    # state.balance_list
    pass

class list_balance_info(object):
    #list_balance_info.weight
    #list_balance_info.row
    #list_balance_info.col
    #list_balance_info.moved
    pass

class list_balance_state(object):
    #state.total_lweight
    #state.total_rweight
    #state.left_side_list
    #state.right_side_list
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
    numNAN = 0
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
                numNAN += 1
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
        return np.empty([10, 12], dtype = Container), 0

    # return array
    return manifest, numNAN

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

def backupLoads(loads, filename): # backup the containers in load to the saved file
    file = open(filename,'w')
    for element in loads:
        file.write('{},{}\n'.format(element.weight, element.desc))
    file.close()

def retrieveBackupLoads(filename): # retrieve containers in loads back into array
    global containerNum
    file = open(filename,'r')
    f = file.readlines()
    l = []
    for line in f:
        c = Container()
        c.num = containerNum
        containerNum+=1
        ind = line.find(',')
        c.weight = int(line[0:ind])
        if(line[-1 == '\n']): # dont record endline in description
            line = line[:-1]
        c.desc = str(line[ind+1:])
        l.append(c)
    file.close()
    return l

#---------------BALANCE MAIN FUNCTIONS------------------------------------
def Bjob(ship): # COMPLETE: initalizes state and computes the goal for balance
    initState = Bstate()
    initState.ship = ship
    initState.g = 0
    initState.moves = []
    initState.times = []
    initState.cranePos = (-1,-1) # crane starts on dock by trucks
    if(Balanced(initState)):
        return initState
    moves_list = get_moves_list(initState)
    if(len(moves_list) > 0):
        initState.balance_list = []
        #adds list of containers to the state that need to be moved 
        for i in range(len(moves_list)):
            initState.balance_list.append((moves_list[i].row, moves_list[i].col))

        #flags each container that needs to be moved as needing to be moved to the left or right side of the ship
        for j in range(12):
            for i in range(10):
                if((i, j) in initState.balance_list):
                    if(j < 6):
                        initState.ship[i][j].move_right = True
                        initState.ship[i][j].move_left = False
                    else:
                        initState.ship[i][j].move_left = True
                        initState.ship[i][j].move_right = False
                else:
                    initState.ship[i][j].move_right = False
                    initState.ship[i][j].move_left = False

        Bheuristic(initState)
        return Bsearch(initState)
    else:
        initState.hasContainer = False
        return SIFTsearch(initState)

def Bsearch(initState): # COMPLETE: A* search for Balance jobs no SIFT
    global entryCount
    entryCount = 0
    q = [] # priority queue
    heapq.heappush(q, ((initState.g + initState.h), entryCount, initState)) # push initial state onto queue
    entryCount+=1

    checkedStates = [] # hold checked states

    while (len(q) > 0): # Loop while queue is not empty
        item = heapq.heappop(q)
        curState = item[2] # get current state

        if(BstateCheck(curState, checkedStates)): # so we dont expand states we already expanded
            continue

        if (Balanced(curState)): # Test if state is the goal (no more moves to balance)
            return curState # return state as solution if true
        else:
            Bexpand(curState, q) # expand state if false

        checkedStates.append(curState) # add state to checked states

    print("No Solution") # print error if no solution
    return

def Bexpand(state, q): # COMPLETE: expands given state for Balance job
    global entryCount
    tops = findTops(state)
    for j in range(12): # for each column
        i = tops[j] # get row of container to move
        if(i < 0) or (state.ship[i][j].desc == "NAN"): # no containers in that column
            continue

        ##get range of movement for container
        #start = 0
        #end = 12
        ##containers with move_left = True will only move to columns in the left side
        #if(state.ship[i][j].move_left):
        #    end = 6
        ##containers with move_right = True will only move to columns in the right side
        #if(state.ship[i][j].move_right):
        #    start = 6

        for c in range(12): # for every other column
            if (c != j):
                r = tops[c]+1 # get row location of move (1 above the top)
                if(r < 10): # Check that the col is not the max col height
                    copy = BstateCopy(state)

                    #if container that needs to be moved to the left is moved to the right side of the ship
                    #add it to list of containers that need to be balanced
                    if(state.ship[i][j].move_left and c >= 6):
                        copy.balance_list.append((r, c))

                    #if container that needs to be moved to the right is moved to the left side of the ship
                    #add it to list of containers that need to be balanced
                    elif(state.ship[i][j].move_right and c < 6):
                        copy.balance_list.append((r, c))


                    #remove original container position from balance list if it is on there
                    if((i, j) in state.balance_list):
                        copy.balance_list.remove((i,j))

                    copy.ship[r][c].weight = copy.ship[i][j].weight # move container
                    copy.ship[r][c].desc = copy.ship[i][j].desc
                    copy.ship[r][c].num = copy.ship[i][j].num
                    copy.ship[r][c].move_left = copy.ship[i][j].move_left
                    copy.ship[r][c].move_right = copy.ship[i][j].move_right
                    copy.ship[i][j].weight = 0
                    copy.ship[i][j].desc = "UNUSED"
                    copy.ship[i][j].num = -1
                    copy.ship[i][j].move_left = False
                    copy.ship[i][j].move_right = False
                    copy.moves.append((i,j,r,c))
                    cost = 0
                    if(copy.cranePos == (-1, -1)): #check if crane is by truck
                        cost += (abs(i-8) + abs(j-0) + 2)
                    else: #move crane to container position
                        cost += manhattanDist(copy.cranePos[0],copy.cranePos[1],i,j,tops)
                    #add distance to move container to new location
                    cost +=  manhattanDist(i, j, r, c, tops)
                    copy.g += cost
                    copy.times.append(str(datetime.timedelta(minutes=cost))[:-3])
                    #leave crane postion at new location
                    copy.cranePos = (r, c)
                    
                    Bheuristic(copy) # calculate new heuristic
                    heapq.heappush(q, ((copy.g + copy.h), entryCount, copy)) # push copy to queue
                    entryCount+=1

def Bheuristic(state): # COMPLETE: find h(n) of a given Bstate, store in state parameter automatically
    tops = findTops(state)
    ship = state.ship
    tempPos = state.cranePos
    h = 0
    #stores position of nearest positions on left and right side
    #even if height of the column is 10, the heuristic will still be underestimating the distance so it is ok
    right = (tops[6], 6)
    left = (tops[5], 5)

    for j in range(12): # for each col
        for i in range(tops[j]+1): # for each row with filled containers
            if((i,j) in state.balance_list): # check if container needs to be moved to other side
                for k in range(tops[j],i-1,-1): # for the rest of the containers from top to the found container that needs to go to the opposite side of the ship
                    if(tempPos == (-1,-1)):
                        h+=(abs(k-8) + abs(j-0) + 2) # move crane from truck to container
                    else:
                        h+=(abs(k-tempPos[0]) + abs(j-tempPos[1])) # move crane to container

                    if((k,j) in state.balance_list): # if container needs to be moved to the other side add the distance
                        if(j < 6):
                            h += manhattanDist(k, j, right[0], right[1], tops)
                            tempPos = (right[0],right[1]) # set crane position at nearest right side location
                        else:
                            h += manhattanDist(k, j, left[0], left[1], tops)
                            tempPos = (left[0],left[1]) # set crane position at nearest left side location
                    else: # if not, add nearest distance that does not overestimate
                        pos = nearestDistPos(k,j,tops)
                        h+=(abs(pos[0]-tempPos[0]) + abs(pos[1]-tempPos[1]))
                        tempPos = pos
                break

    for i in range(8,10):
        for j in range(12):
            if(ship[i][j].desc != "UNUSED"):
                h+=nearestTempRemoval(i,j,tops) # add nearest distance to column not reaching into temp rows

    state.h = h

def SIFTsearch(initState): # COMPLETE: A* search for SIFT jobs
    goalShip = findSIFTGoal(initState)
    SIFTheuristic(initState, goalShip)

    global entryCount
    entryCount = 0
    q = [] # priority queue
    heapq.heappush(q, ((initState.g + initState.h), entryCount, initState)) # push initial state onto queue
    entryCount+=1

    checkedStates = [] # hold checked states

    while (len(q) > 0): # Loop while queue is not empty
        item = heapq.heappop(q)
        curState = item[2] # get current state

        if(SIFTstateCheck(curState, checkedStates)): # so we dont expand states we already expanded
            continue

        if (SIFTGoalCheck(curState,goalShip)): # Test if state is the goal (no more moves to balance)
            return curState # return state as solution if true
        else:
            SIFTexpand(curState, q, goalShip) # expand state if false

        checkedStates.append(curState) # add state to checked states

    print("No Solution") # print error if no solution
    return

def SIFTexpand(state, q, goalShip): # COMPLETE: expands given state for SIFT job
    global entryCount
    tops = findTops(state)
    if(state.hasContainer): # container attached to crane, expand by moving containers
        for c in range(12): # move to all other valid columns
            r = tops[c]+1
            if (c == state.cranePos[1]) or (r == 10):
                continue
            copy = SIFTstateCopy(state)
            i = copy.cranePos[0]
            j = copy.cranePos[1]
            cost = manhattanDist(i,j,r,c,tops)
            copy.g += cost
            cost += copy.times[-1]
            copy.times[-1] = str(datetime.timedelta(minutes=cost))[:-3]
            copy.cranePos = (r,c) # leave crane at dropoff position
            copy.ship[r][c].weight = copy.ship[i][j].weight # swap container
            copy.ship[r][c].desc = copy.ship[i][j].desc
            copy.ship[r][c].num = copy.ship[i][j].num
            copy.ship[i][j].weight = 0
            copy.ship[i][j].desc = "UNUSED"
            copy.ship[i][j].num = 0
            copy.moves.append((i,j,r,c))
            copy.hasContainer = False
            SIFTheuristic(copy, goalShip) # calculate new heuristic
            heapq.heappush(q, ((copy.g + copy.h), entryCount, copy)) # push copy to queue
            entryCount+=1  
    else: # crane does not have contianer, expand by moving crane to contianer positions
        for c in range(12):
            r = tops[c]
            if (r == -1) or (state.ship[r][c].num == -1): # column is empty
                continue
            copy = SIFTstateCopy(state)
            if(copy.cranePos == (-1,-1)):
                cost = (abs(r-8) + abs(c-0) + 2)
            else:
                i = copy.cranePos[0]
                j = copy.cranePos[1]
                cost = manhattanDist(i,j,r,c,tops)
            copy.g += cost
            copy.times.append(cost)
            copy.cranePos = (r,c)
            copy.hasContainer = True
            SIFTheuristic(copy, goalShip)
            heapq.heappush(q, ((copy.g + copy.h), entryCount, copy)) # push copy to queue
            entryCount+=1

def SIFTheuristic(state, goalShip): # COMPLETE: find h(n) of a given LUstate, store in state parameter automatically
    ship = state.ship
    tops = findTops(state)
    h = 0
    for i in range(10):
        for j in range(12):
            if(ship[i][j].num > 0):
                for r in range(10):
                    for c in range(12):
                        if(ship[i][j].num == goalShip[r][c].num):
                            h += manhattanDist(i,j,r,c,tops)
    state.h = h

#---------------BALANCE HELPER FUNCTIONS------------------------------------
def BstateCopy(state): # COMPLETE: Copies an balance state
    copy_state = Bstate() # set up copy state
    copy_state.h = state.h
    copy_state.g = state.g
    copy_state.balance_list = state.balance_list
    copy_state.ship = [] # copies ship state with container copy
    for i in range(10):
        row = []
        for j in range(12):
            row.append(BcontainerCopy(state.ship[i][j]))
        copy_state.ship.append(row)

    copy_state.moves = state.moves.copy() # moves array is tuples, so this works
    copy_state.times = state.times.copy()
    copy_state.cranePos = state.cranePos
    copy_state.balance_list = copy.deepcopy(state.balance_list)
    return copy_state

def BstateCheck(state, checkedStates): # COMPLETE: checks if state and states in list are equivolent (ignoring h and g values)
    ship = state.ship
    for i in range(len(checkedStates)): # for all checked states
        curShip = checkedStates[i].ship
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

def Balanced(state): # checks if a ships sides are balanced
    ship = state.ship
    left = 0
    for i in range(10):
        for j in range(6):
            left+=ship[i][j].weight
    right = 0
    for i in range(10):
        for j in range(6,12):
            right+=ship[i][j].weight
    if(max(left,right) == 0):
        return True
    return (min(left,right)/max(left,right) > 0.9)

def BcontainerCopy(container): # COMPLETE: Copies a Container
    copy = Container()
    copy.weight = container.weight
    copy.desc = container.desc
    copy.num = container.num
    copy.move_left = container.move_left
    copy.move_right = container.move_right
    return copy

def get_moves_list(state): # returns the moves list for a given state
    iter_list, total_lweight, total_rweight = get_iterlist(state)
    list_state = list_balance_state()
    list_state.total_lweight = total_lweight
    list_state.total_rweight = total_rweight
    list_state.left_side_list = []
    list_state.right_side_list = []
    moves_list = []

    #go through all the iterations adding each layer of containers and seeing if we can find a solution with the minimal amount of layers
    for i in range(len(iter_list)):
        for j in range(len(iter_list[i])):
            if(iter_list[i][j].col < 6):
                #want to append containers in a way where the first container is closest to the middle
                list_state.left_side_list = [iter_list[i][j]] + list_state.left_side_list
            else:
                list_state.right_side_list.append(iter_list[i][j])
        moves_list = balance_list_expand(list_state)
        if(len(moves_list) > 0):
            break
    return moves_list

def get_iterlist(state): #returns 2d list of balance_info objects speparated by which iteration they will be added, also returns total right and left side weight
    #initialize list of iterations, this will hold all of the iterations(see iter)
    iter_list = []
    total_rweight = 0
    total_lweight = 0

    #get ship information and containers with the greatest height in each column
    #ship = state.ship
    ship = state.ship
    tops = findTops(state)
    
    #we are going to havc only up to 8 iterations, this function will be used for ships that have just docked
    #this means there will be no columns with a height of above 8
    for k in range(8):
        #iter contains the containers that will be added to the search every iteration
        #see the second video on balancing to understand: https://drive.google.com/file/d/1fd9yuonDalaF3-NQqS4hX7KB-2bcQabg/view
        iter = []

        #iterate through each column
        for j in range (12):
            #get row of topmost container for that column
            i = tops[j]
            #if the value is below 0, then there are no containers in that column left to check
            if(i >= 0):
                #if topmost container is nan, then we can ignore the column
                if(ship[i][j].desc != "NAN"):
                    b = list_balance_info()
                    #get information of container
                    b.weight = ship[i][j].weight
                    b.row = i
                    b.col = j
                    b.moved = False
                    iter.append(b)
                    if(j < 6):
                        total_lweight += b.weight
                    else:
                        total_rweight += b.weight
                    #set up next iteration to get the container below the current one
                    tops[j] = tops[j] - 1
        #appends the iter to iter_list
        if(len(iter) > 0):
            iter_list.append(iter)
        #if iter is empty, that means we have already added all possible containers and we can stop
        else:
            break

    return iter_list, total_lweight, total_rweight

def get_list_heuristic(list_state): #gets heuristic for the list_state
    mean = (list_state.total_lweight + list_state.total_rweight)/2
    h = abs(list_state.total_lweight - mean) + abs(list_state.total_rweight - mean)

    #returns 0 if we are within 10% of each other, this means that this state is balanced 
    if(abs(list_state.total_lweight - mean) <= 0.05 * mean and abs(list_state.total_rweight - mean) <= 0.05 * mean):
        return 0
    #returns heuristic value if we are not within 10% of each other
    return h

def balance_list_expand(list_state): #function that does the work expanding the nodes for every given iteration
    counter = 0
    limit = 100000
    queue = []
    move_list = []
    #pushes initial state onto queue and sorts it by heuristic value, then by counter if the heuristic values are equal
    heapq.heappush(queue, (get_list_heuristic(list_state), counter, list_state))
    counter += 1

    #if the for loop reaches the limit or queue is empty, the function will terminate and return an empty moves_list
    for i in range(limit):
        if(len(queue) > 0):
            current_node = heapq.heappop(queue)
            current_state = current_node[2]

            #if we found the goal state return the list of containers that need to be moved to achieve this goal state
            if(current_node[0] == 0  and len(current_state.left_side_list) <= 48 and len(current_state.right_side_list) <= 48):


                for l in range(len(current_state.left_side_list)):
                    if(current_state.left_side_list[l].moved):
                        move_list.append(current_state.left_side_list[l])

                for r in range(len(current_state.right_side_list)):
                    if(current_state.right_side_list[r].moved):
                        move_list.append(current_state.right_side_list[r])

                break

            for l in range(len(current_state.left_side_list)):
                #create a state for each possible container movement from left to right(we do not move containers that have been moved once already)
                if(current_state.left_side_list[l].moved != True):

                    #copy container information over
                    copy_state = list_balance_state()
                    copy_state.total_lweight = current_state.total_lweight
                    copy_state.total_rweight = current_state.total_rweight
                    copy_state.left_side_list = copy.deepcopy(current_state.left_side_list)
                    copy_state.right_side_list = copy.deepcopy(current_state.right_side_list)

                   

                    #move the selected container over
                    copy_state.total_lweight -= copy_state.left_side_list[l].weight
                    copy_state.total_rweight += copy_state.left_side_list[l].weight
                    copy_state.left_side_list[l].moved = True
                    heapq.heappush(queue, (get_list_heuristic(copy_state), counter, copy_state))
                    counter += 1

            for r in range(len(current_state.right_side_list)):
                #create a state for each possible container movement from right to left(we do not move containers that have been moved once already)
                if(current_state.right_side_list[r].moved != True):

                    #copy container information over
                    copy_state = list_balance_state()
                    copy_state.total_lweight = current_state.total_lweight
                    copy_state.total_rweight = current_state.total_rweight
                    copy_state.left_side_list = copy.deepcopy(current_state.left_side_list)
                    copy_state.right_side_list = copy.deepcopy(current_state.right_side_list)

                    #move the selected container over
                    copy_state.total_lweight += copy_state.right_side_list[r].weight
                    copy_state.total_rweight -= copy_state.right_side_list[r].weight
                    copy_state.right_side_list[r].moved = True
                    heapq.heappush(queue, (get_list_heuristic(copy_state), counter, copy_state))
                    counter += 1
        else:
            break

    return move_list

def SIFTstateCopy(state): # COMPLETE: Copies an LU state
    copy = Bstate() # set up copy state
    copy.h = state.h
    copy.g = state.g

    copy.ship = [] # copies ship state with container copy
    for i in range(10):
        row = []
        for j in range(12):
            row.append(containerCopy(state.ship[i][j]))
        copy.ship.append(row)

    copy.moves = state.moves.copy() # moves array is tuples, so this works
    copy.times = state.times.copy()
    copy.cranePos = state.cranePos
    copy.hasContainer = state.hasContainer

    return copy

def SIFTstateCheck(state, checkedStates): # COMPLETE: checks if state and states in list are equivolent (ignoring h and g values)
    ship = state.ship
    for i in range(len(checkedStates)): # for all checked states
        if(state.cranePos != checkedStates[i].cranePos):
            continue
        if(state.hasContainer != checkedStates[i].hasContainer): # container attachment not equal, not equivolent
            continue
        curShip = checkedStates[i].ship
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

def findSIFTGoal(initState):
    goal = np.empty([10, 12], dtype = Container)
    siftInds = [(0,6),(0,5),(0,7),(0,4),(0,8),(0,3),(0,9),(0,2),(0,10),(0,1),(0,11),(0,0),
                (1,6),(1,5),(1,7),(1,4),(1,8),(1,3),(1,9),(1,2),(1,10),(1,1),(1,11),(1,0),
                (2,6),(2,5),(2,7),(2,4),(2,8),(2,3),(2,9),(2,2),(2,10),(2,1),(2,11),(2,0),
                (3,6),(3,5),(3,7),(3,4),(3,8),(3,3),(3,9),(3,2),(3,10),(3,1),(3,11),(3,0),
                (4,6),(4,5),(4,7),(4,4),(4,8),(4,3),(4,9),(4,2),(4,10),(4,1),(4,11),(4,0),
                (5,6),(5,5),(5,7),(5,4),(5,8),(5,3),(5,9),(5,2),(5,10),(5,1),(5,11),(5,0),
                (6,6),(6,5),(6,7),(6,4),(6,8),(6,3),(6,9),(6,2),(6,10),(6,1),(6,11),(6,0),
                (7,6),(7,5),(7,7),(7,4),(7,8),(7,3),(7,9),(7,2),(7,10),(7,1),(7,11),(7,0)]
    ship = initState.ship
    conts = []
    for i in range(8):
        for j in range(12):
            if(ship[i][j].num > 0):
                conts.append((ship[i][j].weight,ship[i][j].num,ship[i][j]))
            if(ship[i][j].num == -1):
                siftInds.remove((i,j))
                c = containerCopy(ship[i][j])
                goal[i][j] = c
    conts.sort(reverse=True)
    for i in range(len(conts)):
        c = containerCopy(conts[i][2])
        goal[siftInds[i][0]][siftInds[i][1]] = c
    for i in range(len(conts),len(siftInds)):
        c = Container()
        c.num = 0
        c.weight = 0
        c.desc = "UNUSED"
        goal[siftInds[i][0]][siftInds[i][1]] = c
    for i in range(8, 10):
        for j in range(12):
            c = Container()
            c.weight = 0
            c.desc = "UNUSED"
            c.num = 0
            goal[i][j] = c
    return goal

def SIFTGoalCheck(state,goalShip):
    ship = state.ship
    for i in range(10):
        for j in range(12):
            if(ship[i][j].num != goalShip[i][j].num):
                return False
    return True

#---------------LU MAIN FUNCTIONS------------------------------------
def LUjob(ship,loads,unloads): # initalizes state and computes the goal for LU
    initState = LUstate()
    initState.ship = ship
    initState.loads = loads
    initState.unloads = unloads
    initState.cranePos = (-1,-1) # crane starts at the dock
    initState.hasContainer = False
    LUheuristic(initState)
    initState.g = 0
    initState.moves = []
    initState.times = []
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
    if(state.hasContainer): # container attached to crane, expand by moving containers
        if(state.cranePos == (-1,-1)): # crane is attached to a load container
            for c in range(12): # unload to all valid columns
                r = tops[c]+1
                if(r == 10):
                    continue
                copy = LUstateCopy(state)
                copy.hasContainer = False
                cost = (abs(r-8) + abs(c-0) + 2)
                copy.g += cost # add cost of load to g
                cost += copy.times[-1]
                copy.times[-1] = str(datetime.timedelta(minutes=cost))[:-3]
                copy.cranePos = (r,c) # leave crane at dropoff position
                copy.ship[r][c].weight = copy.loads[-1].weight # move container
                copy.ship[r][c].desc = copy.loads[-1].desc
                copy.ship[r][c].num = copy.loads[-1].num
                copy.loads = copy.loads[:-1] # remove container from loads
                copy.moves.append(("Truck",r,c)) # track move 
                copy.hasContainer = False  
                LUheuristic(copy) # calculate new heuristic
                heapq.heappush(q, ((copy.g + copy.h), entryCount, copy)) # push copy to queue
                entryCount+=1
        else: # crane is attached to container on the ship
            if(state.cranePos in state.unloads): # container is an unload
                copy = LUstateCopy(state)
                copy.unloads.remove(copy.cranePos) # remove container from unloads
                i = copy.cranePos[0]
                j = copy.cranePos[1]
                cost = (abs(i-8) + abs(j-0) + 2)
                copy.g += cost # add distance to unload container to g
                cost += copy.times[-1]
                copy.times[-1] = str(datetime.timedelta(minutes=cost))[:-3]
                copy.cranePos = (-1,-1) # leave cranePos at the truck
                copy.ship[i][j].weight = 0 # move container
                copy.ship[i][j].desc = "UNUSED"
                copy.ship[i][j].num = 0
                copy.moves.append((i,j,"Truck")) # track move
                copy.hasContainer = False
                LUheuristic(copy) # calculate new heuristic
                heapq.heappush(q, ((copy.g + copy.h), entryCount, copy)) # push copy to queue
                entryCount+=1
            else: # container is not an unload
                for c in range(12): # move to all other valid columns
                    r = tops[c]+1
                    if (c == state.cranePos[1]) or (r == 10):
                        continue
                    copy = LUstateCopy(state)
                    i = copy.cranePos[0]
                    j = copy.cranePos[1]
                    cost = manhattanDist(i,j,r,c,tops)
                    copy.g += cost # move container
                    cost += copy.times[-1]
                    copy.times[-1] = str(datetime.timedelta(minutes=cost))[:-3]
                    copy.cranePos = (r,c) # leave crane at dropoff position
                    copy.ship[r][c].weight = copy.ship[i][j].weight # swap container
                    copy.ship[r][c].desc = copy.ship[i][j].desc
                    copy.ship[r][c].num = copy.ship[i][j].num
                    copy.ship[i][j].weight = 0
                    copy.ship[i][j].desc = "UNUSED"
                    copy.ship[i][j].num = 0
                    copy.moves.append((i,j,r,c))
                    copy.hasContainer = False
                    LUheuristic(copy) # calculate new heuristic
                    heapq.heappush(q, ((copy.g + copy.h), entryCount, copy)) # push copy to queue
                    entryCount+=1  
    else: # crane does not have contianer, expand by moving crane to contianer positions
        if(state.cranePos == (-1,-1)): # crane is by the truck
            if (len(state.loads) > 0): # still loads, so attach container
                copy = LUstateCopy(state)
                copy.hasContainer = True
                copy.times.append(0)
                LUheuristic(copy)
                heapq.heappush(q, ((copy.g + copy.h), entryCount, copy)) # push copy to queue
                entryCount+=1
            for c in range(12):
                r = tops[c]
                if (r == -1) or (state.ship[r][c].num == -1): # column is empty
                    continue
                copy = LUstateCopy(state)
                cost = (abs(r-8) + abs(c-0) + 2)
                copy.g += cost # add cost of move to g
                copy.times.append(cost)
                copy.cranePos = (r,c)
                copy.hasContainer = True
                LUheuristic(copy)
                heapq.heappush(q, ((copy.g + copy.h), entryCount, copy)) # push copy to queue
                entryCount+=1 
        else:
            i = state.cranePos[0]
            j = state.cranePos[1]
            if (len(state.loads) > 0): # still loads, so attach container
                copy = LUstateCopy(state)
                cost = (abs(i-8) + abs(j-0) + 2)
                copy.g += cost # add cost of move to g
                copy.times.append(cost)
                copy.hasContainer = True
                copy.cranePos = (-1,-1)
                LUheuristic(copy)
                heapq.heappush(q, ((copy.g + copy.h), entryCount, copy)) # push copy to queue
                entryCount+=1
            for c in range(12):
                r = tops[c]
                if (r == -1) or (state.ship[r][c].num == -1): # column is empty
                    continue
                copy = LUstateCopy(state)
                cost = manhattanDist(i,j,r,c,tops)
                copy.g += cost # move crane into position
                copy.times.append(cost)
                copy.cranePos = (r,c)
                copy.hasContainer = True
                LUheuristic(copy)
                heapq.heappush(q, ((copy.g + copy.h), entryCount, copy)) # push copy to queue
                entryCount+=1

def LUheuristic(state): # COMPLETE: find h(n) of a given LUstate, store in state parameter automatically
    tops = findTops(state)
    ship = state.ship
    h = 0
    for j in range(12): # for each col
        for i in range(tops[j]+1): # for each row with filled containers
            if((i,j) in state.unloads): # check if container needs to be unloaded
                tempPos=(tops[j],j)
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
    copy.times = state.times.copy()
    copy.cranePos = state.cranePos
    copy.hasContainer = state.hasContainer

    return copy

def LUstateCheck(state, checkedStates): # checks if state and states in list are equivolent (ignoring h and g values)
    ship = state.ship
    for i in range(len(checkedStates)): # for all checked states
        curState = checkedStates[i]
        if(state.cranePos != curState.cranePos):
            continue
        if(state.hasContainer != curState.hasContainer): # container attachment not equal, not equivolent
            continue
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
    return False # return false if all checked states are different from states

#---------------GENERAL HELPER FUNCTIONS------------------------------------
def manhattanDist(r1,c1,r2,c2,tops): # Manhatten distance between inital indexes and final indexs, taking into account you cant pass through containers
    maxHeight = -1
    if(c1 > c2):
        for c in range(c2,c1):
            if(tops[c]+1 > maxHeight):
                maxHeight = tops[c]+1 # find max height in between columns
    elif (c1 < c2):
        for c in range(c1+1,c2+1):
            if(tops[c]+1 > maxHeight):
                maxHeight = tops[c]+1 # find max height in between columns
    else:
        return abs(r1-r2)
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

def retrieveInds(moves,currMove): # turns tuples of moves into useable indexes
    tup = moves[currMove]
    if len(tup) == 4:
        return tup[0],tup[1],tup[2],tup[3]
    elif len(tup) == 3 and tup[0] == "Truck":
        return -1,-1,tup[1],tup[2]
    else:
        return tup[0],tup[1],-1,-1

def getAnimationList(ship,r1,c1,r2,c2): # creates list of moves for animation
    animationList = []
    sr = r1+1
    sc = c1+1
    er = r2+1
    ec = c2+1
    if(r1 == -1 and c1 == -1): # truck to ship
        animationList.append((9,1))
        for c in range(2,ec+1):
            animationList.append((9,c))
        for r in range(8,er-1,-1):
            animationList.append((r,ec))
        return animationList

    if(r2 == -1 and c2 == -1): # ship to truck
        animationList.append((sr,sc))
        for r in range(sr+1,10):
            animationList.append((r,sc))
        for c in range(sc-1,0,-1):
            animationList.append((9,c))
        return animationList
    
    # find tops
    tops = []
    for j in range(12): # for each col
        for i in range(9,-1,-1): # for each row top down
            if (ship[i][j].desc != "UNUSED"):
                tops.append(i) # append the first actual container and break
                break
        if(len(tops) != (j+1)): # if the whole column is empty, -1 index
            tops.append(-1)
    
    maxHeight = -1
    if(c1 > c2):
        for c in range(c2,c1):
            if(tops[c]+1 > maxHeight):
                maxHeight = tops[c]+1 # find max height in between columns
        maxHeight+=1
        if(maxHeight <= sr): # dont need to go up to max height, just over and down
            for c in range(sc,ec-1,-1):
                animationList.append((sr,c))
            for r in range(sr-1,er-1,-1):
                animationList.append((r,ec))
        else: # go up to max, then over, then down
            for r in range(sr,maxHeight+1):
                animationList.append((r,sc))
            for c in range(sc-1,ec-1,-1):
                animationList.append((maxHeight,c))
            for r in range(maxHeight-1,er-1,-1):
                animationList.append((r,ec))
    else:
        for c in range(c1+1,c2+1):
            if(tops[c]+1 > maxHeight):
                maxHeight = tops[c]+1 # find max height in between columns
        maxHeight+=1
        if(maxHeight <= sr): # dont need to go up to max height, just over and down
            for c in range(sc,ec+1):
                animationList.append((sr,c))
            for r in range(sr-1,er-1,-1):
                animationList.append((r,ec))
        else: # go up to max, then over, then down
            for r in range(sr,maxHeight+1):
                animationList.append((r,sc))
            for c in range(sc+1,ec+1):
                animationList.append((maxHeight,c))
            for r in range(maxHeight-1,er-1,-1):
                animationList.append((r,ec))
    return animationList

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
                [sg.Column([[sg.Button('Login', key='login_login'), sg.Button('Cancel', key='login_cancel')]], justification='center')],
            ]
    return sg.Window("SAIL ENTERPRISE - Login", layout, size=(1000, 700), resizable=True, grab_anywhere=True, margins=(0, 0), finalize=True)

def LUloginWindow():
    #currUser : user that is logged in 
    #center items using columns : [sg.Column([ ], justification='center')]
    #adjust filename if needed for your pc -- Remember to change at production time
    #my_img = sg.Image(filename='CS179M_Project/img/SaIL.png', key='-sail_logo-')
    my_img = sg.Image(filename=(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img', 'SaIL.png')), key='-sail_logo-')
    
    layout =[
                [sg.Column([[my_img]], justification='center')],
                [sg.Column([[sg.Text('Enter username: ', font=body_font)]], justification='center')],  
                [sg.Column([[sg.Input(justification='center', key='-usrnmLU-')]], justification='center')], 
                [sg.Column([[sg.Button('Login', key='LUlogin_login'), sg.Button('Cancel', key='LUlogin_cancel')]], justification='center')],
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
                [sg.Column([[sg.Button('Start New Load/Unload', key='main_LU')]], justification='center')],  
                [sg.Column([[sg.Button('Start New Balancing Job', key='main_Bal')]], justification='center')],
                [sg.Column([[sg.Button('Login', key='main_login')]], justification='center')],
            ]
    return sg.Window("SAIL ENTERPRISE - Select Job", layout1, size=(1000, 700), resizable=True, grab_anywhere=True, margins=(0, 0), finalize=True)

#---------------UPLOAD MANIFEST METHOD------------------------------------
def uploadManifest(): 
    layout =[
                [sg.Column([[sg.Text('Current User: ' + currUser ,font=body_font)]], justification='left')],    
                [sg.Column([[sg.Text('\n\n Upload Manifest: ', font=heading_font)]], justification='center')],   
                [sg.Column([[sg.Text("Choose a file: "), sg.Input(), sg.FileBrowse(key="-manifest-")]], justification='center')],  
                [sg.Column([[sg.Button('Submit Manifest', key='upload_submit')]], justification='center')],
                [sg.Column([[sg.Button('View Manifest', key='upload_view')]], justification='center')],
                [sg.Column([[sg.Button('Cancel', key='upload_cancel')]], justification='center')],
                [sg.Column([[sg.Multiline('', size=(200, 100), font=body_font, key = '_text2_', visible = True)]], justification='center')],
            ]
    return sg.Window("SAIL ENTERPRISE - Upload Manifest", layout, size=(1000, 700), resizable=True, grab_anywhere=True, margins=(0, 0), finalize=True)

#---------------INTERACTIVE GRID METHOD------------------------------------
def gridSelection(ship):
    layout =[
                [sg.Column([[sg.Text('Current User: ' + currUser ,font=body_font)]], justification='left')],  
                [sg.Column([[sg.Text('Ship: ' + str(shipName), font=body_font)]], justification='left')],  
                [sg.Column([[sg.Text('\nSelect Containers to Load/Unload: ', font=heading_font)]], justification='center')],   
                [sg.Column([[sg.Button(f'{row},{col}') for col in range(1,13)] for row in range(8,0,-1)], justification='center')],
                [sg.Column([[sg.Button('LOAD NEW CONTAINER', key='grid_loadNew')]], justification='center')],
                [sg.Column([[sg.Button('START', key='grid_start')]], justification='center')],
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
                [sg.Column([[sg.Button('Add Container', key='add_add'), sg.Button('Cancel', key='add_cancel')]], justification='center')],
                [sg.Column([[sg.Text('WARNING: You will not be able to change a container once it is added to the loading list',font=body_font)]], justification='Center')],
            ]
    return sg.Window("SAIL ENTERPRISE - Add New Container", layout, size=(1000, 700), resizable=True, grab_anywhere=True, margins=(0, 0), finalize=True)

#---------------ADD LOG WINDOW METHOD-------------------------------------
def addLogWindow():
    layout =[
                [sg.Column([[sg.Text('Current User: ' + currUser ,font=body_font)]], justification='left')],  
                [sg.Column([[sg.Text('Ship: ' + str(shipName), font=body_font)]], justification='left')],
                [sg.Column([[sg.Text('Enter the information to push to the log: ',font=body_font)]], justification='Center')],   
                [sg.Column([[sg.Input(justification='center', key='-dscLU-')]], justification='center')],
                [sg.Column([[sg.Button('Add Log', key='LUadd_add'), sg.Button('Cancel', key='LUadd_cancel')]], justification='center')],
                [sg.Column([[sg.Text('WARNING: You will not be able to change a log once it is added to the log',font=body_font)]], justification='Center')],
            ]
    return sg.Window("SAIL ENTERPRISE - Add New Log", layout, size=(1000, 700), resizable=True, grab_anywhere=True, margins=(0, 0), finalize=True)

#--------------- LU MOVEMENT METHOD------------------------------------
def movement(ship,r1,c1,r2,c2):
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
                [sg.Column([[sg.Text('Current User: ' + currUser ,font=body_font, key='LU_currUser')]], justification='left')],  
                [sg.Column([[sg.Text('Ship: ' + str(shipName), font=body_font)]], justification='left')],
                [sg.Column([[sg.Text('Move: ' + moveMsg, font=body_font)]], justification='center')],
                [sg.Column([[sg.Text('Description: ' + c.desc, font=body_font)]], justification='center')],
                [sg.Column([[sg.Text('Weight: ' + str(c.weight), font=body_font)]], justification='center')],   
                [sg.Column([[sg.Button(f'{str(row).zfill(2)},{str(col).zfill(2)}') for col in range(1,13)] for row in range(11,0,-1)], justification='center')],
                [sg.Column([[sg.Button('Add Log', key='LUmov_addLog'), sg.Button('NEXT', key='LUmov_next'), sg.Button('Login', key='LUmov_login')]], justification='center')],
                [sg.Column([[sg.Text('Estimated Move Time: ' + estimatedTimeMove + '\t', font=body_font), sg.Text('Estimated Total Time: ' + estimatedTimeTotal, font=body_font)]], justification='center')],
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

#---------------ALGORITHM RUNNING METHOD------------------------------------
def algorithmRunning():
    my_img = sg.Image(filename=(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img', 'SaIL.png')), key='-sail_logo-')
    
    layout =[
                [sg.Column([[my_img]], justification='center')],
                [sg.Column([[sg.Text('\nAlgorithm in Progress...',font=heading_font)]], justification='center')],
                [sg.Column([[sg.Text('Please Wait',font=heading_font)]], justification='center')],
            ]
    return sg.Window("SAIL ENTERPRISE - Algorithm in Progress", layout, size=(1000, 700), resizable=True, grab_anywhere=True, margins=(0, 0), finalize=True)

#---------------LOAD SAVED DATA------------------------------------
# Gets all .saved files
currUserFile = (os.path.join(os.path.dirname(os.path.abspath(__file__)), '.saved', 'currentUser.txt'))
selectedJobFile = (os.path.join(os.path.dirname(os.path.abspath(__file__)), '.saved', 'selectedJob.txt'))
backupManifestFile = (os.path.join(os.path.dirname(os.path.abspath(__file__)), '.saved', 'backupManifest.txt'))
backupMovesFile = (os.path.join(os.path.dirname(os.path.abspath(__file__)), '.saved', 'backupMoves.txt'))
currentMoveFile = (os.path.join(os.path.dirname(os.path.abspath(__file__)), '.saved', 'currentMove.txt'))
backupLoadsFile = (os.path.join(os.path.dirname(os.path.abspath(__file__)), '.saved', 'backupLoads.txt'))
backupTimesFile = (os.path.join(os.path.dirname(os.path.abspath(__file__)), '.saved', 'backupTimes.txt'))
totalTimeFile = (os.path.join(os.path.dirname(os.path.abspath(__file__)), '.saved', 'totalTime.txt'))
shipNameFile = (os.path.join(os.path.dirname(os.path.abspath(__file__)), '.saved', 'backupShipName.txt'))

file = open(currUserFile,'r')
currUser = file.read() # gets logged in User
file.close()
file = open(selectedJobFile,'r')
selectedJob = int(file.read()) # gets selected job
file.close()
if(selectedJob == 1): # unload was in progress
    ship = loadManifest(backupManifestFile) # retrieve ship state
    moves = pickle.load(open(backupMovesFile, 'rb')) # retrieve moves list
    file = open(currentMoveFile,'r')
    currMove = int(file.read()) # retrieve current move
    file.close()
    file = open(totalTimeFile,'r')
    estimatedTimeTotal = file.read() # retrieve total estimated time
    file.close()
    file = open(shipNameFile,'r')
    shipName = file.read() # retrieve ship name
    file.close()
    times = pickle.load(open(backupTimesFile, 'rb')) # retrieve estimated move times
    loads = retrieveBackupLoads(backupLoadsFile) # retrieve loads
    estimatedTimeMove = times[currMove] # set current moves estimated time
    r1,c1,r2,c2 = retrieveInds(moves,currMove) # gets indicies for current move
    animationList = getAnimationList(ship,r1,c1,r2,c2) # retrieves animation list
    animationInd = 1 # index of current animation (0 is already green to start)
    animationLen = len(animationList)
    jobOngoing = True # set job ongoing
    window = movement(ship,r1,c1,r2,c2) # generate window based off move and ship state
    prevWindow = None

elif(selectedJob == 2):
    ship = loadManifest(backupManifestFile) # retrieve ship state
    moves = pickle.load(open(backupMovesFile, 'rb')) # retrieve moves list
    file = open(currentMoveFile,'r')
    currMove = int(file.read()) # retrieve current move
    file.close()
    file = open(totalTimeFile,'r')
    estimatedTimeTotal = file.read() # retrieve total estimated time
    file.close()
    file = open(shipNameFile,'r')
    shipName = file.read() # retrieve ship name
    file.close()
    times = pickle.load(open(backupTimesFile, 'rb')) # retrieve estimated move times
    estimatedTimeMove = times[currMove] # set current moves estimated time
    r1,c1,r2,c2 = retrieveInds(moves,currMove) # gets indicies for current move
    animationList = getAnimationList(ship,r1,c1,r2,c2) # retrieves animation list
    animationInd = 1 # index of current animation (0 is already green to start)
    animationLen = len(animationList)
    jobOngoing = True # set job ongoing
    window = movement(ship,r1,c1,r2,c2) # generate window based off move and ship state
    prevWindow = None

else:
    window, prevWindow = selectJob(), None # start off with main window open if no job going

#--------------------MAIN EVENT LOOP---------------------------------------------------------
while True:             # Event Loop
    event, values = window.read(timeout=500)
    if event == sg.WIN_CLOSED:
        break
   
    # LOGIN Process
    if event == 'login_login': # login button on login window
        login(values['-usrnm-']) # updates currUser and logs sign in/off
        window.close()
        window = selectJob() # REDIRECT to job selection window

    elif event == 'login_cancel': # Go back button on login window
        window.close()
        window = selectJob() # REDIRECT to job selection window
    
    # JOB SELECTION process
    elif event == 'main_LU': # LU job select button on main window
        selectedJob = 1
        window.close() # closes job selection window
        window = uploadManifest()

    elif event == 'main_Bal': # Balance job select button on main window
        selectedJob = 2
        window.close() # closes job selection window
        window = uploadManifest()

    elif event == 'main_login': # Login button on main window
        window.close() # closes job selection window
        window = loginWindow()   # load login window

    # UPLOAD manifest process
    elif event == 'upload_view': # view manifest contentes before submitting
        if('' == values['-manifest-']): #see if file is selected
            sg.popup("No file selected. Select file to view.",title="File Read Error") # Error message if mainfest file invalid  
        else:
            fileM = open(values['-manifest-'])
            line = fileM.read()      
            fileM.close()
            manifestCont = '\nManifest Contents: \n' + line
            window['_text2_'].update(manifestCont)

    elif event == 'upload_submit': # submit manifest button on upload window
        manifest = values['-manifest-'] # get input
        #outputting manifest to window
        #updating window to print manifest
        ship, numNAN = loadManifest(manifest) # load manifest into array
        if(ship[0][0] == None):
            sg.popup("Invalid manifest file, try again.",title="File Read Error") # Error message if mainfest file invalid            
        else:
            manifest = os.path.basename(manifest) # get manifest file name
            numContainers = containerNum-1
            addLog("Manifest " + manifest + " is opened, there are " + str(numContainers) + " containers on the ship") # push log                
            shipName = manifest[:-4] # remove ".txt" from manifest to get ship name
            file = open(shipNameFile,'w')
            file.write(shipName)
            file.close()
            manifestCont = ''
            if selectedJob == 1:
                loads = [] # reset loads
                unloads = [] # reset unloads
                window.close()
                window = gridSelection(ship) # open grid slection if LU job
            elif selectedJob == 2: 
                window.close()
                window = algorithmRunning() # display algorith running screen
                window.perform_long_operation(lambda : Bjob(ship), '-algorithm_complete-') # performs job as a thread

    elif event == 'upload_cancel': # cancel upload button on upload window
        manifestCont = ''
        selectedJob = 0 # restore job selection
        window.close()
        window = selectJob() # REDIRECT to job selection window           

    # GRID WINDOW process
    elif event == 'grid_loadNew':       
        prevWindow = window
        prevWindow.Hide()
        window = addContainer()

    elif event.find(',') >= 0: # When a user clicks a grid button
        ind = event.find(',')
        row = int(event[0:ind])-1
        col = int(event[ind+1:])-1
        if(ship[row][col].num > 0): # find container they select and check if its a valid container
            if (row,col) not in unloads:
                unloads.append((row,col)) # add to unloads if not already selected
                numContainers -= 1
                window[event].update(button_color=("white","green"))
                loadedMsg= "Selected container \"" + ship[row][col].desc + "\" Click button again to de-select it."
                window['_text1_'].update("\nAction: " + loadedMsg)
            else:
                if numContainers == (96-numNAN): # check overflow
                    loadedMsg= "Can not de-select container \"" + ship[row][col].desc + "\" the ship can not hold any more containers"
                    window['_text1_'].update("\nWarning: " + loadedMsg)
                else:
                    unloads.remove((row,col)) # remove from unloads if button was already selected
                    numContainers += 1
                    window[event].update(button_color=("white","grey"))
                    loadedMsg= "De-select container \"" + ship[row][col].desc + "\" Click button again to select it."
                    window['_text1_'].update("\nAction: " + loadedMsg)

    elif event == 'grid_start': # NOT FINISHED
        loadedMsg = ''
        if not loads and not unloads:
            # Go to finish screen, no algorithm needs to be run
            fileName = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop', '{}OUTBOUND.txt'.format(shipName))
            grid2Manifest(ship,fileName)
            sg.popup("Job Complete! The updated manifest has been downloaded to the desktop as " + shipName + "OUTBOUND.txt. Remember to email it to the captain!",title="Success")
            addLog("Finished a Cycle. Manifest " + shipName + "OUTBOUND.txt was written to desktop, and a reminder pop-up to operator to send file was displayed.")
            window.close()
            window = selectJob() # REDIRECT to job selection window
        else:
            window.close()
            window = algorithmRunning() # display algorith running screen
            window.perform_long_operation(lambda : LUjob(ship,loads,unloads), '-algorithm_complete-') # performs job as a thread

    elif event == '-algorithm_complete-': # thread is complete
        goal = values[event] # get solution
        if(goal.g == 0):
            selectedJob = 0
            file = open(selectedJobFile,'w')
            file.write(str(selectedJob)) # backup selected job so we can start up again
            file.close()
            fileName = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop', '{}OUTBOUND.txt'.format(shipName))
            grid2Manifest(ship,fileName)
            sg.popup("Job Complete! The updated manifest has been downloaded to the desktop as " + shipName + "OUTBOUND.txt. Remember to email it to the captain!",title="Success")
            addLog("Finished a Cycle. Manifest " + shipName + "OUTBOUND.txt was written to desktop, and a reminder pop-up to operator to send file was displayed.")
            window.close()
            window = selectJob() # REDIRECT to job selection window
            continue
        estimatedTimeTotal = str(datetime.timedelta(minutes=goal.g))[:-3] # get estimated time
        moves = goal.moves # get move list
        times = goal.times # get estimated move times
        currMove = 0 # index of current move
        r1,c1,r2,c2 = retrieveInds(moves,currMove)
        animationList = getAnimationList(ship,r1,c1,r2,c2) # retrieves animation list
        animationInd = 1 # index of current animation (0 is already green to start)
        animationLen = len(animationList)
        estimatedTimeMove = times[currMove] # get current move estimated time
        file = open(selectedJobFile,'w')
        file.write(str(selectedJob)) # backup selected job so we can start up again
        file.close()
        pickle.dump(moves, open(backupMovesFile, 'wb')) # backup moves
        pickle.dump(times, open(backupTimesFile, 'wb')) # backup times
        grid2Manifest(ship,backupManifestFile) # backup ship state
        backupLoads(loads,backupLoadsFile) # backup loads
        file = open(currentMoveFile,'w')
        file.write(str(currMove)) # backup current move
        file.close()
        file = open(totalTimeFile,'w')
        file.write(estimatedTimeTotal) # backup total estimated time
        file.close()
        jobOngoing = True
        sg.popup("Algorithm Complete! Click 'OK' to begin performing the job.",title="Success")
        window.close()
        window = movement(ship,r1,c1,r2,c2) # generate window based off move and initial ship state

    # ADD CONTAINER PROCESS
    elif event == 'add_add': # add container button on add window
        description = str(values['-dsc-'])
        weight = int(values['-wgt-'])
        if (description == "") or (description.isspace()): # check empty of only whitespace
            sg.popup("Description must contain at least one character",title="Input Error")
        elif(len(description) > 256) or (weight < 0) or (weight > 99999): # check validity of inputs
            sg.popup("Invalid weight or description length",title="Input Error")
        elif (numContainers == (96-numNAN)): # check overflow
            sg.popup("The ship can not hold any more containers. Please select more containers for unload if you wish to add more loads.",title="Warning")
        else:
            c = Container() # create new container
            c.weight = weight
            c.desc = description
            c.num = containerNum
            containerNum+=1
            numContainers += 1
            loads.append(c) # add to loads
            sg.popup("Successfully added container to load list.",title="Success")
            window.close()
            window = prevWindow
            window.UnHide()

    elif event == 'add_cancel': # Cancel Button on add window
        window.close()
        window = prevWindow
        window.UnHide()

    # MOVEMENT PROCESS
    elif event == 'LUmov_next': # NEXT button in move Window
        r1,c1,r2,c2 = retrieveInds(moves,currMove)
        # make sure ship is updated with the move (since they hit next confirming they made the move)
        if r1 == -1 and c1 == -1: # load
            c = loads[-1]
            loads = loads[:-1]
            ship[r2][c2] = c # load container
            addLog("\"" + c.desc + "\" is onloaded.") # push log if onload
            backupLoads(loads,backupLoadsFile) # backup loads
        else:
            c = ship[r1][c1]
            if r2 == -1 and c2 == -1: # unload
                addLog("\"" + c.desc + "\" is offloaded.") # push log if offload
                ship[r1][c1].desc = "UNUSED" # spot is now empty
                ship[r1][c1].weight = 0
                ship[r1][c1].num = 0
            else: # internal move
                ship[r1][c1] = ship[r2][c2] # swap
                ship[r2][c2] = c
        currMove+=1
        if currMove == len(moves): # last move was completed, so we are done and can download new manifest
            jobOngoing = False
            fileName = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop', '{}OUTBOUND.txt'.format(shipName))
            grid2Manifest(ship,fileName)
            sg.popup("Job Complete! The updated manifest has been downloaded to the desktop as " + shipName + "OUTBOUND.txt. Remember to email it to the captain!",title="Success")
            addLog("Finished a Cycle. Manifest " + shipName + "OUTBOUND.txt was written to desktop, and a reminder pop-up to operator to send file was displayed.")
            selectedJob = 0
            file = open(selectedJobFile,'w')
            file.write(str(selectedJob)) # backup selected job so we default startup to main page
            file.close()
            window.close()
            window = selectJob() # REDIRECT to job selection window
        else:
            grid2Manifest(ship,backupManifestFile) # backup new ship state
            file = open(currentMoveFile,'w')
            file.write(str(currMove)) # backup current move
            file.close()
            r1,c1,r2,c2 = retrieveInds(moves,currMove)
            animationList = getAnimationList(ship,r1,c1,r2,c2) # get new animation list
            animationInd = 1 # index of current animation (0 is already green to start)
            animationLen = len(animationList)
            estimatedTimeMove = times[currMove]
            window.close()
            window = movement(ship,r1,c1,r2,c2) # else, generate new window based on new ship and next move
    
    elif event == 'LUmov_login':
        jobOngoing = False
        prevWindow = window
        prevWindow.Hide()
        window = LUloginWindow() # REDIRECT to job selection window

    elif event == 'LUlogin_login':
        login(values['-usrnmLU-']) # updates currUser and logs sign in/off
        window.close()
        window = prevWindow
        window['LU_currUser'].update('Current User: {}'.format(currUser))
        window.UnHide()
        jobOngoing = True

    elif event == 'LUlogin_cancel':
        window.close()
        window = prevWindow
        window.UnHide()
        jobOngoing = True

    elif event == 'LUmov_addLog':
        jobOngoing = False
        prevWindow = window
        prevWindow.Hide()
        window = addLogWindow()

    elif event == 'LUadd_add':
        window.close()
        window = prevWindow
        window.UnHide()
        addLog(values['-dscLU-'])
        jobOngoing = True

    elif event == 'LUadd_cancel':
        window.close()
        window = prevWindow
        window.UnHide()
        jobOngoing = True

    elif event == sg.TIMEOUT_KEY:
        if(jobOngoing):
            animationStr = str(animationList[animationInd][0]).zfill(2) + ',' + str(animationList[animationInd][1]).zfill(2)
            window[animationStr].update(button_color=("white","green")) # update current animation to green
            if(animationInd == 0):
                animationStr = str(animationList[animationLen-1][0]).zfill(2) + ',' + str(animationList[animationLen-1][1]).zfill(2)
                window[animationStr].update(button_color=("white","red")) # update ending slot back to red if it was turned green
            else:
                animationStr = str(animationList[animationInd-1][0]).zfill(2) + ',' + str(animationList[animationInd-1][1]).zfill(2)
                if(animationInd!=1) and (ship[animationList[animationInd-1][0]-1][animationList[animationInd-1][1]-1].num > 0):
                    window[animationStr].update(button_color=("white","grey")) # update previous green slot back to white
                else:
                    window[animationStr].update(button_color=("white","white")) # update previous green slot back to white
            if(animationInd == animationLen-1):
                animationInd = 0 # wraparound
            else:
                animationInd+=1 # increment index

window.close()
