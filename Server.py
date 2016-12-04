import SlidingWindow as window
import socket
import os
import time
import hashlib
from threading import Thread
from threading import Lock

###############################################################################
# Defining the codes that identify messages
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
FILEACK = (5).to_bytes(1, byteorder='big')

# The number of times the Server will try to send a packet before it gives up
NUMTRIES = 5

print("Flags: %s %s %s %s %s" % (FNAME, FSIZE, FREADYACK, FPACKET, FILEACK))

class Server(object):
    """
    An FTP Server implementing the Sliding Window protocol to ensure
    data reliability.

    author: Frank Derry Wanye
    author: Gloire Rubambiza

    date: 12/03/2016
    """

    def __init__(self):
        """
        Initializes a Server on the localhost with a port number of 2876.
        """

        port = input("What port number would you like to connect to?")
        print ("Creating server socket on port %d." % port)

        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.serverSocket.bind(("10.0.0.2", port))
        
        while 1:
            self.serverInstance()
    # End of __init__()
            
    def serverInstance(self):
        """
        Receives a file requested by the Client. 
        """
        self.lock = Lock()

        ###################################################################
        # Obtaining requested files from the Client
        # If wrong packet received at this time, wait until right packet 
        # is received before proceeding.
        ###################################################################
        for i in range(NUMTRIES):
            print("Waiting for file request...")
            
            (filerequest, address) = self.serverSocket.recvfrom(1024)
            
            if self.compareHash(filerequest, 1) and filerequest[0] == FNAME[0]:
                filenameLen = int.from_bytes(
                    filerequest[57:66], byteorder='big')
                filename = filerequest[66:(66 + filenameLen)].decode("UTF-8")
                print("Requested file name: %s" % filename)
                break
            
            if i == (NUMTRIES - 1):
                print("Could not receive file name from Client")
                return

        ###################################################################
        # Sending the acknowledgment to the Client, including fileSize
        ###################################################################
        filesize = os.path.getsize("files/" + filename)
        filesizePacket = []
        filesizePacket.extend(FSIZE)
        filesizePacket.extend([0]*56)
        filesizePacket.extend(filesize.to_bytes(9, byteorder='big'))
        # Attach hash to packet
        hashBytes = self.calculateHash(filesizePacket).encode("ISO-8859-1")
        print("Filesizepacket hash %s" % hashBytes)
        for i in range(56):
            filesizePacket[1 + i] = hashBytes[i]
        filesizePacket = bytes(filesizePacket)
        self.serverSocket.sendto(filesizePacket, address)
        print("Sent fileSize packet to Client")

        ######################################################################
        # Receiving ready signal from Client
        ######################################################################
        for i in range(NUMTRIES):
            print("Waiting for ready acknowledgement from Client...")
            
            (fready, address) = self.serverSocket.recvfrom(66)
            
            if fready[0] == FREADYACK[0] and self.compareHash(fready, 1):
                print("Client ready to receive file.")
                break
            else:
                self.serverSocket.sendto(filesizePacket, address)
            
            if i == (NUMTRIES - 1):
                print("Could not receive ready acknowledgement from Client")
                return
        
        self.slidingWindow = window.SlidingWindow(
            "files/" + filename, mode='Server')

        # Thread to handle sending packets to the client
        self.sendThread = Thread(target=self.HandleClients, args=(address, ))
        self.sendThread.daemon = True
        self.sendThread.start()

        # Thread to handle acknowledgments from the client
        self.ackThread = Thread(target=self.clientAcknowledgements)
        self.ackThread.daemon = True
        self.ackThread.start()

        print("Sliding Window set up on connection from %s" % address[0])
        
        self.sendThread.join()
        self.ackThread.join()
    # End of serverInstance()
        
    def HandleClients(self, address):
        '''
        Handles the transfer of the files from server to serverSocket

        TO-DO
        - Receive file request from the client - DONE
        - Read from local file and save in memory - DONE
        - Instantiate a sliding window to keep track of packets sent - DONE
        - Finish send and potentially wait for another client request

        '''
        print("Handling a Client")

        self.lock.acquire()
        packets = self.slidingWindow.getPackets()
        self.lock.release()
        while not packets == []:
            #time.sleep(1)
            print("Num packets in sliding window: %d" % len(packets))
            for packet in packets:
                self.sendFilePacket(packet, address)
            time.sleep(0.1)
            self.lock.acquire()
            packets = self.slidingWindow.getPackets()
            self.lock.release()
        print("Packets left in sliding window: %d" % len(packets))
        return
    # End of handleClients()

    def clientAcknowledgements(self):
        """
        Receives acknowledgements from the Client, and marks the sliding
        window packets as received by the Client.
        """
        while 1:
            index = self.recvFileAcknowledgement()
            
            if not index == -1:
                self.lock.acquire()
                self.slidingWindow.mark(index)
                self.lock.release()
                
                if self.slidingWindow.isDone():
                    print("Finished sending file")
                    break
            
        return
    # End of clientAcknowledgements()
    
    def sendFilePacket(self, packet, address):
        """
        Inserts the hash for a packet and sends it to the client. 
        
        :type packet: a list of bytes
        :param packet: the packet to be sent, with the hash positions zeroed out
        
        :type address: (string, int) tuple
        :param address: the address to which the packet will be sent
        """
        packet[0] = FPACKET[0]
        
        # Removing unused bytes from packet
        while packet[-1] == None:
            del packet[-1]
            
        hashBytes = self.calculateHash(packet).encode("ISO-8859-1")
        
        # Adding hash to the packet
        for i in range(56):
            packet[i + 10] = hashBytes[i]
        
        print("Sending packet: %d starting with %d" %
            (int.from_bytes(packet[1:10], byteorder='big'), packet[0]))
            
        self.serverSocket.sendto(bytes(packet), address)
    # End of sendFilePacket()
    
    def recvFileAcknowledgement(self):
        """
        Receives a file acknowledgement from the Client. Checks the hash of the 
        packet, and returns the index of the acknowledged packet if the 
        acknowledgement meets all criteria.
        """
        (packet, address) = self.serverSocket.recvfrom(66)
        
        # If it is an acknowledgement packet
        if packet[0] == FILEACK[0] and self.compareHash(packet, start=10):
            index = int.from_bytes(packet[1:10], byteorder='big')
            print("Received acknowledgment from %s for packet %d" % 
                      (address[0], index))
            return index 
        else:
            return -1
    # End of recvFileAcknowledgement()
    
    def getHash(self, packet, start=10):
        """
        Returns a string representation of the hash included in the packet.
        
        :type packet: list of bytes
        :param packet: the packet containing a hash
        
        :type start: int
        :param start: the position from which the hash function starts
        """
        if packet == None:
            print("Error: no packet given")
            return ""
            
        if len(packet) < (start + 56):
            print("Error: packet not long enough to contain hash function")
            return ""
        
        hashbytes = []
        hashbytes.extend(packet[start:(start + 56)])
        hashbytes = bytes(hashbytes)
        hashStr = hashbytes.decode("ISO-8859-1")
        return hashStr
    # End of getHash()
        
    def compareHash(self, packet, start=10):
        """
        Compares the hash included in the packet with the calculated 
        value of what the hash is supposed to be. Returns True if 
        they are the same, False if they are not, or there is an 
        error in the function parameters.
        
        :type packet: list of bytes
        :param packet: the packet containing a hash
        
        :type start: int
        :param start: the position from which the hash function starts
        """
        if packet == None:
            print("Error: no packet given")
            return False
            
        if len(packet) < (start + 56):
            print("Error: packet not long enough to contain hash function")
            return False
            
        hashStr = self.getHash(packet, start)
        
        # Convert bytes object to list - bytes object cannot be edited
        packetList = []
        packetList.extend(packet)
        
        # Zero out hash in packet
        for i in range(56):
            packetList[i + start] = 0
        
        calcHash = self.calculateHash(packetList)
        
        if hashStr == calcHash:
            return True
        else:
            print("Incorrect hash in packet. Given %s, calculated %s" %
                  (hashStr, calcHash))
            return False
    # End of compareHash()
        
    def calculateHash(self, packet):
        """
        Calculates the hash of the given packet, assuming that the bytes 
        containing the hash are already zeroed out.
        
        :type packet: a list of bytes | bytes object
        :param packet: the packet to be hashed
        
        :return type: string
        :return param: a string representation of the hash of the packet
        """
        if packet == None:
            print("Error: no packet given")
            return ""
        
        packetBytes = bytes(packet)
        #packetStr = packetBytes.decode("UTF-8")
        hashStr = hashlib.sha224(packetBytes).hexdigest()
        return hashStr
    # End of calculateHash()
        
if __name__ == "__main__":
    Server()
