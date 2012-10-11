x = [3,4,True]
y = [3,4,True]
print x == y
print x is y
x[0] = False
print x
print y
x = [3,4,input()]
y = [3,4,input()]
print x == y
print x is y
x = [3,4,input()]
y = [3,4,input()]
print x == y
print x is y
a = [1,2,3]
b = a
a = [4,5,6]
print b
b = a
a[0] = 7
print b

