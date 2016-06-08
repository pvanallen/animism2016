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
import ui
import os
import textwrap
import requests


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

class checkWrangler (threading.Thread):
	def __init__(self, q, delay, notebook, note):
		logging.debug("ever initializing")
		threading.Thread.__init__(self)
		self.q = q
		self.delay = delay
		self.notebook = notebook
		self.note = note
		self.running = threading.Event()
		self.running.set()
		self.url = 'http://node.philvanallen.com:3000'
		self.dev_token = "S=s1:U=1dbf3:E=15c27a8ffee:C=154cff7d3f0:P=1cd:A=en-devtoken:V=2:H=9ab5e1b793ae08a980a1f8e539372447"
		self.wrangler_note_guid = 'a741ddcd-da55-476a-83e4-6ba200a305de'

	def run(self):
		# set up Evernote
		self.noteStore = init_evernote(self.dev_token)

		# loop until we get notice to terminate
		try:
			while self.running.isSet():
				#
				# get most recent queryId for wrangler
				try:
					r = requests.get(self.url + '/wrangler')
					wrangler = r.json()
					r = requests.get(self.url + '/goodtwin')
					me = r.json()
					logging.info(json.dumps(wrangler, indent=4, sort_keys=True))
					logging.info(json.dumps(me, indent=4, sort_keys=True))
				except:
					logging.info("couldn't get wrangler queryId" )

				# get our most recent queryId
				#last_query_id = get_evernote_sync()

				# if they are different, get the query from Evernote
				if wrangler['queryId'] != me['lastQuery']:
					#set_evernote_sync(wrangler['queryId'])
					pay_load = {'lastQuery': wrangler['queryId'], 'mode': 'processing'}
					r = requests.post(self.url + '/goodtwin')
					print(json.dumps(r.json(), indent=4, sort_keys=True))
					# get the query from Evernote
					text = get_evernote_wrangler(self.noteStore, self.wrangler_note_guid)
					# put the query in the queue
					self.q.put(text)

				sleep(self.delay)

		except:
			logging.debug('leaving isSet')

		logging.info("stopping...")

	def stop(self):
		self.running.clear()

def init_evernote(dev_token):
	client = EvernoteClient(token=dev_token)
	return client.get_note_store()

def get_evernote_wrangler(noteStore, noteGuid):
	noteContent = noteStore.getNoteContent(noteGuid )
	soup_html = noteContent.split('dtd">')[1] # get rid of the XML stuff
	soup = BeautifulSoup(soup_html)
	text = soup.get_text()
	text_cleaned = re.sub('[^a-zA-Z0-9 \n\.]', '', text)
	print (text,text_cleaned)
	return(text_cleaned)



def display_search_results(results):
	for result in results:
		display_text = '{}: {}\n{}\n'.format(result['Title'],result['Description'],result['Url'])
		print(display_text)
	print('===================================================\n')
	print('===================================================\n')



class ShowTableView(object):
	def __init__(self):
		self.view = ui.load_view('twin')
		self.view.present('fullscreen')
		self.view.name = 'ShowTableView'
		self.currentQuery = ""
		self.myQueue = Queue.Queue() # http://lonelycode.com/2011/02/04/python-threading-and-queues-and-why-its-awesome/
		atexit.register(self.exit_handler)
		self.view['webview1'].load_url('http://google.com')
		self.check_for_new(None)


	@ui.in_background
	def check_for_new(self, sender):
		# kick off thread to see if there are any changes on evernote
		#
		self.thread = checkWrangler(self.myQueue, 2, "wrangler", "currentQuery")
		self.thread.start()

		try:
			while True:
				# check queue to see if any changes from evernote
				if not self.myQueue.empty():
					val = self.myQueue.get()
					if val != self.currentQuery and val != '':
						self.currentQuery = val
						logging.info( "new query:\n" + val)
						self.display_search_results(None, self.bing_search(None,self.currentQuery))

				time.sleep(2)
		except KeyboardInterrupt:
			# clean up
			self.exit_handler(None)

	def display_search_results(self, sender, results):
		logging.info("in searchresults")
		#logging.info(results)
		results_lst = []

		for result in results:
			title = result['Title'] + '\n' + result['Description']
			results_lst.append({'title': title,'url': result['Url'],'image':'ionicons-alert-32'})
			#print(title)

		lst = ui.ListDataSource(results_lst)
		lst.number_of_lines = 5

		#lst = ui.ListDataSource([{'title':'none','accessory_type':'none'},
		#{'title':'checkmark','accessory_type':'checkmark'},
		#{'title':'detail_button','accessory_type':'detail_button'},
		#{'title':'detail_disclosure_button','accessory_type':'detail_disclosure_button'},
		#{'title':'disclosure_indicator','accessory_type':'disclosure_indicator'},
		#{'title':'image24 and checkmark','image':'ionicons-images-24','accessory_type':'checkmark'},
		#{'title':'image32','image':'ionicons-alert-32'},
		#{'title':'image256','image':'ionicons-alert-circled-256'},
		#{'title':'frog','image':'Frog_Face'},
		#{'title':'OwnImage','image':'Image/OwnImage.png'}])
		tv1 = self.view['tableview']
		tv1.data_source = tv1.delegate = lst
		tv1.data_source.delete_enabled = tv1.editing = False
		lst.action = self.tv1_action
		tv1.reload_data()

	#@ui.in_background
	def tv1_action(self, sender):
		info = sender.items[sender.selected_row]
		self.view['webview1'].load_url(info['url'])

	def bing_search(self, sender, query, search_type='Web', num_results=15, skip=0):
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


	def exit_handler(self, sender):
		logging.info( 'application closed')
		self.thread.stop()

ShowTableView()
