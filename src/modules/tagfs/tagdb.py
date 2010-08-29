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
		
			
		cursor.execute('CREATE TABLE IF NOT EXISTS hierarchy   (pid INTEGER, cid INTEGER)')
		cursor.execute('CREATE TABLE IF NOT EXISTS items       (type VARCHAR(1), id INTEGER PRIMARY KEY, path VARCHAR UNIQUE)')
		cursor.execute('CREATE TABLE IF NOT EXISTS tags        (tid INTEGER,fid INTEGER, type VARCHAR(1), tag VARCHAR)')
		cursor.execute('CREATE TABLE IF NOT EXISTS tagvalues   (tid INTEGER,value VARCHAR)')
		
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
		
		for i in range(1, len(subdirs)-1): #element 0 is always null for well formed paths
			path = ''
			for j in range (1,i+1):
				path = path + '/' + subdirs[j]
				cursor.execute('INSERT or IGNORE INTO items(path,type) VALUES(\'' + path +'\', \'D\')')
				
		cursor.execute('INSERT INTO items(path,type) VALUES(\'' + file +'\', \'F\')')
		cursor.execute(' INSERT INTO hierarchy(pid, cid) '\
					   ' SELECT a.id, b.id FROM items a, items b '\
					   ' WHERE b.path = \'' + file + '\' '\
					   ' AND   b.path like a.path || \'%\' '\
					   ' AND   a.type = \'D\' '\
					  )
		self.connection.commit()
		
	def removeFile(self, file):
		cursor = self.connection.cursor()
		cursor.execute('DELETE FROM tags WHERE fid = (SELECT id FROM items where path = \''+ file + '\' AND type = \'F\')')
		cursor.execute('DELETE FROM hierarchy WHERE cid = (SELECT id FROM items where path = \''+ file + '\' AND type = \'F\')')
		cursor.execute('DELETE FROM items where path = \''+ file + '\' AND type = \'F\'')
		self.connection.commit() 
		
	def addDirectory(self, path):
		cursor = self.connection.cursor()
		
		subdirs = path.split('/')
		
		for i in range(1, len(subdirs)-1): #element 0 is always null for well formed paths
			subdirpath = ''
			for j in range (1,i+1):
				subdirpath = subdirpath + '/' + subdirs[j]
				cursor.execute('INSERT OR IGNORE INTO items(path,type) VALUES(\'' + subdirpath +'\', \'D\')')
		
		cursor.execute('INSERT OR IGNORE INTO items(path,type) VALUES(\'' + path +'\', \'D\')')
		cursor.execute(' INSERT INTO hierarchy(pid, cid) '\
					   ' SELECT a.id, b.id FROM items a, items b '\
					   ' WHERE b.path = \'' + path + '\' '\
					   ' AND   b.path like a.path || \'%\' '\
					   ' AND   a.type = \'D\' '\
					  )
		
		self.connection.commit()  
		
		
	def removeDirectory(self, path):
		cursor = self.connection.cursor()
		cursor.execute('SELECT id FROM items where path = \'' + path +'\' AND type = \'D\'')
		r = cursor.fetchone()
		id = r[0]
		cursor.execute('DELETE FROM tags  WHERE fid in (SELECT cid FROM hierarchy where pid = ' + str(id) +')')
		cursor.execute('DELETE FROM items WHERE id in (SELECT cid FROM hierarchy where pid = ' + str(id) +')')
		cursor.execute('DELETE FROM hierarchy WHERE pid in (SELECT cid FROM hierarchy where pid = ' + str(id) +')')
		cursor.execute('DELETE FROM hierarchy WHERE pid = ' + str(id))
		cursor.execute('DELETE FROM tags WHERE fid = ' + str(id))
		cursor.execute('DELETE FROM items where id = ' + str(id))
		self.connection.commit()
		
	def addTagToDirectory(self, tag, path):
		cursor = self.connection.cursor()
		cursor.execute('INSERT INTO tags(fid, tag) '\
					   'SELECT id, \'' + tag + '\' '\
					   'FROM items '\
					   'WHERE path = \'' + path + '\'')
		self.connection.commit()
		
	def addTagToFile(self, tag, file):
		cursor = self.connection.cursor()
		cursor.execute('INSERT INTO tags(fid, tag) '\
					   'SELECT id, \'' + tag + '\' '\
					   'FROM items '\
					   'WHERE path = \''+file+'\'')
		self.connection.commit()
		
	def removeTagFromDirectory(self,tag,path):
		cursor = self.connection.cursor()
		cursor.execute(' DELETE FROM tags '\
					   ' WHERE fid = (SELECT id FROM items WHERE path = \''+path+'\') '\
					   ' AND tag = \''+tag+'\'')
		self.connection.commit()
		
	def removeTagFromFile(self,tag,file):
		cursor = self.connection.cursor()
		cursor.execute(' DELETE FROM tags '\
					   ' WHERE fid = (SELECT id FROM items WHERE path = \''+file+'\') '\
					   ' AND tag = \''+ tag + '\'' )
		self.connection.commit()
		
	def removeAllTagsFromDirectory(self,path):
		cursor = self.connection.cursor()
		cursor.execute('DELETE FROM tags '\
					   'WHERE fid = (SELECT id FROM items WHERE path = \''+path+'\')')
		self.connection.commit()
		
	def removeAllTagsFromFile(self,file):
		cursor = self.connection.cursor()
		cursor.execute(' DELETE FROM tags '\
					   ' WHERE fid in (SELECT id FROM items WHERE path = \''+file+'\')')
		self.connection.commit()
		
	def resetTagsForDirectoryTo(self,path,taglist):
		self.removeAllTagsFromDirectory(path)
		for tag in taglist:
			self.addTagToDirectory(tag, path)  
			
	def resetTagsForFileTo(self,file,taglist):
		self.removeAllTagsFromFile(file)
		for tag in taglist:
			self.addTagToFile(tag, file) 
		
	def getTagsForItem(self, path):
		cursor = self.connection.cursor()
		ret = []
		cursor.execute(' SELECT b.tag FROM '\
					   ' tags b '\
					   ' WHERE b.fid in (SELECT a.pid FROM hierarchy a, items b '\
					   ' 				 WHERE b.path = \'' + path + '\' '\
					   '                 AND   a.cid = b.id ' \
					   					' UNION SELECT id FROM items where path = \'' + path + '\' )')
		
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

