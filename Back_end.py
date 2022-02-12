import heapq

class Container(object):
    pass

def loadManifest(filename):
    # make 2D array (10 col x 12 row)
    # open the file
    # for each line in the file
        # get attributes, i.e.
        cont = Container()
        cont.wgt = 100
        cont.dsc = "Walmart Bicycles"
        # use position in file to fill in array with the container you just made
    # return array

class LUstate(object):
    pass
    # holds 2D ship array
    # empty buffer?
    # cost g(n) which is estimated time
    # heuristic h(n)
    # list of previous states to get here

def loadUnloadJob(initalState):
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

def LUgoal(state):
    print()

def LUexpand(state, q):
    print()