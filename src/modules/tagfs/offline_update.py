
import os
import os.path
import time

class OfflineUpdater:
	def __init__(self, config, source_dir, last_update):
		self.dir   = source_dir
		self.mtime = last_update
		self.new_mtime = time.time()
		self.config = config
	
	def scan(self):
		for root, dirs, files in os.walk(self.dir):
			#print root, os.path.getmtime(root)
			if os.path.getmtime(root) > self.mtime:
				# rescan directory
				print 'rescan directory:', root

			tagfile = os.path.join(root, '/.tag')
			if os.path.exists(tagfile) and os.path.getmtime(tagfile) > self.mtime:
				# rescan .tag file
				print 'rescan .tag file', root+'.tag'

if __name__ == "__main__":
	c = object()
	mtime = time.mktime(time.localtime()) - 3600
	o = OfflineUpdater(c, '/tmp', mtime)
	o.scan()
			