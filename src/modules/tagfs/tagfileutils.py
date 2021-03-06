#!/usr/bin/python
from __future__ import with_statement

import os
from tagdb import TagDB
import logging

class TagFileUtils:
	"""Helper methods to keep database and .tag files in sync"""
	def __init__(self, config):
		"Initialise with a reference to the configuration."
		self.config = config

	def getDB(self):
		"Get a reference to the database"
		db = TagDB(self.config.dbLocation)
		return db

	def mkpath(self, path):
		"Converts paths from real world paths to paths inside the items directory"
		prefix_len = len(self.config.itemsDir)
		newpath = path[prefix_len:]
		if newpath == "": newpath = "/" 
		logging.debug("original path: " + path)
		logging.debug("truncated path: " + newpath)
		return newpath

	# get directory and file tags from db and write to .tag file
	def updateTagFileFromDB(self, path):
		"This can be called after modifying the database, to keep the .tag files in sync"
		self.db = self.getDB()
		writepath = path
		path = self.mkpath(path)
		dirlist, filelist = self.db.getDirectoryItems(path)

		directoryTags = self.db.getTagsForItem(path)
		
		if path != "/":
			parent = os.path.normpath(os.path.join(path, '..'))
			directoryTags = [tag for tag in directoryTags if tag not in self.db.getTagsForItem(parent)]
		
		logging.debug("directory tags: " + str(directoryTags))

		newtagfile = '\n'.join(directoryTags)

		for f in filelist:
			fileTags = [tag for tag in self.db.getTagsForItem(f) if tag not in self.db.getTagsForItem(path)]
			logging.debug("tags for file " + f + ": " + str(fileTags))
			if not fileTags == []:
				newtagfile += "\n\n[\"" + os.path.basename(f) + "\"]\n" + '\n'.join(fileTags)
	
		logging.debug("new .tag file would be:\n" + newtagfile)
	
		compareString = ""
		f = open(writepath + "/.tag", "r")
		for line in f:
			print line,
			compareString += line
		f.close()

		if newtagfile.strip() != compareString.strip():
			logging.debug("writing new tagfile to " + writepath + "/.tag")
			f = open(writepath + "/.tag", "w")
			f.write(newtagfile)
			f.close()
			return
		logging.debug("tagfile would be the same, not writing it...")

	# parses a tagfile and updates the db
	def updateDBFromTagFile(self, tagfile):
		"This should be called after changes to a .tag-file to keep the database in sync"
		self.db = self.getDB()
		directoryTags = []
		fileTags = {}
		insertList = directoryTags
		
		with open(tagfile, 'r') as file:
			for line in file:
				# strip whitespace
				tag = line.strip()
				# skip empty lines
				if not len(tag) > 0:
					continue
				if tag.startswith('["'):
					# looks like a file section
					if tag.endswith('"]'):
						# create taglist for file and switch insertList to it
						insertList = fileTags[tag[2:-2]] = []
					else:
						# syntax error!
						pass
				else:
					# add tag to current tag-list
					insertList.append(tag)
		
		logging.debug("directory tags: " + str(directoryTags))
		self.db.resetTagsForDirectoryTo(self.mkpath(tagfile[:-5]), directoryTags)
		for file, taglist in fileTags.iteritems():
			logging.debug("filetags for file %s : %s" % (self.mkpath(tagfile[:-4])+file, taglist))
			self.db.resetTagsForFileTo(self.mkpath(tagfile[:-4])+file, taglist)
			

