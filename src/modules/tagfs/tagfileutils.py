#!/usr/bin/python

import os
from tagdb import TagDB

class TagFileUtils:

	def __init__(self, config):
		debug = True
		self.config = config
		db = TagDB(self.config.dbLocation)
		tagfsroot = self.config.itemsDir

	def mkpath(self, path):
		prefix_len = len(tagfsroot)
		newpath = path[prefix_len:]
		if newpath == "": newpath = "/" 
		if debug: print "original path: " + path
		if debug: print "truncated path: " + newpath
		return newpath

	# get directory and file tags from db and write to .tag file
	def updateTagFileFromDB(self, path):
		writepath = path
		path = self.mkpath(path)
		dirlist, filelist = db.getDirectoryItems(path)

		directoryTags = db.getTagsForItem(path)
		
		if path != "/":
			parent = os.path.normpath(os.path.join(path, '..'))
			directoryTags = [tag for tag in directoryTags if tag not in db.getTagsForItem(parent)]
		
		if debug: print "directory tags: ", directoryTags

		newtagfile = ''.join(directoryTags)

		for f in filelist:
			fileTags = [tag for tag in db.getTagsForItem(f) if tag not in db.getTagsForItem(path)]
			if debug: print "tags for file " + f + ": ", fileTags
			if not fileTags == []:
				newtagfile += "\n[\"" + os.path.basename(f) + "\"]\n" + ''.join(fileTags)
	
		if debug: print "new .tag file:\n" + newtagfile + "\nwriting it to " + writepath + "/.tag"
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
			db.resetTagsForDirectoryTo(self.mkpath(tagfile[:-5]), [])
			return

		#build list of directory tags
		while not tags[pos].startswith("[\"") and pos < size-1:
			if tags[pos] != "\n": directoryTags.append(tags[pos])
			pos+=1

		# update directory tags in the database
		if debug: print "directory tags: ", directoryTags
		db.resetTagsForDirectoryTo(self.mkpath(tagfile[:-5]), directoryTags)
		
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
			db.removeAllTagsFromFile(self.mkpath(tagfile[:-4] + filename))
			for tag in fileTags:
				db.addTagToFile(tag, self.mkpath(tagfile[:-4] + filename))
			if debug: print "filetags for file " + filename + " : ", fileTags

