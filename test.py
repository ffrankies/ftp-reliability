# import SlidingWindow as window

# server = window.SlidingWindow('files/try.txt', mode='Server')
# print("Started the Server Sliding Window")

# client = window.SlidingWindow(
#     "saved/trysaved2.txt", mode='Client', fileSize=server.fileSize)
# print("Started the Client Sliding Window")

# packets = server.getPackets()
# while not packets == []:
#     for packet in packets:
#         print("Num packets: %d, packet to save: %s" % 
#               (len(packets), packet[10:]))
#         index = client.saveBytes(packet)
#         if index == "Done":
#             print("Done saving file")
#         index = (int.from_bytes(packet[:10], byteorder="big"))
#         server.mark(index)
#         print("Saved packet with index %d" % index)
#     packets = server.getPackets()

s = "hello"
sb = s.encode("ISO-8859-1")
sl = bytes(sb)
s2 = sb.decode("ISO-8859-1")
s2 = sl.decode("ISO-8859-1")
print(s2)