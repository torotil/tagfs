#!/usr/bin/python

import logging
import os
import pyinotify
from tagdb import TagDB
from tagfileutils import TagFileUtils
from time import time

class EventHandler(pyinotify.ProcessEvent):

	def __init__(self, config):
		logging.debug("hello world from pyinotify")
		self.config = config
		self.tagfsroot = self.config.itemsDir
		self.tfu = TagFileUtils(self.config)

	def getDB(self):
		db = TagDB(self.config.dbLocation)
		return db

	def mkpath(self, path):
		prefix_len = len(self.tagfsroot)
		newpath = path[prefix_len:]
		if newpath == "": newpath = "/" 
		return newpath

	# a new file was created
	def process_IN_CREATE(self, event):
		new_mtime = time()
		
		if event.name.startswith("."):
			# do nothing
			return
		elif os.path.isdir(event.pathname):
			logging.debug("creating directory: " + event.pathname)
			db = self.getDB()
			db.addDirectory(self.mkpath(event.pathname))
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
		new_mtime = time()

		if event.name.startswith("."):
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

	# a file was written, let's see if it was a .tag file and update the db
	# WISHLIST: if existing meta tags (e.g. id3 tags) are imported as well,
	# they could be handled here, e.g. if the file extension/mime type is
	# mp3, the id3 tags could be extracted and if changed written to the db
	def process_IN_CLOSE_WRITE(self, event):
		new_mtime = time()

		if event.pathname.endswith("/.tag"):
			logging.debug(".tagfile " + event.pathname + "was modified")
			db = self.getDB()
			self.tfu.updateDBFromTagFile(event.pathname)
			db.setModtime(new_mtime)
