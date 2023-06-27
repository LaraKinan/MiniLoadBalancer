import socket, sys, time, threading
HTTP_PORT = 80
previous_server = 3
lock = threading.Lock()
SERV_HOST = '10.0.0.1'
servers = {'serv1': ('192.168.0.101', None), 'serv2': ('192.168.0.102', None), 'serv3': ('192.168.0.103', None)}
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


def getNextServer():
    global lock
    global previous_server
    lock.acquire()
    next_server = previous_server % 3 + 1
    previous_server = next_server
    lock.release()
    return next_server


def parseRequest(req):
    return (
     req[0], req[1])

 
def expectedTime(servID, reqType, reqTime):
    if(serverTimes['serv%d' % servID][0] == 'M' and reqType == "V"):
        return 3*int(reqTime)
    if((serverTimes['serv%d' % servID][0] == 'M' and reqType == "P") or (serverTimes['serv%d' % servID][0] == 'V' and reqType == "M")):
        return 2*int(reqTime)
    return int(reqTime)

def expectedTotalTime(servID, reqType, reqTime, reqRecvTime, time_rn):
    times = []
    for i in range(1, len(servers) + 1):
        start_time = int(reqRecvTime) if serverTimes['serv%d' % i][2] == 0 else serverTimes['serv%d' % i][2]
        if i == servID:
            if time_rn - start_time < serverTimes['serv%d' % i][1]:
                times.append( serverTimes['serv%d' % i][2] + ( (start_time + 2*serverTimes['serv%d' % i][1]) - time_rn) + expectedTime(i, reqType, reqTime))
            else:
                times.append( serverTimes['serv%d' % i][2] + serverTimes['serv%d' % i][1] + expectedTime(i, reqType, reqTime))
        else:
            times.append(serverTimes['serv%d' % i][2] + serverTimes['serv%d' % i][1])
    return max(times)

def decide(reqType, reqTime, reqRecvTime):
    time_rn = int(time.time())
    max_times = []
    for i in range(1, len(servers) + 1):
        max_times.append((expectedTotalTime(i, reqType, reqTime, reqRecvTime, time_rn), i))
    if max_times[1][0] == max_times[2][0]:
        return 2 if serverTimes['serv%d' % 2][0] == reqType else 3
    if max_times[0][0] == max_times[2][0]:
        return 1 if serverTimes['serv%d' % 1][0] == reqType else 3
    minTime, minServID = min(max_times)
    return minServID

def handle(client_socket, client_address):
    client_sock = client_socket
    req = client_sock.recv(2)
    req_type, req_time = parseRequest(req)
    reqGotAtTime = int(time.time())
    servID = decide(req_type, req_time, reqGotAtTime)
    start_time_req = reqGotAtTime if  serverTimes['serv%d' % servID][2] == 0 else serverTimes['serv%d' % servID][2]
    serverTimes['serv%d' % servID] =  (serverTimes['serv%d' % servID][0], serverTimes['serv%d' % servID][1] + expectedTime(servID, req_type, req_time), start_time_req)
    LBPrint('recieved request %s from %s, sending to %s' % (req, client_address[0], getServerAddr(servID)))
    LBPrint("For server i = " + str(servID) + str(serverTimes['serv%d' % servID][0]) + " " + str(serverTimes['serv%d' % servID][1]) + " " + str(serverTimes['serv%d' % servID][2]) + " ")
    serv_sock = getServerSocket(servID)
    serv_sock.sendall(req)
    data = serv_sock.recv(2)
    client_sock.sendall(data)
    client_sock.close()

if __name__ == '__main__':
    try:
        LBPrint('LB Started')
        LBPrint('Connecting to servers')
        for name, (addr, sock) in servers.iteritems():
            new_socket = createSocket(addr, HTTP_PORT)
            servers[name] = (
             addr, new_socket)

        my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        my_socket.bind((SERV_HOST, HTTP_PORT))
        my_socket.listen(20)

        while True:
            client_sock, client_address = my_socket.accept()
            handler = threading.Thread(target=handle, args=(client_sock, client_address))
            handler.start()
    except socket.error as msg:
        LBPrint(msg)
