#!/usr/bin/python

import pyinotify
import re
import tagdb
import os
from tagdb import *

debug = True
#
homedir = os.path.expanduser('~')
db = TagDB(homedir + "/.tagfs/db.sqlite")

wm = pyinotify.WatchManager()
mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE | pyinotify.IN_CLOSE_WRITE

class EventHandler(pyinotify.ProcessEvent):
	# a new file was created, let's update the db
	def process_IN_CREATE(self, event):
		if debug: print "Creating:", event.pathname
	
		# TODO since editors name their temp files differently, the file
		# extensions to ignore should be stored in a common place and not
		# being hardcoded here. .swp & .swpx are extensions used by vim
		if event.pathname.endswith(".swp") or event.pathname.endswith(".swpx"):
			# do nothing
			if debug: print "A temporary file has been created, ignoring..."
		elif event.name == ".tag":
			# do nothing
			if debug: print ".tag file created"
		else:
			db.addFile(event.pathname)
			curTags = db.getTagsForDirectory(event.path)
			for tag in curTags:
				db.addTagToFile(tag, event.pathname)

	# a file was removed, so let's remove it from the db aswell
	def process_IN_DELETE(self, event):
		if debug: print "Deleting:", event.pathname
		
		if event.pathname.endswith(".swp") or event.pathname.endswith(".swpx"):
			if debug: print "A temporary file has been deleted, ignoring..."
			# do  nothing
		else:
			db.removeFile(event.pathname)
			# also remove tags for that file from .tag file?

	# a file was written, let's see if it was a .tag file and update the db
	# accordingly
	def process_IN_CLOSE_WRITE(self, event):
		if event.name == ".tag":
			if debug: print "DEBUG: changes to a .tag file!"

			db.removeAllTagsFromDirectory(event.path)

			f = open(event.pathname, 'r')
			for line in f:
				if debug: print line,
				db.addTagToDirectory(line, event.path)
			f.close()


handler = EventHandler()
notifier = pyinotify.Notifier(wm, handler)

wdd = wm.add_watch('/tmp', mask, rec=True)

notifier.loop()
