#!/usr/bin/python
"Handles Events from pyinotify"
import logging
import os
import pyinotify
from tagdb import TagDB
from tagfileutils import TagFileUtils
from time import time

class EventHandler(pyinotify.ProcessEvent):
	
	def __init__(self, config, wm):
		"""Initialise an EventHandler Object with the config and the WatchManager"""
		logging.debug("hello world from pyinotify")
		self.mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE | pyinotify.IN_CLOSE_WRITE | pyinotify.IN_MOVED_TO | pyinotify.IN_MOVED_FROM
		self.config = config
		self.wm = wm
		self.tagfsroot = self.config.itemsDir
		self.tfu = TagFileUtils(self.config)

	def getDB(self):
		"Get a reference to the Database"
		db = TagDB(self.config.dbLocation)
		return db

	def mkpath(self, path):
		"Convert a path from the real filesystem to one inside your items directory"
		prefix_len = len(self.tagfsroot)
		newpath = path[prefix_len:]
		if newpath == "": newpath = "/" 
		return newpath

	# a new file was created
	def process_IN_CREATE(self, event):
		"Adds new files and directories to the database, called from pyinotify"
		new_mtime = time()
	
		if event.name.startswith("."):
			if not event.name.endswith("."):
				# do nothing
				return
		elif os.path.isdir(event.pathname):
			logging.debug("creating directory: " + event.pathname)
			db = self.getDB()
			db.addDirectory(self.mkpath(event.pathname))
			self.wm.add_watch(event.pathname, self.mask, rec=True)
			db.setModtime(new_mtime)
			return
		# we have a file that we really wanna tag
		else:
			logging.debug("creating file: " + event.pathname)
			db = self.getDB()
			db.addFile(self.mkpath(event.pathname))
			db.setModtime(new_mtime)

	# a file was removed, so let's remove it from the db as well
	def process_IN_DELETE(self, event):
		"Removes deleted files and directories from the database, called from pyinotify"
		new_mtime = time()

		if event.name.startswith("."):
			if not event.name.endswith("."):
				# do nothing
				return
		elif os.path.isdir(event.pathname):
			logging.debug("removing directory: " + event.pathname)
			db = self.getDB()
			db.removeDirectory(self.mkpath(event.pathname))
			db.setModtime(new_mtime)
			return
		else:
			logging.debug("removing file: " + event.pathname)
			db = self.getDB()
			db.removeFile(self.mkpath(event.pathname))
			db.setModtime(new_mtime)
			self.tfu.updateTagFileFromDB(event.path)

	def process_IN_MOVED_TO(self, event):
		"Updates the database when files or directories are moved. Entries of the old directory are removed, the new location is added. Directory tags get lost, file tags get transferred. Called from pyinotify."
		new_mtime = time()
		db = self.getDB()
		fileTags = [tag for tag in db.getTagsForItem(self.mkpath(event.src_pathname)) if tag not in db.getTagsForItem(self.mkpath(os.path.dirname(event.src_pathname)))]

		logging.debug("filetags for " + event.src_pathname + ": " + str(fileTags))
	
		logging.debug("removing file: " + event.src_pathname)
		db.removeFile(self.mkpath(event.src_pathname))
		
		logging.debug("creating file: " + event.pathname)
		db.addFile(self.mkpath(event.pathname))
		
		for tag in fileTags:
			db.addTagToFile(tag, self.mkpath(event.pathname))
	
		db.setModtime(new_mtime)
		
		self.tfu.updateTagFileFromDB(os.path.dirname(event.src_pathname))
		self.tfu.updateTagFileFromDB(os.path.dirname(event.pathname))

	# a file was written, let's see if it was a .tag file and update the db
	# WISHLIST: if existing meta tags (e.g. id3 tags) are imported as well,
	# they could be handled here, e.g. if the file extension/mime type is
	# mp3, the id3 tags could be extracted and if changed written to the db
	def process_IN_CLOSE_WRITE(self, event):
		"Handles modifications on .tag-files and updates the database accordingly. Called from pyinotify."
		new_mtime = time()

		if event.pathname.endswith("/.tag"):
			logging.debug(".tagfile " + event.pathname + "was modified")
			db = self.getDB()
			self.tfu.updateDBFromTagFile(event.pathname)
			db.setModtime(new_mtime)
