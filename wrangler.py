#!python2

from evernote.api.client import EvernoteClient
import evernote.edam.type.ttypes as Types
import evernote.edam.notestore.ttypes as NoteTypes
import ui
from time import sleep


auth_token = "S=s1:U=1dbf3:E=15c27a8ffee:C=154cff7d3f0:P=1cd:A=en-devtoken:V=2:H=9ab5e1b793ae08a980a1f8e539372447"
wrangler_note_guid = 'a741ddcd-da55-476a-83e4-6ba200a305de'

@ui.in_background
def send(sender):
	sender.superview['send_status'].text = 'Posting...'
	dialog_text = sender.superview['dialog'].text
	update_evernote_wrangler(wrangler_note_guid, dialog_text)
	sender.superview['send_status'].text = 'Posted'
	sleep(0.75)
	sender.superview['send_status'].text = 'Enter dialog text'
	
def init_evernote(dev_token):
	global noteStore
	client = EvernoteClient(token=dev_token)
	noteStore = client.get_note_store()

def get_note_guid(notebookName, noteTitle):
	global noteStore
	guid = ''
	notebooks = noteStore.listNotebooks()
	
	for notebook in notebooks:
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
					guid = note.guid
	
	return guid
	
def update_evernote_wrangler(noteGuid, text):
	global noteStore
	noteFull = noteStore.getNote(noteGuid, True, False, False, False )
	noteFull.content = '<?xml version="1.0" encoding="UTF-8"?>'
	noteFull.content += '<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">'
	noteFull.content += '<en-note>'
	noteFull.content += text
	noteFull.content += '</en-note>'
	#print(noteFull.content)
	noteStore.updateNote(noteFull)
					
init_evernote(auth_token)
#print 'guid: ' + get_note_guid('wrangler', 'currentQuery')
v = ui.load_view('wrangler').present('sheet')

