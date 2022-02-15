import heapq
import datetime

file = open(".saved/currentUser.txt", "r")
user = file.read() # Global variable to store currently logged in user

class Container(object):
    pass

class LUstate(object):
    pass
    # holds 2D ship array
    # empty buffer?
    # cost g(n) which is estimated time
    # heuristic h(n)
    # list of previous states to get here

def loadManifest(filename): # INCOMPLETE
    # make 2D array (10 col x 12 row)
    # open the file
    # for each line in the file
        # get attributes, i.e.
        cont = Container()
        cont.wgt = 100
        cont.dsc = "Walmart Bicycles"
        # use position in file to fill in array with the container you just made
    # return array

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

def loadUnloadJob(initalState): # INCOMPLETE
    q = [] # priority queue
    heapq.heappush(q, ((initalState.gn + initalState.hn), initalState)) # push initial state onto queue

    # Create list of checked states?

    while (len(q) > 0): # Loop while queue is not empty
        item = heapq.heappop(q)
        curState = item[1] # get current state

        if LUgoal(curState): # Test if state is the goal (all unloads gone, no loads left, no containers in temp space)
            return curState # return state as solution if true
        else:
            LUexpand(curState, q) # expand state if false
        
        # push back state into list of checked state?

    print("No Solution") # print error if no solution
    return

def LUgoal(state): # COMPLETE: checks goal state for load/unload job
    if(len(state.lds) > 0): # check that no loads remain
        return False
    ship = state.ship
    for i in range(8,10): # check that the top 2 temporary rows of the ship are UNUSED
        for j in range(12):
            if(ship[i][j].dsc != "UNUSED"):
                return False
    for i in range(8): # check that all containers in ship are not meant to be unloaded
        for j in range(12):
            if(ship[i][j].unl):
                return False
    return True

def LUexpand(state, q): # Incomplete
    print()

def exampleState(): # temporary function to test stuff, will delete
    ship = []
    for i in range(2):
        row = []
        for j in range(12):
            cont = Container()
            cont.dsc = "example"
            cont.wgt = 100
            cont.unl = False
            row.append(cont)
        ship.append(row)
    for i in range(8):
        row = []
        for j in range(12):
            cont = Container()
            cont.dsc = "UNUSED"
            cont.wgt = 0
            cont.unl = False
            row.append(cont)
        ship.append(row)
    state = LUstate()
    state.ship = ship
    state.lds = []
    return state