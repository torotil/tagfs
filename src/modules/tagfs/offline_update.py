
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
			dir = self.config.itemsDir
		new_mtime = time.time()
		
		
		for root, dirs, files in os.walk(dir):
			#print root, os.path.getmtime(root)
			if os.path.getmtime(root) > mtime:
				# rescan directory
				print 'rescan directory:', root

			tagfile = os.path.join(root, '/.tag')
			if os.path.exists(tagfile) and os.path.getmtime(tagfile) > mtime:
				# rescan .tag file
				print 'rescan .tag file', root+'.tag'

		db.setModtime(new_mtime)

if __name__ == "__main__":
	c = object()
	mtime = time.mktime(time.localtime()) - 3600
	o = OfflineUpdater(c, '/tmp', mtime)
	o.scan()
			