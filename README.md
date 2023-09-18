# MiniLoadBalancer

This is an example of a mini proxy load balancer, developed in Python.

The Load Balancer demonstrates achieving connection to 3 servers: Two of which are servers designed to process and handle requests of type Video or Picture and a server of Music Type.

Requests from clients are sent to the Load Balancer which will send them to one of the servers, recieve a response and send the response back to the client. Requests are of type: Video, Picture or Music. Each Request is sent with its length, for each server, handling a request of its own type, the processing time is equal to the requested message's length, a Video server will take twice as long for a request of type Music, and a Music server will take twice as long for a picture request and three times as long for a video request.

In short:

| Server\Request Type | Video | Picture | Music |
| ------------------- | ----- | ------- | ----- |
| Video/Picture | x1 | x1 | x2 |
| Music | x3 | x2 | x1 |

The load balancer's job is to divide the load on all the servers such that the time needed for finishing all requests is as minimal as it can be.

Note: The time needed for finishing all requests is defined the processing time from the moment the first request is received until the last request is handled, meaning the maximum processing time between all the servers on each run.

The load balancer operates as such:

1) Establish a connection to the three servers.
2) Keep track of each server, the requests sent to him and at what time he is expected to end all the requests in its queue.
3) Listen for requests from clients.
4) On each request recieved, according to its type, decide which server to send the request to, by sending it to the server that sending the request to will minimize the "Finishing Time" (Maximum server processing time).
5) Send request to server choosen and recieve response to send back to client.

This code demonstrates Socket Programming, opening connections, listening, load balancing, managing requests queue and handling requests in a (forked) process in Python.
