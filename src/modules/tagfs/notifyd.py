#!/usr/bin/python

import os
import pyinotify
from tagdb import TagDB
from tagfileutils import TagFileUtils
from time import time

class EventHandler(pyinotify.ProcessEvent):

	def __init__(self, config):
		self.config = config
		debug = True
		tagfsroot = self.config.itemsDir
		tfu = TagFileUtils(self.config)
		#connect to the database

		#wm = pyinotify.WatchManager()
		#mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE | pyinotify.IN_CLOSE_WRITE
		## TODO start when mounting fs
		##handler = EventHandler()
		##notifier = pyinotify.Notifier(wm, handler)
		##wdd = wm.add_watch(tagfsroot, mask, rec=True)
		##notifier.loop()

		#notifier = pyinotify.ThreadedNotifier(wm, EventHandler())
		#notifier.start()
		#wdd = wm.add_watch('/tmp', mask, rec=True)


	def getDB(self):
		db = TagDB(self.config.dbLocation)
		return db

	def mkpath(self, path):
		prefix_len = len(tagfsroot)
		newpath = path[prefix_len:]
		if newpath == "": newpath = "/" 
		if debug: print "original path: " + path
		if debug: print "truncated path: " + newpath
		return newpath

	# a new file was created
	def process_IN_CREATE(self, event):
		db = self.getDB()
		if debug: print "Created:", event.pathname
		new_mtime = time()
		
		# directories need special care...
		if os.path.isdir(event.pathname):
			if debug: print "A directory has been created"
			db.addDirectory(self.mkpath(event.pathname))
			db.setModtime(new_mtime)
			return
		# ...so do hidden files
		elif event.name.startswith("."):
			# do nothing
			if debug: print "A hidden file has been created, ignoring..."
			return
		# we have a file that we really wanna tag
		else:
			print "Adding file " + event.pathname + " to db"
			db.addFile(self.mkpath(event.pathname))
			db.setModtime(new_mtime)

	# a file was removed, so let's remove it from the db as well
	def process_IN_DELETE(self, event):
		db = self.getDB()
		if debug: print "Deleting:", event.pathname
		new_mtime = time()

		# directories need special care...
		if os.path.isdir(event.pathname):
			if debug: print "A directory has been created"
			db.removeDirectory(self.mkpath(event.pathname))
			db.setModtime(new_mtime)
			return
		elif event.name.startswith("."):
			# do nothing
			if debug: print "A hidden file has been created, ignoring..."
			return
		else:
			if debug: print "removing " + event.pathname + "from db"
			db.removeFile(self.mkpath(event.pathname))
			db.setModtime(new_mtime)

	# a file was written, let's see if it was a .tag file and update the db
	# WISHLIST: if existing meta tags (e.g. id3 tags) are imported as well,
	# they could be handled here, e.g. if the file extension/mime type is
	# mp3, the id3 tags could be extracted and if changed written to the db
	def process_IN_CLOSE_WRITE(self, event):
		db = self.getDB()
		new_mtime = time()

		if event.pathname.endswith("/.tag"):
			if debug: print "changes have been made to a .tag file"
			tfu.updateDBFromTagFile(event.pathname)
			db.setModtime(new_mtime)
