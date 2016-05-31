#!python2
# -*- coding: utf-8 -*-
from random import *
from time import sleep
import re
import copy
import string
import urllib
import urllib2
import json


from bs4 import BeautifulSoup
from evernote.api.client import EvernoteClient
import evernote.edam.type.ttypes as Types
import evernote.edam.notestore.ttypes as NoteTypes
from evernote.edam.error.ttypes import EDAMErrorCode
from evernote.edam.error.ttypes import EDAMSystemException
import Queue
import time
import threading # http://www.tutorialspoint.com/python/python_multithreading.htm
import atexit
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] (%(threadName)-10s) %(message)s'        )

currentQuery = ""
myQueue = Queue.Queue() # http://lonelycode.com/2011/02/04/python-threading-and-queues-and-why-its-awesome/



class checkEvernote (threading.Thread):
	def __init__(self, q, delay, notebook, note):
		logging.debug("ever initializing")
		threading.Thread.__init__(self)
		self.q = q
		self.delay = delay
		self.notebook = notebook
		self.note = note
		self.running = threading.Event()
		self.running.set()
		
	def run(self):
		dev_token = "S=s1:U=1dbf3:E=15c27a8ffee:C=154cff7d3f0:P=1cd:A=en-devtoken:V=2:H=9ab5e1b793ae08a980a1f8e539372447"
		client = EvernoteClient(token=dev_token)
		# userstore
		userStore = client.get_user_store()
		user = userStore.getUser()
		
		# notestore & notebooks
		noteStore = client.get_note_store()
		
		while self.running.isSet():
			logging.debug("getting note")
			text = get_evernote_data(noteStore, self.notebook, self.note)
			self.q.put(text)
			sleep(self.delay)
			
		logging.info("stopping")
		
	def stop(self):
		self.running.clear()
		
def get_evernote_data(noteStore, notebookName, noteTitle):
	
	try:
		syncState = noteStore.getSyncState()
	
	except EDAMSystemException, e:
		if e.errorCode == EDAMErrorCode.RATE_LIMIT_REACHED:
			logging.info("Rate limit reached, sleeping for {} seconds".format( e.rateLimitDuration))
			sleep(e.rateLimitDuration)
			return('') # no changes
		
	newSync = str(syncState.updateCount)
	currentSync = get_evernote_sync()
	if newSync == currentSync:
		return('') # no changes
	else:
		set_evernote_sync(newSync)
	
		notebooks = noteStore.listNotebooks()
		
		for notebook in notebooks:
			#print notebook.name
			# get the matching notebook
			if notebookName == notebook.name:
			
				filter = NoteTypes.NoteFilter()
				filter.notebookGuid = notebook.guid
				#filter.words = "animism"
				spec = NoteTypes.NotesMetadataResultSpec()
				spec.includeTitle = True
				notes = noteStore.findNotesMetadata(filter, 0, 100, spec)
				
				for note in notes.notes:
					# get the matching note
					if noteTitle == note.title:
						noteContent = noteStore.getNoteContent(note.guid )
						soup_html = noteContent.split('dtd">')[1] # get rid of the XML stuff
						soup = BeautifulSoup(soup_html)
						text = soup.get_text()
						text_cleaned = re.sub('[^a-zA-Z0-9 \n\.]', '', text)
						print (text,text_cleaned)
						#print(soup.prettify())
						return(text)
					
def get_evernote_sync():
	try:
		fo = open("evernote_sync.txt", "r")
		sync = fo.read()
		
	except:
		logging.info('no sync file found')
		sync = '0'
		
	else:
		fo.close()
		
	return sync
	
def set_evernote_sync(value):
	fo = open("evernote_sync.txt", "w")
	fo.write(value)
	fo.close()
	

def bing_search(query, search_type='Web', num_results=5, skip=0):
	if query == "":
		return [] # don't waste a search
	#search_type: Web, Image, News, Video
	key= 'Xbh3De6l6lwxCQtnagUah6zYqzO9oOg2WWhonJ3NVd8'
	query = urllib.quote(query)
	# create credential for authentication
	user_agent = 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; FDM; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 1.1.4322)'
	credentials = (':%s' % key).encode('base64')[:-1]
	auth = 'Basic %s' % credentials
	url = 'https://api.datamarket.azure.com/Data.ashx/Bing/Search/'+search_type+'?Query=%27'+query+'%27&$top=' + str(num_results) + '&$skip=' + str(skip) + '&$format=json'
	request = urllib2.Request(url)
	request.add_header('Authorization', auth)
	request.add_header('User-Agent', user_agent)
	request_opener = urllib2.build_opener()
	response = request_opener.open(request)
	response_data = response.read()
	json_result = json.loads(response_data)
	result_list = json_result['d']['results']
	return result_list
	
def display_search_results(results):
	for result in results:
		display_text = '{}: {}\n{}\n'.format(result['Title'],result['Description'],result['Url'])
		print(display_text)
	print('=================================\n')
	
def exit_handler():
	logging.info( '\napplication is ending!')
	thread.stop()
	
atexit.register(exit_handler)

thread = checkEvernote(myQueue, 2, "wrangler", "currentQuery")
thread.start()


try:
	while True:
		if not myQueue.empty():
			val = myQueue.get()
			if val != currentQuery and val != '':
				currentQuery = val
				logging.info( "new query:\n" + val)
				display_search_results(bing_search(currentQuery))
				
		time.sleep(2)
except KeyboardInterrupt:
	# clean up
	exit_handler()

