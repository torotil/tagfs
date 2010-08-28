import sqlite3

class TagDB:

	#TODO use prepared sql statements
	#TODO Atomic commits
	#TODO MEMORY OPTION
	#TODO check for thread safety
	def __init__(self, location, sql="", memory=False) :
		self.connection = sqlite3.connect(location)
		cursor = self.connection.cursor()
		
		#TODO BETTER INDIZES + KEYs
		
		cursor.execute('CREATE TABLE IF NOT EXISTS global_metadata (modtime NUMERIC)')
		
		cursor.execute('SELECT count(modtime) FROM global_metadata')
		
		if cursor.fetchone()[0] == 0 :
			cursor.execute('INSERT INTO global_metadata(modtime) VALUES(0)')
		
			
		
		cursor.execute('CREATE TABLE IF NOT EXISTS files (id INTEGER PRIMARY KEY, path VARCHAR UNIQUE)')
		cursor.execute('CREATE TABLE IF NOT EXISTS tags  (tid INTEGER,fid INTEGER, tag VARCHAR)')
		cursor.execute('CREATE TABLE IF NOT EXISTS tagvalues  (tid INTEGER,value VARCHAR)')
		
		self.connection.commit()
		
	def getModtime(self):
		cursor = self.connection.cursor()
		cursor.execute('SELECT modtime FROM global_metadata')
		return cursor.fetchone()[0]
	
	def setModtime(self,timestamp):
		cursor = self.connection.cursor()
		cursor.execute('UPDATE global_metadata set modtime = ' + str(timestamp))
		self.connection.commit()
		
	def addFile(self, file):
		cursor = self.connection.cursor()
		subdirs = file.split('/')
		whereclause = '( 1=2'
		
		for i in range(1, len(subdirs)-1): #element 0 is always null for well formed paths
			path = ''
			for j in range (1,i+1):
				path = path + '/' + subdirs[j]
			whereclause += '\n or f.path like \'' +  path + '%\''	
		whereclause += ')'
			
		cursor.execute('INSERT INTO files(path) VALUES(\'' + file +'\')')
		
		cursor.execute('INSERT INTO tags(fid, tag) '\
					   'SELECT a.id, b.tag '\
					   'FROM files a, '\
						'(SELECT t.tag '\
	 					' FROM files f, tags t '\
	 	 				' where f.path = ' + whereclause + ' '\
	 	 	 			' AND t.fid = f.id '\
		 	 	 		') b '\
		 	 	 		'where a.path = \'' + file + '\'')
		
		self.connection.commit()
		
	def removeFile(self, file):
		cursor = self.connection.cursor()
		cursor.execute('DELETE FROM tags WHERE fid = (SELECT id FROM files where path = \''+ file + '\')')
		cursor.execute('DELETE FROM files where path = \''+ file + '\'')
		self.connection.commit()   
		
	def removeDirectory(self, path):
		cursor = self.connection.cursor()
		cursor.execute('DELETE FROM tags WHERE fid in (SELECT id FROM files where path like \''+ path + '%\')')
		cursor.execute('DELETE FROM files where path like \''+ path + '%\'')
		self.connection.commit()
		
	def addTagToDirectory(self, tag, path):
		cursor = self.connection.cursor()
		cursor.execute('INSERT INTO tags(fid, tag) '\
					   'SELECT id, \'' + tag + '\' '\
					   'FROM FILES '\
					   'WHERE path like \'' + path + '%\'')
		self.connection.commit()
		
	def addTagToFile(self, tag, file):
		cursor = self.connection.cursor()
		cursor.execute('INSERT INTO tags(fid, tag) '\
					   'SELECT id, \'' + tag + '\' '\
					   'FROM FILES '\
					   'WHERE path = \''+file+'\'')
		self.connection.commit()
		
	def removeTagFromDirectory(self,tag,path):
		cursor = self.connection.cursor()
		cursor.execute(' DELETE FROM tags '\
					   ' WHERE fid in (SELECT id FROM FILES WHERE path like \''+path+'%\') '\
					   ' AND tag = \''+tag+'\'')
		self.connection.commit()
		
	def removeTagFromFile(self,tag,file):
		cursor = self.connection.cursor()
		cursor.execute(' DELETE FROM tags '\
					   ' WHERE fid = (SELECT id FROM FILES WHERE path = \''+file+'\') '\
					   ' AND tag = \''+ tag + '\'' )
		self.connection.commit()
		
	def removeAllTagsFromDirectory(self,path):
		cursor = self.connection.cursor()
		cursor.execute('DELETE FROM tags '\
					   'WHERE fid in (SELECT id FROM FILES WHERE path like \''+path+'%\')')
		self.connection.commit()
		
	def removeAllTagsFromFile(self,file):
		cursor = self.connection.cursor()
		cursor.execute(' DELETE FROM tags '\
					   ' WHERE fid in (SELECT id FROM FILES WHERE path like \''+file+'%\')')
		self.connection.commit()
		
	def resetTagsForDirectoryTo(self,path,taglist):
		self.removeAllTagsFromDirectory(path)
		for tag in taglist:
			self.addTagToDirectory(tag, path)
			
	def resetTagsForFileTo(self,file,taglist):
		self.removeAllTagsFromFile(file)
		for tag in taglist:
			self.addTagToFile(tag, file)
		
	def getTagsForFile(self, file):
		cursor = self.connection.cursor()
		ret = []
		cursor.execute('SELECT b.tag FROM '\
					   'files a, tags b '\
					   'WHERE a.path = \'' + file + '\''\
					   'AND b.fid = a.id')
		
		for row in cursor:
			ret.append(row[0])
		
		return ret
	
	def getTagsForDirectory(self, path):
		cursor = self.connection.cursor()
		ret = []
		cursor.execute('SELECT DISTINCT b.tag FROM '\
					   'files a, tags b '\
					   'WHERE a.path like \'' + path + '%\''\
					   'AND b.fid = a.id')
		
		for row in cursor:
			ret.append(row[0])
		
		return ret

	def getTagsForTagCloud(self):
		cursor = self.connection.cursor()
		ret = []
		cursor.execute('SELECT tag FROM tags')
		
		for row in cursor:
			ret.append(row[0])
		
		return ret
		
	













