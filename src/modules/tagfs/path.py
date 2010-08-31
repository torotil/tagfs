
from tagdb import TagDB
import os
import copy
from stat import S_IFDIR, S_IFLNK, S_IFREG
from fuse import FuseOSError
import errno

def split_list(sep, list):
	res = []
	partial_list = []
	for item in list:
		if item == sep:
			res.append(partial_list)
			partial_list = []
		else:
			partial_list.append(item)
	res += [partial_list]
	return res

class PathFactory:
	def __init__(self, config):
		self.config = config
	def create(self, path):
		parts, last = self.parts(path)
		d = len(last)
		if d == 0:
			return TagPath(self.config, path, parts, last)
		if d == 1:
			return FilesPath(self.config, path, parts, last)
		return DuplicatesPath(self.config, path, parts, last)
	
	def createForFile(self, path):
		dir, file = path.rsplit('/', 1)
		return self.create(dir), file
	
	@staticmethod
	def parts(path):
		if len(path) <= 0:
			path = '/'
		if path[-1] == '/':
			path = path[:-1]
		tags = [split_list('AND', p) for p in split_list('OR', path.split('/')[1:])]
		rest = tags[-1][-1]
		return (tags, rest)

class Path:
	sd = ['.', '..']
	stat = {'st_mode':0, 'st_nlink':0, 'st_uid':os.geteuid(), 'st_gid':os.getegid() }
	def __init__(self, config, path, tags, last):
		self.config = config
		tags[-1][-1] = tags[-1][-1][:1]
		self.valid = True
		self.path = path
		self.tags = self.simplifyTags(tags)
		self.rest = last[1:]
	
	def simplifyTags(self, tags):
		for i in range(0, len(tags)):
			s = tags[i]
			tags[i] = [x[0] for x in s if len(x)] 
			for x in s:
				if len(x) > 1:
					self.valid = False
		return tags
	
	def isValid(self):
		return self.valid
		
	def db(self):
		return TagDB(self.config.dbLocation)
	
	def getStat(self, **kwargs):
		attr = copy.copy(self.stat)
		for k, v in kwargs.iteritems():
			attr[k] = v
		return attr
	
	def __repr__(self):
		return '%s: %s + %s' % (self.__class__.__name__, self.tags, self.rest)
	
	def readlink(self, filename):
		ret = os.path.abspath(os.path.join(self.config.itemsDir, self.readlinkRel(filename)[1:]))
		
		if ret == None:
			raise FuseOSError(errno.ENOENT)
		
		return ret
	
	def readlinkRel(self, filename):
		return self.db().getSourceFile(self.tags, filename)

class TagPath(Path):
	def readdir(self):
		return self.sd + self.db().getAvailableTagsForPath(self.tags)
	def getattr(self, file):
		return self.getStat(st_mode = S_IFDIR | 0500, st_nlink = 2)

class FilesPath(Path):
	def readdir(self):
		return self.sd + ['AND', 'OR'] + self.db().listFilesForPath(self.tags)
	def getattr(self, file):
		chk = self.db().isFile(self.tags, file)
		if chk == None:
			raise FuseOSError(errno.ENOENT)
		
		if file not in ['OR', 'AND'] and chk:
			return self.getStat(st_mode = S_IFLNK | 0400)
		else:
			return self.getStat(st_mode = S_IFDIR | 0500, st_nlink = 2)
		

class DuplicatesPath(Path):
	def readdir(self):
		return self.sd + self.db().getDuplicatePaths(self.tags, self.rest[-1])
	def getattr(self, file):
		return self.getStat(st_mode = S_IFLNK | 0400)
	def readlinkRel(self, filename):
		return self.db().getDuplicateSourceFile('/'.join([self.path, filename]))