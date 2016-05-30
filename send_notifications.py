import random
import notification


minute = 60
hour = minute*60
day = hour*24
week = day*7

def get_provocations(file_name):
	try:
		fo = open(file_name, "r")
		provocations = fo.read().split('\n')

	except:
		logging.info('no sync file found')
		provocations = ['None found']

	else:
		fo.close()

	return provocations
	
provocations = get_provocations('oblique_strategies.txt')

for i in range(4):
	delay = (10 * minute) + (i * (10 * minute))
	provocation = 'Eno: ' + random.choice(provocations)
	print(str(delay) + ' ' + provocation)
	notification.schedule(provocation,delay)
