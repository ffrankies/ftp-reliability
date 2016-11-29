# 
# Author: Frank Derry Wanye
# Author: Gloire Rubambiza
# Date: 11/29/2016
#

import SlidingWindow as window
import socket
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

print("Flags: %s %s %s %s" % (FNAME[0], FSIZE[0], FREADYACK[0], FPACKET[0]))


port = 2876
print ("Creating connection to the server")
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
host = "127.0.0.1"


#Send the file request to the server
#while 1:
###########################################################################
# Send fileName of requested file to the Server
###########################################################################
filename = input("Please enter the name of the file you want to download " +
                 "from the Server: ")
filenameBytes = filename.encode("UTF-8")
filenameBuffer = []
filenameBuffer.extend(FNAME)
filenameBuffer.extend((len(filenameBytes)).to_bytes(9, byteorder='big'))
filenameBuffer.extend(filenameBytes)
filenameBuffer.extend([0]*(1024-10-len(filenameBytes)))
filenameBuffer = bytes(filenameBuffer)
# Will eventually attach a checksum to this before sending, resend if
# acknowledgement not received within a time limit
clientSocket.sendto(filenameBuffer, (host, port))

###########################################################################
# Receive filename acknowledgement from the Server
# Acknowledgement should contain 10 bytes of fileSize
###########################################################################
(acknowledgement, addr) = clientSocket.recvfrom(10)
while not acknowledgement[0] == FSIZE[0]:
    clientSocket.sendto(filenameBuffer, (host, port))
    (acknowledgement, addr) = clientSocket.recvfrom(10)
# Proceed or print error message depending on contents of acknowledgment
# Send again if acknowledgement not received within timeframe
fileSize = int.from_bytes(acknowledgement[1:10], byteorder='big')

# Might need a flag signalling that the server is sending file
# Else can use global variables flags, maybe.

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

# Send acknowledgment back to Server, this time with the file ready flag
clientSocket.sendto(bytes(ack), (host, port))
#
# Save file using slidingWindow
# Not sure about the while, but it's the only way to keep receiving and
# acknowledging packets at the same time
while 1:
    (packet, addr) = clientSocket.recvfrom(1024)
    index = (int).from_bytes(packet[1:10], byteorder='big')
    if packet[0] == FPACKET[0]: # If it is a file packet
        print("Received file packet %d" % index)
        # Not sure about how to check that we have not received this
        # packet previously
        packetarr = []
        packetarr.extend(packet)
        packetarr[0] = (0).to_bytes(1, byteorder='big')[0]
        bytesSent = client.saveBytes(packetarr)
        if bytesSent != -1:
            # Building acknowledgement
            acknowledgement = []
            acknowledgement.extend(FILEACK)
            acknowledgement.extend(packet[1:10])
            acknowledgement.extend([0]*28)
            clientSocket.sendto(bytes(acknowledgement), (host, port))
            print("Sent acknowledgement of packet %d" % index)
        if bytesSent == "Done":
            print("Done receiving file.")
            break;
    else:
        clientSocket.sendto(bytes(ack), (host, port))
# Need to think of way of knowing when to stop receiving
# I don't know to implement it in sliding window cuz I haven't seen saveBytes
#   method in action

# I don't think I've implemented that in slidingWindow yet...
#
