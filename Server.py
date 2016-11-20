import SlidingWindow as window
import socket
from threading import Thread

port = input("Please enter a port for connection: ")
print ("Creating server socket.")

serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
serversocket.bind((socket.gethostname(), port))
serversocket.listen(2)

#Create a socket and pass it on to a thread
while 1:
    (clientsocket, address) = serversocket.accept()
    t = Thread(target=HandleClients, args=(address,))
    t.start()
    

def HandleClients(address):
    '''
    Handles the transfer of the files from server to clientsocket
    
    :type address: socket address
    :param address: the address of the client passed by the thread
    
    TO-DO
    - Receive file request from the client
    - Read from local file and save in memory
    - Instantiate a sliding window to keep track of packets sent
    - Finish send and potentially wait for another client request
    
    '''
    
    
