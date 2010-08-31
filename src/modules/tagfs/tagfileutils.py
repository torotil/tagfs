#!/usr/bin/python
from __future__ import with_statement

import os
from tagdb import TagDB
import logging

class TagFileUtils:

	def __init__(self, config):
		self.config = config
		self.db = TagDB(self.config.dbLocation)

	def mkpath(self, path):
		prefix_len = len(self.config.itemsDir)
		newpath = path[prefix_len:]
		if newpath == "": newpath = "/" 
		logging.debug("original path: " + path)
		logging.debug("truncated path: " + newpath)
		return newpath

	# get directory and file tags from db and write to .tag file
	def updateTagFileFromDB(self, path):
		writepath = path
		path = self.mkpath(path)
		dirlist, filelist = self.db.getDirectoryItems(path)

		directoryTags = self.db.getTagsForItem(path)
		
		if path != "/":
			parent = os.path.normpath(os.path.join(path, '..'))
			directoryTags = [tag for tag in directoryTags if tag not in self.db.getTagsForItem(parent)]
		
		logging.debug("directory tags: " + directoryTags)

		newtagfile = ''.join(directoryTags)

		for f in filelist:
			fileTags = [tag for tag in self.db.getTagsForItem(f) if tag not in self.db.getTagsForItem(path)]
			logging.debug("tags for file " + f + ": " + fileTags)
			if not fileTags == []:
				newtagfile += "\n[\"" + os.path.basename(f) + "\"]\n" + ''.join(fileTags)
	
		logging.debug("new .tag file:\n" + newtagfile + "\nwriting it to " + writepath + "/.tag")
		f = open(writepath + "/.tag", "w")
		f.write(newtagfile)
		f.close()

	# parses a tagfile and updates the db
	def updateDBFromTagFile(self, tagfile):
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
				# add tag to current tag-list
				insertList.append(tag)
		
		logging.debug("directory tags: " + str(directoryTags))
		self.db.resetTagsForDirectoryTo(self.mkpath(tagfile[:-5]), directoryTags)
		for file, taglist in fileTags.iteritems():
			logging.debug("filetags for file %s : %s" % (file, taglist))
			self.db.resetTagsForFileTo(file, taglist)
			

