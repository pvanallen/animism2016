#!python2

from evernote.api.client import EvernoteClient
import evernote.edam.type.ttypes as Types
import evernote.edam.notestore.ttypes as NoteTypes
import ui

v = ui.load_view()
v.present('sheet')

auth_token = "S=s1:U=1dbf3:E=15c27a8ffee:C=154cff7d3f0:P=1cd:A=en-devtoken:V=2:H=9ab5e1b793ae08a980a1f8e539372447"

def update_evernote_data(notebookName, noteTitle, dev_token, text):

	client = EvernoteClient(token=dev_token)
	
	# userstore
	userStore = client.get_user_store()
	user = userStore.getUser()
	
	# notestore & notebooks
	noteStore = client.get_note_store()
	notebooks = noteStore.listNotebooks()
	
	for notebook in notebooks:
		# get the matching notebook
		if notebookName == notebook.name:
		
			filter = NoteTypes.NoteFilter()
			filter.notebookGuid = notebook.guid
			#filter.words = "animism"
			spec = NoteTypes.NotesMetadataResultSpec()
			spec.includeTitle = True
			notes = noteStore.findNotesMetadata(dev_token, filter, 0, 100, spec)
			
			for note in notes.notes:
				# get the matching note
				if noteTitle == note.title:
					noteFull = noteStore.getNote(dev_token, note.guid, True, False, False, False )
					noteFull.content = '<?xml version="1.0" encoding="UTF-8"?>'
					noteFull.content += '<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">'
					noteFull.content += '<en-note>'
					noteFull.content += text
					noteFull.content += '</en-note>'
					print(noteFull.content)
					noteStore.updateNote(dev_token, noteFull)
					
					
query = raw_input('Enter your query: ')
update_evernote_data("wrangler", "currentQuery", auth_token, query)

