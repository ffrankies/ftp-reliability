import SlidingWindow as window
import socket

port = 2876
print ("Creating connection to the server")
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(('localhost', int(port)))

#Send the file request to the server
while 1:
    filename = input("Please enter a filename: ")
    
