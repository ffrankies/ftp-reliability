import SlidingWindow as window
import socket
import os
import time
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

    def __init__(self, clientSocket, add):
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
        (filerequest, address) = clientSocket.recvfrom(1024)
        filenameLen = int.from_bytes(filerequest[:10], byteorder='big')
        filename = filerequest[10:(10 + filenameLen)].decode("UTF-8")
        print("Requested file name: %s" % filename)
        # checksum = ???

        ###################################################################
        # Sending the acknowledgment to the Client, including fileSize
        ###################################################################
        filesize = os.path.getsize("files/" + filename)
        filesizePacket = []
        filesizePacket.extend(FSIZE)
        filesizePacket.extend(filesize.to_bytes(10, byteorder='big'))
        filesizePacket = bytes(filesizePacket)
        # Attach checksum later
        self.clientSocket.sendto(filesizePacket, address)
        print("Sent fileSize packet to Client")

        ######################################################################
        # Receiving ready signal from Client
        ######################################################################

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

    def HandleClients(self, address):
        '''
        Handles the transfer of the files from server to clientsocket

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
            time.sleep(3)
            print("Num packets in sliding window: %d" % len(packets))
            for packet in packets:
                packet[0] = FPACKET[0]
                while packet[-1] == None:
                    del packet[-1]
                packet = bytes(packet)
                print("Sending packet: %d starting with %d" %
                    (int.from_bytes(packet[1:10], byteorder='big'), packet[0]))
                self.clientSocket.sendto(packet, address)
                # The marking should be done on another thread
                # The other thread essentially listens to the acknowledgements
                # from the Client
                # When the Client acknowledges a packet, it gets marked
                # The SlidingWindow therefore should be visible to both threads
            self.lock.acquire()
            packets = self.slidingWindow.getPackets()
            self.lock.release()
        print("Packets left in sliding window: %d" % len(packets))
        return

    def clientAcknowledgements(self):
        """
        Receives acknowledgements from the Client, and marks the sliding
        window packets as received by the Client.
        """
        while 1:
            (acknowledgement, addr) = self.clientSocket.recvfrom(38)
            print("Received acknowledgment from %s" % addr[0])
            flag = acknowledgement[:1]
            index = acknowledgement[1:10]
            # Implementation for checking will be done in part 2
            checksum = acknowledgement[10:]
            self.lock.acquire()
            self.slidingWindow.mark(int.from_bytes(index, byteorder='big'))
            self.lock.release()
            if self.slidingWindow.isDone():
                print("Finished sending file")
                break
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
        serversocket.bind(("127.0.0.1", port))

        ServerInstance(serversocket, "address")

if __name__ == "__main__":
    Server()
