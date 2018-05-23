from datetime import datetime
def func0(a):
	r=[]
	for i in a:
		if i%10==0:
			r.append(i)
def func1(a):
	r=filter(lambda x:x%10==0,a)
def stopwatch(func):
	tb=datetime.now()
	func(range(10000000))
	ta=datetime.now()
	print ta-tb #0:00:00.126109

stopwatch(func0)
stopwatch(func1)

