#!/usr/bin/python

import os
import pyinotify
from tagdb import *
from tagfileutils import *
from time import time

debug = True

class EventHandler(pyinotify.ProcessEvent):

	def mkpath(self, path):
		prefix_len = len(tagfsroot)
		newpath = path[prefix_len:]
		if debug: print "old " + path
		if newpath == "": newpath = "/"
		if debug: print "new " + newpath
		return newpath

#	def __init__(self):
		#self.config = config

	# a new file was created
	def process_IN_CREATE(self, event):
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
			#curTags = db.getTagsForItem(event.path)
			#if debug: print "current tags for " + event.path
			#if debug: print curTags
			#for tag in curTags:
				#if debug: print "adding tag " + tag + " to file " + event.pathname
				#db.addTagToFile(tag, event.pathname)
			db.setModtime(new_mtime)

	# a file was removed, so let's remove it from the db as well
	def process_IN_DELETE(self, event):
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
		new_mtime = time()

		if event.pathname.endswith("/.tag"):
			if debug: print "changes have been made to a .tag file"
			tfu.updateDBFromTagFile(event.pathname)
			#newTags = []

			## get the tags from the .tag file and add them to the list
			#f = open(event.pathname, 'r')
			#for line in f:
				#newTags.append(line)
			#f.close()

			## update database with the taglist
			#db.resetTagsForDirectoryTo(self.mkpath(event.path), newTags)
			db.setModtime(new_mtime)

if __name__== "__main__":
	tagfsroot = os.path.abspath("/tmp/tagfs")
	tfu = TagFileUtils()

	#connect to the database
	homedir = os.path.expanduser('~')
	db = TagDB(homedir + "/.tagfs/db.sqlite")

	db.addDirectory("/")

	wm = pyinotify.WatchManager()
	mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE | pyinotify.IN_CLOSE_WRITE
	# TODO start when mounting fs
	handler = EventHandler()
	notifier = pyinotify.Notifier(wm, handler)
	wdd = wm.add_watch(tagfsroot, mask, rec=True)
	notifier.loop()
