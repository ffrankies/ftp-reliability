import io # For reading to/from files
import os # For accessing files

# The variable inside the parentheses acts like extends in Java
# Basically, SlidingWindow extends object
class SlidingWindow(object):
    """
    The SlidingWindow class is an implementation of the Sliding Window protocol
    for enforcing reliability in data communications between two nodes on the
    network. 
    Our implementation of the sliding window class builds the sliding window 
    out of a file. Using a dafault packet size of 1024, it makes use of an 
    array of 5 * 1024 bytes. Since it has access to the file, the sliding 
    window automatically slides to the right in increments of 1024 bytes once 
    the first group of 1024 bytes is acknowledged or otherwise removed. 
    """
    
    def __init__(self, filePath, packetSize=1024, mode='Server', fileSize=None):
        """
        Initializes a SlidingWindow object, with a specified file and a 
        specified packet size.
        
        :type filePath:   String
        :param filePath:  denotes the path to the requested file
        
        :type packetSize:  int
        :param packetSize: the size of each packet to be sent
        
        :type mode: string
        :param mode: determines which functionality the SlidingWindow supports. 
                     The default setting: 'Server', allows the SlidingWindow to 
                     read data from a file. The other possible setting, 
                     'Client', allows the SlidingWindow to write to a file.
                     
        :type fileSize: int
        :param fileSize: the size of the file to be transferred. This only 
                         needs to be provided if the SlidingWindow is being 
                         set up to receive a file.
        """
        
        # The size of each packet
        self.packetSize = packetSize
        
        # The path to the requested file
        self.filePath = filePath
        
        # The actual file to be read from/written to
        if mode == 'Server':
            option = 'rb'
            self.mode = mode
        if not (mode == 'Server'):
            option = 'wb' 
            self.mode = 'Client'
        self.file = io.open(filePath, option)
        
        # The size of the file
        if fileSize == None:
            self.fileSize = os.path.getsize(filePath)
        else:
            self.fileSize = fileSize
        
        # Keeps track of which packets are marked
        self.marks = {}
        
        # Keeps track of the first key of the marks dictionary
        self.start = 0
        
        # Keeps track of the last key of the marks dictionary
        self.end = 0
        
        # The array containing bytes 
        self.window = [None] * self.packetSize * 5;
        
        # Keeps track of the number of bytes read from the file
        self.bytesRead = 0
        
        # Builds the start of the Sliding Window
        if mode == 'Server':
            self._buildServerWindow()
        else:
            self._buildClientWindow()
        
        print(
            ("Initialized a sliding window with packet size: %d, for file %s" +
            " with size %d") % 
            (self.packetSize, self.filePath, self.fileSize)
        )
    # End of constructor() 
    
    def arraycopy(self, src, destStart, dest=None, srcStart=0, length=1024):
        """
        A function to copy data from one list (array) to another. Made to 
        mimic 
        
        :type src: list
        :param src: the list from which data will be copied
        
        :type srcStart: int
        :param srcStart: the index from which data will be copied
        
        :type dest: list
        :param dest: the list to which data will be copied. If it is not
                     provided, the data will be copied to the sliding window
        
        :type destStart: int
        :param destStart: the starting index to which data will be copied 
        
        :type length: int
        :param length: the amount of data to be copied would be between the 
                       length of src and this value
        """
        if dest == None:
            dest = self.window
            
        for index in range(min(len(src), length)):
            dest[index + destStart] = src[index + srcStart]
    # End of arraycopy()
    
    def slideServer(self):
        """
        Shifts the Sliding Window to the right. Shifts all the data in the
        window left by the packet size, and all the data in the marks list to 
        the left by 1, but only if the first element of marks is not -1 (has 
        been received if on the Client side, or has been acknowledged if on the 
        Server side.) Continues shifting the SlidingWindow to the right until 
        the first element of marks becomes -1. 
        """
        if not self.mode == 'Server':
            print("Error: Sliding Window not in Server mode: %s" % self.mode)
            return
        
        while self.start < self.fileSize and self.marks[self.start]:
            # Shift sliding window to the right
            for i in range(len(self.window) - self.packetSize):
                self.window[i] = self.window[i + self.packetSize]
            # Nullify end of sliding window
            self.arraycopy([None] * self.packetSize, 
                           len(self.window) - self.packetSize)
            if self.end < self.fileSize:
                # Add 10 bytes of index to the next packet
                self.arraycopy((self.end + (self.packetSize - 10)).to_bytes(
                               10, byteorder='big'), 
                               len(self.window) - self.packetSize)
            # Append next bytes of file to SlidingWindow
            self.arraycopy(self.readBytes(), 
                           len(self.window) - self.packetSize + 10)
            # Slide the marks list to the right
            del self.marks[self.start]
            self.start += (self.packetSize - 10)
            if (self.end + self.packetSize - 10) < self.fileSize:
                self.end += (self.packetSize - 10)
                self.marks[self.end] = False
    # End of slideServer()
    
    def _buildServerWindow(self):
        """
        Builds the marks dictionary and the sliding window from the file 
        specified in the initializaiton. Marks is kept at size 5. The keys for 
        the dictionary are the indexes of the first bytes of the packets. The
        values are True if those particular packets have been acknowledged/
        received, False if not. The array containing the packets to be sent, 
        window, is created by reading data from the file to be sent. 
        
        NOTE: This method is NOT meant to be called from outside this class 
        i.e. it is meant to be treated as a private method.
        """
        if not self.mode == 'Server':
            print("Error: Sliding Window is not in Server mode: %s" % self.mode)
            return
            
        for i in range(5):
            index = self.end
            if index >= self.fileSize:
                self.arraycopy([None] * self.packetSize, i * self.packetSize)
            self.marks[index] = False
            # Appends index (sized to 10 bytes) to start of packet
            self.arraycopy((index).to_bytes(10, byteorder='big'), 
                           i * self.packetSize)
            # Reads data from file and appends it to the packet
            self.arraycopy(self.readBytes(), (i * self.packetSize) + 10)
            if i < 4:
                self.end += (self.packetSize - 10)
        self.start = 0
    # End of buildServerWindow()
    
    def _buildClientWindow(self):
        """
        Builds the marks dictionary and the sliding window for the file 
        specified in the initializaiton. Marks is kept at size 5. The keys for 
        the dictionary are the indexes of the first bytes of the packets. The
        values are True if those particular packets have been acknowledged/
        received, False if not. The array containing the packets to be received, 
        window, is created to be filled with 'None' values. 
        
        NOTE: This method is NOT meant to be called from outside this class 
        i.e. it is meant to be treated as a private method.
        """
        if not self.mode == 'Client':
            print("Error: Sliding Window is not in Client mode: %s" % self.mode)
            return
        
        for i in range(5):
            index = self.end
            if index >= self.fileSize:
                self.arraycopy([None] * self.packetSize, i * self.packetSize)
            self.marks[index] = False
            # Appends index (sized to 10 bytes) to start of packet
            self.arraycopy((index).to_bytes(10, byteorder='big'), 
                           i * self.packetSize)
            # Reads data from file and appends it to the packet
            # self.arraycopy(self.readBytes(), (i * self.packetSize) + 10)
            if i < 4:
                self.end += (self.packetSize - 10)
        self.start = 0
    # End of buildClientWindow()
    
    def mark(self, index=None):
        """
        Marks the packet that starts with byte index as either acknowledged
        or received. After it marks the packet, it tries to slide the window.
        
        :type index: int
        :param index: the index of the first byte that was acknowledged or 
                      received
        """
        if index == None:
            index = self.start
        if index not in self.marks.keys():
            print("Not ready to mark this packet yet")
            return
        self.marks[index] = True
        if self.mode == 'Server':
            self.slideServer()
        else:
            self.slideClient()
    # End of mark()
    
    def slideClient(self):
        """
        Shifts the Sliding Window to the right. If first packet has been 
        received, writes first packet to file, and shifts all the data in the
        window left by the packet size, and all the data in the marks list to 
        the left by 1, but only if the first element of marks is not -1 (has 
        been received if on the Client side, or has been acknowledged if on the 
        Server side.) Continues shifting the SlidingWindow to the right until 
        the first element of marks becomes -1. 
        """
        if not self.mode == 'Client':
            print("Error: Sliding Window not in Client mode: %s" % self.mode)
            return
        
        while self.start < self.fileSize and self.marks[self.start]:
            # Save first packet to file
            temp = self.window[10:self.packetSize]
            # Get rid of None values trailing in packet
            while temp[-1] == None:
                del temp[-1]
            self.file.write(bytes(temp))
            
            # Shift sliding window to the right
            for i in range(len(self.window) - self.packetSize):
                self.window[i] = self.window[i + self.packetSize]
            # Nullify end of sliding window
            self.arraycopy([None] * self.packetSize, 
                           len(self.window) - self.packetSize)
            if self.end < self.fileSize:
                # Add 10 bytes of index to the next packet
                self.arraycopy((self.end + (self.packetSize - 10)).to_bytes(
                               10, byteorder='big'), 
                               len(self.window) - self.packetSize)
            # Slide the marks list to the right
            del self.marks[self.start]
            self.start += (self.packetSize - 10)
            if (self.end + self.packetSize - 10) < self.fileSize:
                self.end += (self.packetSize - 10)
                self.marks[self.end] = False
    # End of slideClient()
    
    def readBytes(self):
        """
        Reads (packetSize - 10) bytes from the requested file. Returns a list 
        of bytes read, or a list of size (packetSize - 10) containing None
        values if the end of file has been reached.
        """
        if not self.mode == 'Server':
            print("Error: Sliding Window not in Server mode: %s" % self.mode)
            return
        
        fileBytes = self.file.read(self.packetSize - 10)
        # if end of file has been reached
        if fileBytes == '':
            return ([None] * (self.packetSize - 10))
        temp = []
        for i in fileBytes:
            temp.append(i)
        self.bytesRead += len(temp)
        return temp
    # End of readBytes()
    
    def getPackets(self):
        """
        Returns the packets that have not been acknowledged yet, in a list. 
        The return value is a list of packets, so a list of lists.
        """
        if not self.mode == 'Server':
            print("Sliding Window not in Server mode: %s" % self.mode)
            return
        
        packets = []
        for i in range(5):
            # Move next packet to list
            packets.append(
                self.window[(i * self.packetSize):((i + 1) * self.packetSize)])
            # Get index of packet
            index = packets[-1][:10]
            # If no more packets
            if index[0] == None:
                del packets[-1]
                return packets
            # Delete packet if it is marked, or not a valid index, or an 
            # empty packet 
            index = int.from_bytes(index, byteorder='big')
            if (index not in self.marks.keys() or self.marks[index] 
                or index > self.fileSize):
                del packets[-1]
                
        return packets
    # End of getPackets()
    
    def saveBytes(self, bytes):
        """
        Saves (packetSize - 10) bytes into the buffer, at the correct place.
        """
        if bytes == None:
            print("Error: no bytes provided to be saved")
            return -1
        if not len(bytes) == (self.packetSize):
            print("Error: byte array provided is of the wrong size: %d" % 
                  self.packetSize)
            return -1
        index = bytes[:10]
        # Do nothing if packet already received/marked
        index = int.from_bytes(index, byteorder='big')
        if index not in self.marks:
            print("Received a packet when its not the packet's turn to be" +
                  "received, with index: %d" % index)
            return -1
        if self.marks[index]:
            print("Received duplicate packet.")
            return -1
        if index > self.fileSize:
            print("Index of received packet greater than file size: %d > %d" % 
                  (index, self.fileSize))
            return -1
        for i in range(5):
            windowIndex = self.start + (i * (self.packetSize - 10))
            if windowIndex == index:
                self.arraycopy(
                               src=bytes,
                               srcStart=0,
                               dest=self.window,
                               destStart=(i * self.packetSize),
                               length=self.packetSize
                              )
                self.mark(windowIndex)
                return windowIndex
        print("Error: for loop completed without saving bytes.")
        return -1
    # End of saveBytes()
# End of SlidingWindow class            
              
if __name__ == "__main__":
    # slidingWindow = SlidingWindow(filePath="trysmall.txt", packetSize=25)
    # print(slidingWindow.marks)
    # print(slidingWindow.window)
    # print(slidingWindow.bytesRead)
    # slidingWindow.mark(0)
    # print(slidingWindow.getPackets())
    # slidingWindow.mark(45)
    # print(slidingWindow.getPackets())
    sW = SlidingWindow(filePath="trysmall.txt", packetSize=25, mode='Client', fileSize=69)
    print(sW.window)
    sW.mark(0)
    print(sW.window)
        