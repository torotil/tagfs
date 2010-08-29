#!/usr/bin/python

import os
import pyinotify
from tagdb import *
from time import time

debug = True

tagfsroot = "/tmp/tagfs"

# connect to the database
homedir = os.path.expanduser('~')
db = TagDB(homedir + "/.tagfs/db.sqlite")

wm = pyinotify.WatchManager()
mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE | pyinotify.IN_CLOSE_WRITE

class EventHandler(pyinotify.ProcessEvent):

	# a new file was created
	def process_IN_CREATE(self, event):
		if debug: print "Creatied:", event.pathname
		new_mtime = time()
		
		# directories need special care...
		if os.path.isdir(event.pathname):
			if debug: print "A directory has been created"
			db.addDirectory(event.pathname)
			db.setModtime(new_mtime)
		# so do temporary files (of which there could be much more)
		elif event.pathname.endswith(".swp") or event.pathname.endswith(".swpx"):
			# do nothing
			if debug: print "A temporary file has been created, ignoring..."
			return
		# we don't want to tag the .tag files
		if event.name == ".tag":
			# do nothing
			if debug: print "A .tag file has been created, ignoring"
		# now we have a file that we really wanna tag
		else:
			print "adding file " + event.pathname + " to db"
			db.addFile(event.pathname)
			curTags = db.getTagsForItem(event.path)
			if debug: print "current tags for " + event.path
			if debug: print curTags
			for tag in curTags:
				if debug: print "adding tag " + tag + " to file " + event.pathname
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

			newTags = []

			f = open(event.pathname, 'r')
			for line in f:
				newTags.append(line)
			db.setModtime(new_mtime)
			f.close()
			if debug: print newTags

			db.resetTagsForDirectoryTo(event.pathname, newTags)

handler = EventHandler()
notifier = pyinotify.Notifier(wm, handler)

wdd = wm.add_watch(tagfsroot, mask, rec=True)

notifier.loop()
