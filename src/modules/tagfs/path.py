
from tagdb import TagDB

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
			return TagPath(self.config, parts, last)
		if d == 1:
			return FilesPath(self.config, parts, last)
		return DuplicatesPath(self.config, parts, last)
	
	def createForFile(self, path):
		dir, file = path.rpslit('/', 1)
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
	def __init__(self, config, tags, last):
		self.config = config
		tags[-1][-1] = tags[-1][-1][:1]
		self.valid = True
		self.tags = self.simplifyTags(tags)
		self.rest = last[1:]
	
	def simplifyTags(self, tags):
		for i in range(0, len(tags)):
			s = tags[i]
			if s == [[]]:
				tags[i] = []
				continue
			for j in range(0, len(s)):
				if len(s[j]) > 1:
					self.valid = False
				s[j] = s[j][0]
		return tags
	
	def isValid(self):
		return self.valid
		
	def db(self):
		return TagDB(self.config.dbLocation)
	
	def __repr__(self):
		return '%s: %s + %s' % (self.__class__.__name__, self.tags, self.rest)

class TagPath(Path):
	def readdir(self):
		return self.sd + self.db().getAvailableTagsForPath(self.tags)

class FilesPath(Path):
	def readdir(self):
		return self.sd + ['AND', 'OR'] + self.db().listFilesForPath(self.tags)

class DuplicatesPath(Path):
	def readdir(self):
		return self.sd + self.db().getDuplicatePaths(self.tags, self.rest[-1])