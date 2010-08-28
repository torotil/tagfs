#!/usr/bin/python

import os
import pyinotify
from tagdb import *
from time import time

debug = True

# connect to the database
homedir = os.path.expanduser('~')
db = TagDB(homedir + "/.tagfs/db.sqlite")

wm = pyinotify.WatchManager()
mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE | pyinotify.IN_CLOSE_WRITE

class EventHandler(pyinotify.ProcessEvent):

	# a new file was created
	def process_IN_CREATE(self, event):
		if debug: print "Creating:", event.pathname
		new_mtime = time()	
		# TODO since editors name their temp files differently, the file
		# extensions to ignore should be stored in a common place and not
		# being hardcoded here. .swp & .swpx are extensions used by vim
		if os.path.isdir(event.pathname):
			if debug: print "A directory has been created"
			db.addFile(event.pathname)
			db.setModtime(new_mtime)
		elif event.pathname.endswith(".swp") or event.pathname.endswith(".swpx"):
			# do nothing
			if debug: print "A temporary file has been created, ignoring..."
		elif event.name == ".tag":
			# do nothing
			if debug: print "A .tag file has been created, ignoring"
		else:
			# add the file to the db and tag it with the directory tags
			db.addFile(event.pathname)
			curTags = db.getTagsForDirectory(event.path)
			for tag in curTags:
				db.addTagToFile(tag, event.pathname)
			db.setModtime(new_mtime)

	# a file was removed, so let's remove it from the db as well
	def process_IN_DELETE(self, event):
		if debug: print "Deleting:", event.pathname
		new_mtime = time()

		# see above def
		if event.pathname.endswith(".swp") or event.pathname.endswith(".swpx"):
			# do  nothing
			if debug: print "A temporary file has been deleted, ignoring..."
		else:
			db.removeFile(event.pathname)
			db.setModtime(new_mtime)

	# a file was written, let's see if it was a .tag file and update the db
	# WISHLIST: if existing meta tags (e.g. id3 tags) are imported as well,
	# they could be handled here, e.g. if the file extension/mime type is
	# mp3, the id3 tags could be extracted and if changed written to the db
	def process_IN_CLOSE_WRITE(self, event):
		new_mtime = time()

		if event.name == ".tag":
			if debug: print "DEBUG: changes to a .tag file!"

			db.removeAllTagsFromDirectory(event.path)

			f = open(event.pathname, 'r')
			for line in f:
				if debug: print line,
				db.addTagToDirectory(line, event.path)
			
			db.setModtime(new_mtime)
			f.close()

handler = EventHandler()
notifier = pyinotify.Notifier(wm, handler)

wdd = wm.add_watch('/tmp', mask, rec=True)

notifier.loop()
