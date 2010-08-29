from __future__ import with_statement

import os
import os.path
import time

from tagdb import TagDB

class OfflineUpdater:
	def __init__(self, config):
		self.config = config
	
	def scan(self, dir = None, mtime = None):
		db = TagDB(self.config.dbLocation)
		if mtime == None:
			mtime = db.getModtime()
		if dir == None:
			dir = os.path.abspath(self.config.itemsDir)
		prefix_len = len(dir)
		new_mtime = time.time()
		
		print 'starting offline update ...'		
		for root, dirs, files in os.walk(dir):
			#print root, os.path.getmtime(root)
			current_dir = root[prefix_len:]
			if current_dir == '': current_dir = '/'
			
			if os.path.getmtime(root) > mtime:
				# rescan directory
				#print 'adding directory'
				#db.addDirectory(root)
				def filenames(p):
					# convert list of path-lists to sets of filenames
					return [set([os.path.split(x)[1] for x in y]) for y in p]
					
				
				old_d, old_f = filenames(db.getDirectoryItems(current_dir))
				print 'olds', (old_d, old_f)
				cur_d, cur_f = set(dirs), set(files)
				print 'curs', (cur_d, cur_f)
				
				for f in (cur_f - old_f):
					print '\tadding file %s' % (os.path.join(current_dir, f))
					db.addFile(os.path.join(current_dir, f))
				for f in (old_f - cur_f):
					print '\tremoving file %s' % (os.path.join(current_dir, f))
					db.removeFile(os.path.join(current_dir, f))
				for f in (cur_d - old_d):
					print '\tadding dir %s' % (os.path.join(current_dir, f))
					db.addDirectory(os.path.join(current_dir, f))
				for f in (old_d - cur_d):
					print '\tremoving dir %s' % (os.path.join(current_dir, f))
					db.removeDirectory(os.path.join(current_dir, f))

			tagfile = os.path.join(root, '/.tag')
			if os.path.exists(tagfile) and os.path.getmtime(tagfile) > mtime:
				# rescan .tag file
				print 'rescan .tag file', tagfile
				with open(tagfile, 'r') as f:
					tags = [line for line in f] 
				db.resetTagsForDirectoryTo(root, tags)

		db.setModtime(new_mtime)
		print 'offline update finished.'

if __name__ == "__main__":
	c = object()
	mtime = time.mktime(time.localtime()) - 3600
	o = OfflineUpdater(c, '/tmp', mtime)
	o.scan()
			
