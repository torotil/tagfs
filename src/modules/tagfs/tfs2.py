#!/usr/bin/env python

from __future__ import with_statement

from errno import EACCES
from os.path import realpath
from sys import argv, exit
from threading import Lock

import logging
import notifyd
import pyinotify
import sys

import os

from fuse import FUSE, FuseOSError, Operations, LoggingMixIn

from tagdb import TagDB
from stat import S_IFDIR, S_IFLNK, S_IFREG
import offline_update


class Stat:
	def __init__(self):
		self.uid = os.geteuid()
		self.gid = os.getegid()
	def fetch(self):
		d = {'st_mode':0, 'st_nlink':0, 'st_uid':self.uid, 'st_gid':self.gid }
		return d
#    def __init__(self, fs):
#        self.st_ino = 0
#        self.st_dev = 0
#        self.st_size = 0
#        self.st_atime = 0
#        self.st_mtime = 0
#        self.st_ctime = 0

class Loopback(LoggingMixIn, Operations):		
		def __init__(self, config):
				self.root = realpath(config.itemsDir)
				self.rwlock = Lock()
				self.config = config
				self.stat = Stat()
		
		def getDB(self):
			return TagDB(self.config.dbLocation)
		
		#def __call__(self, op, path, *args):
		#		return super(Loopback, self).__call__(op, self.root + path, *args)
		
		def access(self, path, mode):
				if not os.access(path, mode):
						raise FuseOSError(EACCES)
		
		chmod = os.chmod
		chown = os.chown
		
		def create(self, path, mode):
				return os.open(path, os.O_WRONLY | os.O_CREAT, mode)
		
		def flush(self, path, fh):
				return os.fsync(fh)

		def fsync(self, path, datasync, fh):
				return os.fsync(fh)
								
		def getattr(self, path, fh=None):
			parts = path.rsplit('/', 1)
			type = self.path_type(parts[0])
			db = self.getDB()
			attr = self.stat.fetch()
			if type == 'tags' and parts[1] == '':
				attr['st_mode'] |= S_IFDIR | 0500
				attr['st_nlink'] = 2
				logging.warn('for root: ' + '%s' % attr)
				return attr
			if type == 'files':
				if parts[1] not in ['OR', 'AND'] and db.isFile(path):
					attr['st_mode'] |= S_IFLNK | 0400
				else:
					attr['st_mode'] |= S_IFDIR | 0500
					attr['st_nlink'] = 2
			if type == 'tags':
				attr['st_mode'] |= S_IFDIR | 0500
				attr['st_nlink'] = 2
			if type == 'duplicates':
				attr['st_mode'] |= S_IFLNK | 0400
			logging.warn(attr)
			return attr
		
		getxattr = None
		
		def link(self, target, source):
				return os.link(source, target)
		
		listxattr = None
		mkdir = None
		mknod = None
		open = os.open
				
		def read(self, path, size, offset, fh):
				with self.rwlock:
						os.lseek(fh, offset, 0)
						return os.read(fh, size)
		
		#def readdir(self, path, fh):
		#		return ['.', '..']
		
		def readdir(self, path, fh):
			type = self.path_type(path)
			
			files = []
			if type == 'tags': 
				logging.debug('handling as tag-dir: '+path)
				files += self.getDB().getAvailableTagsForPath(path)
			if type == 'files':
				logging.debug('handling as files-dir')
				files += ['OR', 'AND']
				files += self.getDB().listFilesForPath(path)
			if type == 'duplicates':
				files = [os.path.split(x)[1] for x in self.getDB().getDuplicatePaths(path)]
			
			logging.debug('answer from database: %s' % files)
			return ['.', '..'] + files
		
		def release(self, path, fh):
				return os.close(fh)
				
		def rename(self, old, new):
				return os.rename(old, self.root + new)
		
		rmdir = os.rmdir
		
		def statfs(self, path):
				stv = os.statvfs(path)
				return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
						'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
						'f_frsize', 'f_namemax'))
		
		def symlink(self, target, source):
				logging.debug('link %s -> %s ?')
				#return os.symlink(source, target)
		
		#def truncate(self, path, length, fh=None):
		#		with open(path, 'r+') as f:
		#				f.truncate(length)
		
		#unlink = os.unlink
		#utimens = os.utime
		
		def write(self, path, data, offset, fh):
				with self.rwlock:
						os.lseek(fh, offset, 0)
						return os.write(fh, data)
		
		def path_type(self, path):
			parts = path.rsplit('/', 2)
			if parts[-1] in ['AND', 'OR', '']:
				return 'tags'
			if parts[-2] in ['', 'AND', 'OR']:
				return 'files'
			return 'duplicates'
		
		def readlink(self, path):
			if self.path_type(path.rsplit('/', 1)[0]) == 'duplicates':
				path = self.getDB().getDuplicateSourceFile(path)
			else:
				path = self.getDB().getSourceFile(path) 
			return os.path.abspath(os.path.join(self.config.itemsDir, path[1:]))
		

class Config:
	pass

def setUpLogging():
		def exceptionCallback(eType, eValue, eTraceBack):
				import cgitb

				txt = cgitb.text((eType, eValue, eTraceBack))


				logging.fatal(txt)
		
				# sys.exit(1)

		# configure file logger
		logging.basicConfig(level = logging.DEBUG,
												format = '%(asctime)s %(levelname)s %(message)s',
												filename = '/tmp/tagfs.log',
												filemode = 'a')
		
		# configure console logger
		consoleHandler = logging.StreamHandler(sys.stdout)
		consoleHandler.setLevel(logging.DEBUG)
		
		consoleFormatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
		consoleHandler.setFormatter(consoleFormatter)
		logging.getLogger().addHandler(consoleHandler)

		# replace default exception handler
		sys.excepthook = exceptionCallback
		
		logging.debug('Logging and exception handling has been set up')


if __name__ == "__main__":
		setUpLogging()
		if len(argv) != 3:
				print 'usage: %s <root> <mountpoint>' % argv[0]
				exit(1)
		
		c = Config()
		c.itemsDir = os.path.abspath(argv[1])
		c.dbLocation = os.path.join(c.itemsDir, '.tag-db.sqlite' )
		
		ou = offline_update.OfflineUpdater(c)
		ou.scan()
		
		wm = pyinotify.WatchManager()
		mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE | pyinotify.IN_CLOSE_WRITE
		notifier = pyinotify.ThreadedNotifier(wm, notifyd.EventHandler(c, wm))
		notifier.start()
		wdd = wm.add_watch(c.itemsDir, mask, rec=True)
		
		print 'started notifier'
		fuse = FUSE(Loopback(c), argv[2], foreground=True)
		
		print 'stopping notifier'
		notifier.stop()
		
