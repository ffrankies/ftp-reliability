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
    
    def __init__(self, filePath, packetSize=1024):
        """
        Initializes a SlidingWindow object, with a specified file and a 
        specified packet size.
        
        :type filePath:   String
        :param filePath:  denotes the path to the requested file
        
        :type packetSize:  int
        :param packetSize: the size of each packet to be sent
        """
        
        # The size of each packet
        self.packetSize = packetSize
        
        # The path to the requested file
        self.filePath = filePath
        
        # The actual file to be read from
        self.file = io.open(filePath)
        
        # The size of the file
        self.fileSize = os.path.getsize(filePath)
        
        # Keeps track of which packets are marked
        self.marks = [-1, -1, -1, -1, -1]
        
        # The array containing bytes 
        self.window = [None] * self.packetSize * 5;
        
        print(
            ("Initialized a sliding window with packet size: %d, for file %s" +
            " with size %d") % 
            (self.packetSize, self.filePath, self.fileSize)
        )
    # End of constructor    
    
    def arraycopy(
        self, src, destStart, dest=None, srcStart=0, length=1024):
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
            
        for index in range(srcStart, min(len(src), length)):
            dest[index - srcStart + destStart] = src[index]
    # End of arraycopy
    
    def slide(self):
        """
        Shifts the Sliding Window to the right. Shifts all the data in the
        window left by the packet size, and all the data in the marks list to 
        the left by 1, but only if the first element of marks is not -1 (has 
        been received if on the Client side, or has been acknowledged if on the 
        Server side.) Continues shifting the SlidingWindow to the right until 
        the first element of marks becomes -1. 
        """
        while self.marks[0] != -1:
            # Shift sliding window to the right
            for i in range(len(self.window) - self.packetSize):
                self.window[i] = self.window[i + self.packetSize]
            # Nullify end of sliding window
            self.arraycopy([None] * self.packetSize, 
                           len(self.window) - self.packetSize)
            #
            # TO-DO: read next bytes of file into sliding window
            # Code here
            #
            # Slide the marks list to the right
            for i in range(len(self.marks) - 1):
                self.marks[i] = self.marks[i + 1]
            self.marks[len(self.marks) - 1] = -1
            
# End of SlidingWindow class            
              
if __name__ == "__main__":
    slidingWindow = SlidingWindow(filePath="try.txt", packetSize=10)
    temp = []
    for i in range(50):
        temp.append(i)
    slidingWindow.arraycopy(temp, 0, length=50)
    print(slidingWindow.window)
    slidingWindow.marks[0] = 0
    slidingWindow.marks[1] = 5
    slidingWindow.slide()
    print(slidingWindow.window)
        
        