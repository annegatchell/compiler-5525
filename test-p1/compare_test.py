a = True == False
b = 1 == 2
c = [1,2]
d = [1,2]
e = c == d
print e #1 True
f =  c is d
print f #2 False
c = [3,4]
d = c
e = c == d
f = c is d
print e #3 True
print f #4 True
c = {3: False, 5:True}
d = {3: False, 5: True}
e = c == d
f = c is d
print e #5 True
print f #6 False
c = [1,2]
d = {3:54}
e = c ==d 
f = c is d
print e #7 False
print f #8 False
print 1 is 1 #9 True
print 1 == 1 #10 True
print 1 is 0 #11 False
print 1 == 0 #12 False 
print 1 is True #13 False
print 1 == True #14 True
print 0 is False #15 False
print 0 == False #16 True
x = 1
y = [1]
print x is y #17 False
print x == y #18 False
print x != y #19 true
print x is 1 #20 True
print d is {3:54} #21 False
print d == {3:54} #22 True
print c is [1,2] #23 False
print c == [1,2] #24 True
z = True
print z is True #25 True
print z == True #26 True
y = 1
print y is True #27 False
print y == True #28 True