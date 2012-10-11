x = [1,2,3]
y = [4,5,6]
y = x + y
print y
x[1] = 99
print x
print y
y[2] = True
print y
y[3] = y[2] or y[0]
print y
y[4] = y[1] and y[2]
print y
y[5] = y[1] or y[2]
print y
z = y and False
z = y and True
z = y or False
z = y or True
z = y or []
z = y and []
z = [] and y
z = [] or y 
