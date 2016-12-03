# 
# Author: Frank Derry Wanye
# Author: Gloire Rubambiza
# Date: 12/03/2016
#

import SlidingWindow as window
import socket
import hashlib
from threading import Thread

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

print("Flags: %s %s %s %s" % (FNAME[0], FSIZE[0], FREADYACK[0], FPACKET[0]))


port = 2876
print ("Creating connection to the server")
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
host = "127.0.0.1"

def getHash(packet, start=10):
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
        
def calculateHash(packet):
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

def compareHash(packet, start=10):
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
        
    hashStr = getHash(packet, start)
    
    # Convert bytes object to list - bytes object cannot be edited
    packetList = []
    packetList.extend(packet)
    
    # Zero out hash in packet
    for i in range(56):
        packetList[i + start] = 0
    
    calcHash = calculateHash(packetList)
    
    if hashStr == calcHash:
        return True
    else:
        print("Incorrect hash in packet. Given %s, calculated %s" %
              (hashStr, calcHash))
        return False
# End of compareHash()

def recvFilePacket(clientSocket, counter):
    """
    Receives a file packet from the Client. Compares the hash of the file and
    passes it on to be saved if it meets all requirements.
    
    :type clientSocket: UDP socket
    :param clientSocket: the socket on which the Client receives/sends packets
    
    :type counter: int
    :param counter: keeps track of how many times the wrong packet has been
                    received from the Server.
                    
    :return type: (list, int) tuple 
    :return param: the packet converted to list format, and the index of the
                   packet.
    """
    (packet, address) = clientSocket.recvfrom(1024)
    
    if compareHash(packet, start=10):
        if packet[0] == FPACKET[0]:
            index = (int).from_bytes(packet[1:10], byteorder='big')
            print("Received file packet %d" % index)
            packetarr = []
            packetarr.extend(packet)
            packetarr[0] = (0).to_bytes(1, byteorder='big')[0]
            return (packetarr, index)
        else:
            print("Received a packet that isn't a file packet.")
            numFailed += 1
            return ([], -1)
    else:
        print("Received a corrupted packet from %s" % address[0])
        return ([], -1)
# End of recvFilePacket()

def sendFileAcknowledgement(clientSocket, packet, host, port):
    """
    Sends the acknowledgement for a saved packet, including the calculated 
    hash value.
    
    :type clientSocket: UDP socket
    :param clientSocket: the socket on which the Client receives/sends packets
    
    :type packet: list of bytes
    :param packet: the packet that is being acknowledged 
    
    :type host: string 
    :param host: the hostname to which the acknowledgement will be sent 
    
    :type port: int
    :param port: the port number on the host to which the packet will be 
                 passed
    """
    acknowledgement = []
    acknowledgement.extend(FILEACK)
    acknowledgement.extend(packet[1:10])
    acknowledgement.extend([0] * 56)
    hashBytes = calculateHash(acknowledgement).encode("ISO-8859-1")
    for i in range(56):
        acknowledgement[10 + i] = hashBytes[i]
    clientSocket.sendto(bytes(acknowledgement), (host, port))
# End of sendFileAcknowledgement()

#Send the file request to the server
while 1:
    failed = False
    
    ###########################################################################
    # Send fileName of requested file to the Server
    ###########################################################################
    filename = input("Please enter the name of the file you want to download " +
                     "from the Server: ")
    filenameBytes = filename.encode("UTF-8")
    filenameBuffer = []
    filenameBuffer.extend(FNAME)
    filenameBuffer.extend([0]*56)
    filenameBuffer.extend((len(filenameBytes)).to_bytes(9, byteorder='big'))
    filenameBuffer.extend(filenameBytes)
    filenameBuffer.extend([0]*(1024-10-56-len(filenameBytes)))
    hashBytes = calculateHash(filenameBuffer).encode("ISO-8859-1")
    for i in range(56):
        filenameBuffer[1 + i] = hashBytes[i]
    filenameBuffer = bytes(filenameBuffer)
    # Will eventually attach a checksum to this before sending, resend if
    # acknowledgement not received within a time limit
    clientSocket.sendto(filenameBuffer, (host, port))
    
    ###########################################################################
    # Receive filename acknowledgement from the Server
    # Acknowledgement should contain 10 bytes of fileSize
    ###########################################################################
    for i in range(NUMTRIES):
        print("Waiting for file request acknowledgement...")
        
        (acknowledgement, addr) = clientSocket.recvfrom(66)
        
        if compareHash(acknowledgement, 1) and acknowledgement[0] == FSIZE[0]:
            fileSize = int.from_bytes(
                acknowledgement[57:66], byteorder='big')
            print("Filesize: %d bytes" % fileSize)
            break
        
        if i == (NUMTRIES - 1):
            print("Could not receive file name acknowledgement from Server")
            failed = True
            continue
        
        clientSocket.sendto(acknowledgement, (host, port))
    
    if failed:
        continue
    
    ###########################################################################
    # Build sliding window, start receiving file
    ###########################################################################
    dest = input("What should the file be saved as? ")
    client = window.SlidingWindow(
        "saved/" + dest, mode='Client', fileSize=fileSize)
        
    # Send same acknowledgement back to server to let it know that it can
    # start sending file
    # Keep sending acknowledgement until server starts sending actual file
    ack = []
    ack.extend(acknowledgement)
    ack[0] = FREADYACK[0]
    # Zero out the hash
    for i in range(56):
        ack[i + 1] = 0
    hashBytes = calculateHash(ack).encode("ISO-8859-1")
    # Append new hash to packet
    for i in range(56):
        ack[i + 1] = hashBytes[i]
    
    # Send acknowledgment back to Server, this time with the file ready flag
    clientSocket.sendto(bytes(ack), (host, port))
    #
    # Save file using slidingWindow
    # Not sure about the while, but it's the only way to keep receiving and
    # acknowledging packets at the same time
    numFailed = 0
    while 1:
        (packetarr, index) = recvFilePacket(clientSocket, numFailed)
        if not packetarr == []:
            bytesSent = client.saveBytes(packetarr)
            if bytesSent != -1:
                sendFileAcknowledgement(clientSocket, packetarr, host, port)
                print("Sent acknowledgement of packet %d" % index)
            if bytesSent == "Done":
                print("Done receiving file.")
                break;
        else: # If it is not a file packet, send ready acknowledgement again
            if numFailed == 5: 
                print("Could not receive file packet from Server.")
                break
            clientSocket.sendto(bytes(ack), (host, port))
            numFailed += 1
    # Need to think of way of knowing when to stop receiving
    # I don't know to implement it in sliding window cuz I haven't seen saveBytes
    #   method in action

# I don't think I've implemented that in slidingWindow yet...
#
