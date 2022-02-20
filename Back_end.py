# Todo:
# 1. Account for loads when unloads are complete (push loads on every expand, not just unloads?)
# 2. Make a more accurate g(n) value by holding current crane position and accounting for how 
# long it takes to go somewhere, even if its not currently holding a container (in-hand with 1)

import heapq
import datetime
import numpy as np

entryCount = 0 # tie breaker for states with equal priority

file = open(".saved/currentUser.txt", "r")
user = file.read() # Global variable to store currently logged in user

# Classes
class Container(object):
    # container.weight
    # container.desc
    pass

class LUstate(object):
    # state.ship
    # state.g
    # state.h
    # state.loads
    # state.unloads
    # state.moves
    pass

# General Program Functions
def getManifest(): # INCOMPLETE: will get the filename from the upload
    return "manifests/exampleManifest.txt"

def loadManifest(filename): # COMPLETE: loads 2D array with manifest
    # make 2D array (10 row x 12 col)
    manifest = np.empty([10, 12], dtype = Container)
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
            manifest[col][row] = c

    # return array
    return manifest

def addLog(logText): # COMPLETE: Appends whatever is in logText to appropriate text file, automatic timestamp
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

def login(userName): # COMPLETE: updates global variable 'user' with userName, adds logs
    global user
    if user == userName:
        return
    if user != "":
        addLog(user + " signs out")
    addLog(userName + " signs in")
    user = userName
    file = open(".saved/currentUser.txt", "w")
    file.write(user)
    file.close()

# LU Main Functions
def LUjob(): # COMPLETE: initalizes state and computes the goal
    filename = getManifest()
    initState = LUstate()
    initState.ship = loadManifest(filename)
    retrieveLU(initState)
    LUheuristic(initState)
    initState.g = 0
    initState.moves = []
    goal = LUsearch(initState)
    movesList(goal)

def retrieveLU(state): # INCOMPLETE: retrieve loads and unloads needed from user
    state.loads = []
    state.unloads = [(0,0),(2,8)]

def LUsearch(initState): # COMPLETE: A* search for LU jobs
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

def LUexpand(state, q): # COMPLETE: expands given state for LU job
    global entryCount
    tops = findTops(state)
    for j in range(12): # for each column
        i = tops[j] # get row of container to move
        if((i,j) in state.unloads): # container is an unload
            copy = LUstateCopy(state)
            copy.unloads.remove((i,j)) # remove container from unloads
            copy.g += (abs(i-8) + abs(j-0) + 2) # add distance to unload container to g
            copy.ship[i][j].weight = 0 # move container
            copy.ship[i][j].desc = "UNUSED"
            copy.moves.append((i,j,"Truck")) # track move
            LUheuristic(copy) # calculate new heuristic
            heapq.heappush(q, ((copy.g + copy.h), entryCount, copy)) # push copy to queue
            entryCount+=1
            if (len(copy.loads) > 0):
                for c in range(12): # for every other column
                    r = tops[c]+1 # get placement location (1 above top)
                    if(r < 10): # Check that the col is not the max col height
                        copy2 = LUstateCopy(copy)
                        copy2.g += (abs(r-8) + abs(c-0) + 2) # add cost of load to g
                        copy2.ship[r][c].weight = copy2.loads[-1].weight # move container
                        copy2.ship[r][c].desc = copy2.loads[-1].desc
                        copy2.loads = copy2.loads[:-1] # remove container from loads
                        copy.moves.append(("Truck",r,c)) # track move   
                        LUheuristic(copy2) # calculate new heuristic
                        heapq.heappush(q, ((copy2.g + copy2.h), entryCount, copy2)) # push copy to queue
                        entryCount+=1
        else: # container is not an unload
            for c in range(12): # for every other column
                if (c != j):
                    r = tops[c]+1 # get row location of move (1 above the top)
                    if((r < 10) and (state.ship[i][j].desc != "NAN")): # Check that the col is not the max col height or top container is NAN
                        copy = LUstateCopy(state)
                        copy.g += manhattenDist(i,j,r,c,tops) # add cost of move to g
                        copy.ship[r][c].weight = copy.ship[i][j].weight # move container
                        copy.ship[r][c].desc = copy.ship[i][j].desc
                        copy.ship[i][j].weight = 0
                        copy.ship[i][j].desc = "UNUSED"
                        copy.moves.append((i,j,r,c))
                        LUheuristic(copy) # calculate new heuristic
                        heapq.heappush(q, ((copy.g + copy.h), entryCount, copy)) # push copy to queue
                        entryCount+=1

def LUheuristic(state): # COMPLETE: find h(n) of a given LUstate, store in state parameter automatically
    tops = findTops(state)
    ship = state.ship
    h = 0
    for j in range(12): # for each col
        for i in range(tops[j]+1): # for each row with filled containers
            if((i,j) in state.unloads): # check if container needs to be unloaded
                h+=(abs(i-8) + abs(j-0) + 2) # add distance to unload container
                for k in range(i+1,tops[j]+1): # for the rest of the containers in col with unload
                    if(ship[k][j].desc == "NAN"):
                        continue
                    if(ship[k][j].desc != "UNUSED") and ((k,j) in state.unloads):
                        h+=(abs(k-8) + abs(j-0) + 2) # add distance to unload container
                        continue
                    if(ship[k][j].desc != "UNUSED") and not ((k,j) in state.unloads):
                        h+=nearestColDist(k,j,tops) # add nearest distance to remove container from col
                        continue
                break

    for i in range(8,10):
        for j in range(12):
            if(ship[i][j].desc != "UNUSED"):
                h+=1 # add 1 for each container in temporary rows

    h+=(len(state.loads)*nearestLoadDist(tops)) # add nearest distance to load container for each container in loads

    state.h = h

# LU Helper Functions
def nearestColDist(r,c,tops): # COMPLETE: finds nearest manhatten to place container in another column
    if(c == 0):
        return (abs(r-(tops[c+1]+1))+1)
    if(c == 11):
        return (abs(r-(tops[c-1]+1))+1)
    return min((abs(r-(tops[c+1]+1))+1),(abs(r-(tops[c-1]+1))+1))

def nearestLoadDist(tops): # COMPLETE: finds nearest manhatten to place container being loaded
    min = float('inf')
    for j in range(12):
        val = ((abs((tops[j]+1)-8)) + abs(j-0) + 2)
        if val < min:
            min = val
    return min

def LUstateCopy(state): # COMPLETE: Copies an LU state
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

    return copy

def LUstateCheck(state, checkedStates): # COMPLETE: checks if state and states in list are equivolent (ignoring h and g values)
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
                c1 = ship[j][k]
                c2 = curShip[j][k]
                if(c1.desc != c2.desc): # containers are not equivolent, so state is not the same
                    same = False
                if(c1.weight != c2.weight): # containers are not equivolent, so state is not the same
                    same = False
        if(same): # if same, return true
            return True
        else: # else keep checking
            continue
    return False # return false if all checked states are different from states

# General Helper Function
def manhattenDist(r1,c1,r2,c2,tops): # COMPLETE: Manhatten distance between inital indexes and final indexs, taking into account you cant pass through containers
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

def findTops(state): # COMPLETE: find the top containers of every row (includes NAN containers if applicable)
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

def containerCopy(container): # COMPLETE: Copies a Container
    copy = Container()
    copy.weight = container.weight
    copy.desc = container.desc
    return copy

def movesList(state): # COMPLETE: Prints a states move list
    moves = state.moves
    for i in range(len(moves)):
        if(len(moves[i]) == 4):
            print("[%d,%d] to [%d,%d]"%(moves[i][0]+1,moves[i][1]+1,moves[i][2]+1,moves[i][3]+1))
            continue
        if(moves[i][0] == "Truck"):
            print("%s to [%d,%d]"%(moves[i][0],moves[i][1]+1,moves[i][2]+1))
        else:
            print("[%d,%d] to %s"%(moves[i][0]+1,moves[i][1]+1,moves[i][2]))
    print(state.g)



# Will run an LU job
# you have to manually change manifest path in getManifest() and loads/unloads in retrieveLU to test
LUjob()