import random

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

provocation = random.choice(get_provocations('oblique_strategies.txt'))
print('Brian Eno: ' + provocation)
