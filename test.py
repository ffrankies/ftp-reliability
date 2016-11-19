import SlidingWindow as window

server = window.SlidingWindow('try.txt', mode='Server')
print("Started the Server Sliding Window")

client = window.SlidingWindow(
    "saved/trysaved.txt", mode='Client', fileSize=server.fileSize)
print("Started the Client Sliding Window")
    
packets = server.getPackets()
while not packets == []:
    for packet in packets:
        print("Packet to save: %s" % packet[10:])
        index = client.saveBytes(packet)
        server.mark(index)
        print("Saved packet with index %d" % index)
    packets = server.getPackets()