import heapq
import datetime

file = open(".saved/currentUser.txt", "r")
user = file.read() # Global variable to store currently logged in user

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

def getManifest(): # INCOMPLETE: will get the filename from the upload
    return "exampleManifest.txt"

def loadManifest(filename): # INCOMPLETE: loads 2D array with manifest
    # make 2D array (10 col x 12 row)
    # open the file
    # for each line in the file
        # get attributes in a container struct
        # use position in file to fill in array with the container you just made
    # return array
    return

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

def LUheuristic(state): # COMPLETE: find h(n) of a given state, store in state parameter automatically
    tops = findTops(state)
    ship = state.ship
    h = 0
    for j in range(12):
        for i in range(tops[j]+1):
            if((i,j) in state.unloads):
                h+=(abs(i-8) + abs(j-0) + 2)
                for k in range(i+1,tops[j]+1):
                    if(ship[k][j].desc == "NAN"):
                        continue
                    if(ship[k][j].desc != "UNUSED") and ((k,j) in state.unloads):
                        h+=(abs(k-8) + abs(j-0) + 2)
                        continue
                    if(ship[k][j].desc != "UNUSED") and not ((k,j) in state.unloads):
                        h+=nearestColDist(k,j,tops)
                        continue
                break

    for i in range(8,10):
        for j in range(12):
            if(ship[i][j].desc != "UNUSED"):
                h+=1

    h+=(len(state.loads)*nearestLoadDist(tops)) 

    state.h = h

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
    return

def findTops(state): # COMPLETE: find the top containers of every row (includes NAN containers if applicable)
    ship = state.ship
    tops = []
    for j in range(12):
        for i in range(9,-1,-1):
            if (ship[i][j].dsc != "UNUSED"):
                tops.append(i)
                break
        if(len(tops) != (j+1)):
            tops.append(-1)
    return tops

def nearestColDist(r,c,tops): # COMPLETE: finds nearest manhatten to place container in another column
    if(c == 0):
        return (abs(r-(tops[c+1]+1))+1)
    if(c == 11):
        return (abs(r-(tops[c-1]+1))+1)
    return min((abs(r-(tops[c+1]+1))+1),(abs(r-(tops[c-1]+1))+1))

def nearestLoadDist(tops): # COMPLETE: finds nearest manhatten to place container being loaded
    min = float('inf')
    for j in range(12):
        val = ((abs(tops[j]-8)+1) + abs(j-0) + 2)
        if val < min:
            min = val
    return min

LUjob()