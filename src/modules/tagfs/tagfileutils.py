#!/usr/bin/python

import os
from tagdb import TagDB
import logging

class TagFileUtils:

	def __init__(self, config):
		debug = True
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
		tags = []
		directoryTags = []
		fileTags = []
		pos = 0

		f = open(tagfile, 'r')
		for line in f:
			tags.append(line)
		f.close()

		size = len(tags)
		if size == 0:
			self.db.resetTagsForDirectoryTo(self.mkpath(tagfile[:-5]), [])
			return

		#build list of directory tags
		while not tags[pos].startswith("[\"") and pos < size-1:
			if tags[pos] != "\n": directoryTags.append(tags[pos])
			pos+=1

		# update directory tags in the database
		logging.debug("directory tags: " + str(directoryTags))
		self.db.resetTagsForDirectoryTo(self.mkpath(tagfile[:-5]), directoryTags)
		
		# extract filename
		while pos < size-1:
			fileTags = []
			filename = tags[pos][2:-3]
			pos+=1
			if tags[pos] != "\n": fileTags.append(tags[pos])
		
			# build list of filetags
			while not tags[pos].startswith("[\"") and pos < size-1:
				pos+=1
				if tags[pos] != "\n" and not tags[pos].startswith("[\""):
					fileTags.append(tags[pos])

			# update file tags in the database
			self.db.removeAllTagsFromFile(self.mkpath(tagfile[:-4] + filename))
			for tag in fileTags:
				self.db.addTagToFile(tag, self.mkpath(tagfile[:-4] + filename))
			logging.debug("filetags for file " + filename + " : " + fileTags)

