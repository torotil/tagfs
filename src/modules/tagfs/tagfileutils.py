#!/usr/bin/python

import os
from tagdb import *

debug = True
tagfsroot = os.path.abspath("/tmp/tagfs")

#connect to the database
homedir = os.path.expanduser('~')
db = TagDB(homedir + "/.tagfs/db.sqlite")

class TagFileUtils:

	def mkpath(self, path):
		prefix_len = len(tagfsroot)
		newpath = path[prefix_len:]
		if newpath == "": newpath = "/" 
		if debug: print "original path: " + path
		if debug: print "truncated path: " + newpath
		return newpath

	# appends a number of tags to the tagfiles directory section
	def appendDirectoryTags(self, tagfile, taglist):
		return

	# appends a number of tags to a file
	def appendFileTags(self, tagfile, filetotag, taglist):
		return

	# removes a file and it's tag from the tagfile
	def removeFileFromTagfile(self, tagfile):
		return

	# removes one or more tags from a file entry
	def removeFileTagsFromTagfile(self, tagfile, file, taglist):
		return
	
	# removes one or more tags from the directory section of a tagfile
	def removeDirectoryTags(self, tagfile, taglist):
		return

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
		
		if size == 0: return

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

