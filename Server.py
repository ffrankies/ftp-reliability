import SlidingWindow as window
import socket
import os
from threading import Thread
from threading import Lock

###############################################################################
# Defining the codes that identify messages
# TO-DO: Add flags to sent/received messages
###############################################################################
# Packet containing file name
FNAME = (1).to_bytes(1, byteorder='big')

# Packet containing file size
FSIZE = (2).to_bytes(1, byteorder='big')

# Packet signifying that the Client is ready to receive file
FREADYACK = (3).to_bytes(1, byteorder='big')

# Packet containing bytes of file
FPACKET = (4).to_bytes(1, byteorder='big')

# Packet containing file acknowledgement
FACK = (5).to_bytes(1, byteorder='big')

print("Flags: %s %s %s %s" % (FNAME, FSIZE, FREADYACK, FPACKET))

class ServerInstance(object):
    """
    A Server Instance - representing one connection between Server and Client.
    This is mostly used in order to make sure that both the sending and 
    receiving threads are accessing the same sliding window object.
    
    author: Frank Derry Wanye
    author: Gloire Rubambiza
    
    date: 11/23/2016
    """
    
    def __init__(self, clientSocket, address):
        """
        Initializes a ServerInstance with the given clientSocket.
        
        :type clientSocket: socket
        :param clientSocket: the client socket through which the file will be 
                             sent
        """
        
        self.clientSocket = clientSocket
        self.lock = Lock()
        
        ###################################################################
        # Obtaining requested files from the Client
        ###################################################################
        filerequest = clientSocket.recv(1024)
        filenameLen = int.from_bytes(filerequest[:10], byteorder='big')
        filename = filerequest[10:(10 + filenameLen)].decode("UTF-8")
        # checksum = ???
        
        ###################################################################
        # Sending the acknowledgment to the Client, including fileSize
        ###################################################################
        filesize = os.path.getsize("files/" + filename)
        filesizePacket = []
        filesizePacket.extend(FSIZE)
        filesizePacket.extend(filesize.to_bytes(10, byteorder='big'))
        # Attach checksum later
        self.clientSocket.send(filesizePacket, len(filesizePacket))
        
        ######################################################################
        # Receiving ready signal from Client
        ######################################################################
        
        self.slidingWindow = window.SlidingWindow(
            "files/" + filename, mode='Server')
        
        # Thread to handle sending packets to the client
        sendThread = Thread(target=self.HandleClients)
        sendThread.start()
        
        # Thread to handle acknowledgments from the client
        ackThread = Thread(target=self.clientAcknowledgements)
        ackThread.start()
        
        print("Sliding Window set up on connection from %s" % address)
    
    def HandleClients(self):
        '''
        Handles the transfer of the files from server to clientsocket
        
        TO-DO
        - Receive file request from the client
        - Read from local file and save in memory
        - Instantiate a sliding window to keep track of packets sent
        - Finish send and potentially wait for another client request
        
        '''
        print("Handling a Client")
        
        self.lock.acquire()
        packets = self.slidingWindow.getPackets()
        self.lock.release()
        while not packets == []:
            for packet in packets:
                print("Sending packet: %d" % 
                    int.from_bytes(packet[:10], byteorder='big'))
                self.clientSocket.send(packet[10:])
                # The marking should be done on another thread
                # The other thread essentially listens to the acknowledgements
                # from the Client
                # When the Client acknowledges a packet, it gets marked
                # The SlidingWindow therefore should be visible to both threads
            self.lock.acquire()
            packets = self.slidingWindow.getPackets()
            self.lock.release()
        return
        
    def clientAcknowledgements(self):
        """
        Receives acknowledgements from the Client, and marks the sliding 
        window packets as received by the Client.
        """
        while 1:
            acknowledgement = self.clientSocket.recv(38)
            flag = acknowledgement[:1]
            index = acknowledgement[1:10]
            # Implementation for checking will be done in part 2
            checksum = acknowledgement[10:]
            self.lock.acquire()
            self.slidingWindow.mark(int.from_bytes(index, byteorder='big'))
            self.lock.release()
        # Server receives acknowledgment packets
        # Get the index of which packet they're acknowledging
        # [Ack][10 bytes of index][checksum]
        # Server tries to mark the index in ServerWindow
        # Print out a message when mark gives -1
        return    

class Server(object):
    """
    An FTP Server implementing the Sliding Window protocol to ensure 
    data reliability.
    
    author: Frank Derry Wanye
    author: Gloire Rubambiza
    
    date: 11/23/2016
    """
    
    def __init__(self):
        """
        Initializes a Server on the localhost with a port number of 2876.
        """
        
        port = 2876
        print ("Creating server socket on port %d." % port)
        
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        serversocket.bind((socket.gethostname(), int(port)))
        serversocket.listen(5)
        
        #Create a socket and pass it on to a thread
        while 1:
            (clientsocket, address) = serversocket.accept()
            ServerInstance(clientsocket, address)

if __name__ == "__main__":
    Server()