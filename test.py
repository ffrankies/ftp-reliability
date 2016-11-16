oldList = [None] * 20
newList = [0, 1, 2, 3, 4]
newList2 = [5, 6, 7, 8, 9]
newList3 = [10, 11, 12]

def arraycopy(newarray, pos, oldarray, pos2, length):
    for i in range(pos, min(length, len(newarray))):
        oldarray[pos2] = newarray[i]
        pos2 += 1
    
class TestClass:
            
    def __init__(self, num):
        self.num = num
        self.increment()
        
    def increment(self):
        self.num += 1

    
# arraycopy(newList, 0, oldList, 0, 5)
# arraycopy(newList2, 0, oldList, 10, 5)
# arraycopy(newList3, 0, oldList, 15, 5)
# print(oldList)
t = TestClass(6)
print("T: %d" % t.num)
t.increment()
print("T: %d" % t.num)

l = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
arraycopy([None] * 5, 0, l, 5, 5)
print(l)

for i in range(5):
    print(i)