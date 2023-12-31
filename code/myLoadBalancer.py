import socket, sys, time, threading
HTTP_PORT = 80
previous_server = 3
lock = threading.Lock()
SERV_HOST = '10.0.0.1'
servers = {'serv1': ('192.168.0.101', None), 'serv2': ('192.168.0.102', None), 'serv3': ('192.168.0.103', None)}
# A dictionary that saves for each server, its type, the execution time of his requests and the start time of his first request
serverTimes = {'serv1' : ("V", 0, 0), 'serv2' : ("V", 0, 0), 'serv3' : ("M", 0, 0)}

def LBPrint(string):
    print '%s: %s-----' % (time.strftime('%H:%M:%S', time.localtime(time.time())), string)


def createSocket(addr, port):
    for res in socket.getaddrinfo(addr, port, socket.AF_UNSPEC, socket.SOCK_STREAM):
        af, socktype, proto, canonname, sa = res
        try:
            new_sock = socket.socket(af, socktype, proto)
        except socket.error as msg:
            LBPrint(msg)
            new_sock = None
            continue

        try:
            new_sock.connect(sa)
        except socket.error as msg:
            LBPrint(msg)
            new_sock.close()
            new_sock = None
            continue

        break

    if new_sock is None:
        LBPrint('could not open socket')
        sys.exit(1)
    return new_sock


def getServerSocket(servID):
    name = 'serv%d' % servID
    return servers[name][1]


def getServerAddr(servID):
    name = 'serv%d' % servID
    return servers[name][0]


def parseRequest(req):
    return (
     req[0], req[1])

# Expected time for server of id = servID to execute a specific request reqType with reqTime
def expectedTime(servID, reqType, reqTime):
    if(serverTimes['serv%d' % servID][0] == 'M' and reqType == "V"):
        return 3*int(reqTime)
    if((serverTimes['serv%d' % servID][0] == 'M' and reqType == "P") or (serverTimes['serv%d' % servID][0] == 'V' and reqType == "M")):
        return 2*int(reqTime)
    return int(reqTime)

# The expected total time of running each of the servers if the server with ID of servID receives a request reqType reqTime
# Meaning the total time until all servers finish all their requests
# reqRecvTime - The time the request was received
# The time at the moment of decision making
def expectedTotalTime(servID, reqType, reqTime, reqRecvTime, time_rn):
    times = []
    for i in range(1, len(servers) + 1):
        start_time = int(reqRecvTime) if serverTimes['serv%d' % i][2] == 0 else serverTimes['serv%d' % i][2]
        # start_time is when the server received its first request
        if i == servID:
            if time_rn - start_time < serverTimes['serv%d' % i][1]: 
                # if the server has not finished the requests "At his hands" yet
                times.append( time_rn + ( (start_time + serverTimes['serv%d' % i][1]) - time_rn) + expectedTime(i, reqType, reqTime))
            else:
                times.append( time_rn + expectedTime(i, reqType, reqTime))
        else:
            times.append(start_time + serverTimes['serv%d' % i][1])
    return max(times) # return the max over all the servers time

# The function that decides for each reqType reqTime, received at reqRecvTime, the server it will send to
def decide(reqType, reqTime, reqRecvTime):
    time_rn = int(time.time())
    max_times = []
    # The expected total run time of servers if the request was handed to server i
    for i in range(1, len(servers) + 1):
        max_times.append((expectedTotalTime(i, reqType, reqTime, reqRecvTime, time_rn), i))
    minTime, minServID = min(max_times) # We want the minimum of this

    # In case of equality i.e. two options are equal from the perspective of the servers, find the optimal one
    # If sending a request to a video server or a music server is equal, send to the one matching the request type
    if max_times[1][0] == max_times[2][0] and minTime == max_times[1][0]:
        return 2 if serverTimes['serv%d' % 2][0] == 'V' and (reqType == 'V' or reqType == 'P') else 3
    if max_times[0][0] == max_times[2][0] and minTime == max_times[0][0]:
        return 1 if serverTimes['serv%d' % 1][0] == 'V' and (reqType == 'V' or reqType == 'P') else 3
    
    # If sending a request to two video servers is equal (because the music server's time overshadows them), send to the one who will finish first
    if max_times[0][0] == max_times[1][0] and minTime == max_times[0][0]:
        start_time1 = int(reqRecvTime) if serverTimes['serv%d' % 1][2] == 0 else serverTimes['serv%d' % 1][2]
        diff1=0
        if time_rn - start_time1 < serverTimes['serv%d' % 1][1]:
            diff1 =  (start_time1 + serverTimes['serv%d' % 1][1]) - time_rn
        e1 = time_rn + expectedTime(1, reqType, reqTime) + diff1
        start_time2 = int(reqRecvTime) if serverTimes['serv%d' % 2][2] == 0 else serverTimes['serv%d' % 2][2]
        diff2=0
        if time_rn - start_time2 < serverTimes['serv%d' % 2][1]:
            diff2 =  (start_time2 + serverTimes['serv%d' % 2][1]) - time_rn
        e2 = time_rn + expectedTime(2, reqType, reqTime) + diff2
        return 1 if e1 < e2 else 2
    
    return minServID


def handle():
    if len(reqQueue) == 0:
        # No hanging requests
        return
    
    # Always access shared variable with lock in threads
    lock.acquire()
    (client_socket, client_address) = reqQueue.pop(0)
    lock.release()

    req = client_socket.recv(2)
    req_type, req_time = parseRequest(req)
    reqGotAtTime = int(time.time())

    servID = decide(req_type, req_time, reqGotAtTime)
    start_time_req = reqGotAtTime if  serverTimes['serv%d' % servID][2] == 0 else serverTimes['serv%d' % servID][2]
    
    # Update variables
    lock.acquire()
    serverTimes['serv%d' % servID] =  (serverTimes['serv%d' % servID][0], serverTimes['serv%d' % servID][1] + expectedTime(servID, req_type, req_time), start_time_req)
    lock.release()

    LBPrint('recieved request %s from %s, sending to %s' % (req, client_address[0], getServerAddr(servID)))
    serv_sock = getServerSocket(servID)
    serv_sock.sendall(req)
    data = serv_sock.recv(2)
    client_socket.sendall(data)
    client_socket.close()

def checkAllDone():
    # If all servers have completed all their requests, empty out data and reassign zero to times
    time_rn = int(time.time())
    for i in range(1, len(servers) + 1):
        if time_rn - serverTimes['serv%d' % i][2] < serverTimes['serv%d' % i][1]:
            return False
    for i in range(1, len(servers) + 1):
        serverTimes['serv%d' % i] = (serverTimes['serv%d' % i][0], 0, 0)
    return True

def acceptConn(reqQueue):
    # Accept connections and add them to shared queue
    client_sock, client_address = my_socket.accept()
    lock.acquire()
    reqQueue.append((client_sock, client_address))
    lock.release()

if __name__ == '__main__':
    try:
        LBPrint('LB Started')
        LBPrint('Connecting to servers')
        reqQueue = [] # A queue that saves all pending requests
        for name, (addr, sock) in servers.iteritems():
            new_socket = createSocket(addr, HTTP_PORT)
            servers[name] = (
             addr, new_socket)

        my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        my_socket.bind((SERV_HOST, HTTP_PORT))
        my_socket.listen(20)
        
        while True:
            checkAllDone()
            acceptConn(reqQueue)
            handler = threading.Thread(target=handle)
            handler.start()
    except socket.error as msg:
        LBPrint(msg)
