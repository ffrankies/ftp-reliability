import SlidingWindow as window
import socket
from threading import Thread

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

print("Flags: %s %s %s %s" % (FNAME, FSIZE, FREADYACK, FPACKET))


port = 2876
print ("Creating connection to the server")
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
host = input("Please enter a host to connect to: ")
clientSocket.connect((host, port))

#Send the file request to the server
while 1:
    ###########################################################################
    # Send fileName of requested file to the Server
    ###########################################################################
    filename = input("Please enter the name of the file you want to download " +
                     "from the Server: ")
    filenameBytes = filename.encode("UTF-8")
    filenameBuffer = []
    filenameBuffer.extend((len(filenameBytes)).to_bytes(10, byteorder='big'))
    filenameBuffer.extend(filenameBytes)
    filenameBuffer.extend([0]*(1024-10-len(filenameBytes)))
    # Will eventually attach a checksum to this before sending, resend if 
    # acknowledgement not received within a time limit
    clientSocket.send(filenameBuffer)
    
    ###########################################################################
    # Receive filename acknowledgement from the Server
    # Acknowledgement should contain 10 bytes of fileSize
    ###########################################################################
    acknowledgement = clientSocket.recv(11)
    # Proceed or print error message depending on contents of acknowledgment
    # Send again if acknowledgement not received within timeframe
    fileSize = int.from_bytes(acknowledgement[1:11], byteorder='big')
    # Send same acknowledgement back to server to let it know that it can 
    # start sending file
    # Keep sending acknowledgement until server starts sending actual file
    # Might need a flag signalling that the server is sending file
    # Else can use global variables flags, maybe.
    
    ###########################################################################
    # Build sliding window, start receiving file
    ###########################################################################
    dest = input("What should the file be saved as? ")
    client = window.SlidingWindow(
        "saved/" + dest, mode='Client', fileSize=fileSize)
    #
    # Save file using slidingWindow
    # Need to think of way of knowing when to stop receiving
    # I don't think I've implemented that in slidingWindow yet...
    # 