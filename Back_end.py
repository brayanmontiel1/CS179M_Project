import heapq
import datetime
import numpy as np

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
    # state.prevStates
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
    initState.prevStates = []
    goal = LUsearch(initState)

def retrieveLU(state): # INCOMPLETE: retrieve loads and unloads needed from user
    state.loads = []
    state.unloads = []

def LUsearch(initState): # INCOMPLETE: A* search for LU jobs
    q = [] # priority queue
    heapq.heappush(q, ((initState.g + initState.h), initState)) # push initial state onto queue

    # Create list of checked states?

    while (len(q) > 0): # Loop while queue is not empty
        item = heapq.heappop(q)
        curState = item[1] # get current state

        if (curState.h == 0): # Test if state is the goal (all unloads gone, no loads left, no containers in temp space)
            return curState # return state as solution if true
        else:
            LUexpand(curState, q) # expand state if false

        # push back state into list of checked state?

    print("No Solution") # print error if no solution
    return

def LUexpand(state, q): # INCOMPLETE: expands given state for LU job
    tops = findTops(state)
    stateCopy = LUstateCopy(state)
    print(stateCopy.unloads)
    return

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

    copy.prevStates = [] # copies states in array with another state copy call (may be expensive, idk)
    for i in range(len(state.prevStates)):
        copy.loads.append(LUstateCopy(state.prevStates[i]))

    return copy

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