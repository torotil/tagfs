#!/usr/bin/env python

import sqlite3

class TagDB:
	"""Class used for access to a SQLite Database -> is responsible for storing information about
	   files, directories, tags and their hierarchy"""

	#TODO use prepared sql statements
	#TODO Atomic commits
	#TODO MEMORY OPTION
	#TODO check for thread safety
	def __init__(self, location, sql="", memory=False) :
		"""Constructor:
						location = /path/to/sqlitedatabase 
						sql and memory are currently not used"""
		self.connection = sqlite3.connect(location)
		cursor = self.connection.cursor()
		
		#TODO BETTER INDIZES + KEYs
		
		cursor.execute('CREATE TABLE IF NOT EXISTS global_metadata (modtime NUMERIC)')
		
		cursor.execute('SELECT count(modtime) FROM global_metadata')
		
		if cursor.fetchone()[0] == 0 :
			cursor.execute('INSERT INTO global_metadata(modtime) VALUES(0)')
		
			
		cursor.execute('CREATE TABLE IF NOT EXISTS hierarchy   (yn_direct_child VARCHAR(1), pid INTEGER, cid INTEGER)')
		cursor.execute('CREATE TABLE IF NOT EXISTS items       (type VARCHAR(1), id INTEGER PRIMARY KEY, path VARCHAR UNIQUE)')
		cursor.execute('CREATE TABLE IF NOT EXISTS tags        (tid INTEGER,fid INTEGER, type VARCHAR(1), tag VARCHAR)')
		cursor.execute('CREATE TABLE IF NOT EXISTS tagvalues   (tid INTEGER,value VARCHAR)')
		cursor.execute('CREATE TABLE IF NOT EXISTS temppaths   (path VARCHAR)')
		cursor.execute('INSERT OR IGNORE INTO items(path,type,id) VALUES(\'/\', \'D\',0)')
		
		
		#cursor.execute('INSERT or IGNORE INTO items (id, type, path) VALUES (1, \'D\', \'/\')')
		self.connection.commit()
		
	def removeAllTempPaths(self):
		"removes all temporary paths"
		cursor = self.connection.cursor()
		cursor.execute('DELETE FROM temppaths')
		self.connection.commit()
		
	def createTempPath(self, path):
		"creates a temporary path"
		cursor = self.connection.cursor()
		cursor.execute('INSERT INTO temppaths(path) VALUES (?)', (path,))
		self.connection.commit()
		
	def removeTempPath(self, path):
		"removes all temporary paths which start with PATH"
		cursor = self.connection.cursor()
		cursor.execute('DELETE FROM temppaths WHERE path like (?) || \'%\'  ', (path,))
		self.connection.commit()
		
	def getTempPaths(self):
		"returns a list of all temporary paths"
		ret = []
		cursor = self.connection.cursor()
		cursor.execute('SELECT path FROM temppaths')
		for row in cursor:
			ret.append(row[0])

		return ret 
		
		
	def getModtime(self):
		"returns the modification time of the source folder"
		cursor = self.connection.cursor()
		cursor.execute('SELECT modtime FROM global_metadata')
		return cursor.fetchone()[0]
	
	def setModtime(self,timestamp):
		"used to store the modification time of the source folder"
		cursor = self.connection.cursor()
		cursor.execute('UPDATE global_metadata set modtime = '+ str(timestamp))
		self.connection.commit()
		
	def addFile(self, file):
		"""adds a file to the db, if the directories in the parameters path are currently not stored they will be added
		   automatically"""
		cursor = self.connection.cursor()
		subdirs = file.split('/')
		
		for i in range(1, len(subdirs)-1): #element 0 is always null for well formed paths
			path = ''
			for j in range (1,i+1):
				path = path + '/' + subdirs[j]
				cursor.execute('INSERT or IGNORE INTO items(path,type) VALUES(?, \'D\')',(path,))
				
		cursor.execute('INSERT INTO items(path,type) VALUES(?, \'F\')',(file,))
		
		yn_direct_child = ''
		
		if len(subdirs) > 2 :
			cursor.execute(' INSERT INTO hierarchy(pid, cid, yn_direct_child) '\
						' SELECT a.id, b.id, CASE WHEN a.path = ? THEN \'Y\' ELSE \'N\' END FROM items a, items b '\
					   	' WHERE b.path = ? '\
					   	' AND   b.path like a.path || \'%\' '\
					   	' AND   a.type = \'D\' '\
					  	,(path, file))
			yn_direct_child = 'N'
		else:
			yn_direct_child = 'Y'
			
			
		cursor.execute(' INSERT INTO hierarchy(pid, cid, yn_direct_child) '\
					   ' SELECT 0, id,?  FROM items WHERE path = ? ', (yn_direct_child, file))
		self.connection.commit()
		
	def removeFile(self, file):
		"""removes a file from the database"""
		cursor = self.connection.cursor()
		cursor.execute('DELETE FROM tags WHERE fid = (SELECT id FROM items where path = ? AND type = \'F\')', (file,))
		cursor.execute('DELETE FROM hierarchy WHERE cid = (SELECT id FROM items where path = ? AND type = \'F\')', (file,))
		cursor.execute('DELETE FROM items where path = ? AND type = \'F\'', (file,))
		self.connection.commit() 
		
	def addDirectory(self, path):
		"""adds a directory to the db, if the directories in the parameters path are currently not stored they will be added
		   automatically"""
		cursor = self.connection.cursor()
		
		subdirs = path.split('/')
		
		for i in range(1, len(subdirs)-1): #element 0 is always null for well formed paths
			subdirpath = ''
			for j in range (1,i+1):
				subdirpath = subdirpath + '/' + subdirs[j]
				cursor.execute('INSERT OR IGNORE INTO items(path,type) VALUES(?, \'D\')', (subdirpath,))
		
		cursor.execute('INSERT OR IGNORE INTO items(path,type) VALUES(?, \'D\')', (path,))
		
		yn_direct_child = ''
		
		if len(subdirs) > 2 :
			cursor.execute(' INSERT INTO hierarchy(pid, cid, yn_direct_child) '\
						' SELECT a.id, b.id, CASE WHEN a.path = ? THEN \'Y\' ELSE \'N\' END FROM items a, items b '\
						' WHERE b.path = ? '\
						' AND   b.path like a.path || \'%\' '\
						' AND   b.path != a.path '\
						' AND   a.type = \'D\' '\
						, (subdirpath, path))
			yn_direct_child = 'N'
		else:
			yn_direct_child = 'Y'
		
		cursor.execute(' INSERT INTO hierarchy(pid, cid, yn_direct_child) SELECT 0, id,? FROM items WHERE path = ? ', (yn_direct_child, path))
		self.connection.commit()
		
	def truncateAll(self):
		"deletes the whole database"
		cursor = self.connection.cursor()
		cursor.execute('DELETE FROM tagvalues')  
		cursor.execute('DELETE FROM tags') 
		cursor.execute('DELETE FROM items') 
		cursor.execute('DELETE FROM hierarchy')
		self.connection.commit()
		
	def removeDirectory(self, path):
		"""removes a directory and all it's children from the database"""
		if path == '/':
			self.truncateAll()
			return
		
		cursor = self.connection.cursor()
		cursor.execute('SELECT id FROM items where path = ? AND type = \'D\'', (path,))
		r = cursor.fetchone()
		id = r[0]
		cursor.execute('DELETE FROM tags  WHERE fid in (SELECT cid FROM hierarchy where pid = ' + str(id)+')')
		cursor.execute('DELETE FROM items WHERE id in (SELECT cid FROM hierarchy where pid = ' + str(id)+')')
		cursor.execute('DELETE FROM hierarchy WHERE pid in (SELECT cid FROM hierarchy where pid = ' + str(id)+')')
		cursor.execute('DELETE FROM hierarchy WHERE pid = ' + str(id))
		cursor.execute('DELETE FROM tags WHERE fid = ' + str(id))
		cursor.execute('DELETE FROM items where id = ' + str(id))
		self.connection.commit()
		
	def addTagToDirectory(self, tag, path):
		"""tags fdirectory at *path (and all its children) with *tag"""
		cursor = self.connection.cursor()
		
		if path == '/':
			cursor.execute(' INSERT INTO tags (fid, tag) VALUES (0, ?)', (tag,))
		
		else:
			cursor.execute('INSERT INTO tags(fid, tag) '\
						'SELECT id, ? '\
						'FROM items '\
						'WHERE path = ?', (tag, path))
			
		self.connection.commit()
		
	def addTagToFile(self, tag, file):
		"tags *file with *tag"
		cursor = self.connection.cursor()
		cursor.execute('INSERT INTO tags(fid, tag) '\
					   'SELECT id, ? '\
					   'FROM items '\
					   'WHERE path = ? ', (tag, file))
		self.connection.commit()
		
	def removeTagFromDirectory(self,tag,path):
		"removes the tag from the directory and all it's children"
		cursor = self.connection.cursor()
		
		if path == '/':
			cursor.execute(' DELETE FROM tags where fid = 0 AND tag = ?', (tag,)) 
		else:
			cursor.execute(' DELETE FROM tags '\
						' WHERE fid = (SELECT id FROM items WHERE path = ?) '\
					   	' AND tag = ?', (path, tag))
		self.connection.commit()
		
	def removeTagFromFile(self,tag,file):
		"removes a tag from a file"
		cursor = self.connection.cursor()
		cursor.execute(' DELETE FROM tags '\
					   ' WHERE fid = (SELECT id FROM items WHERE path = ?) '\
					   ' AND tag = ? ', (file, tag) )
		self.connection.commit()
		
	def removeAllTagsFromDirectory(self,path):
		"removes all tags from directory"
		cursor = self.connection.cursor()
		
		if path == '/':
			cursor.execute(' DELETE FROM tags where fid = 0') 
		else:
			cursor.execute('DELETE FROM tags '\
					   	'WHERE fid = (SELECT id FROM items WHERE path = ?)', (path,))
			
		self.connection.commit()
		
	def removeAllTagsFromFile(self,file):
		"removes all tags from file"
		cursor = self.connection.cursor()
		cursor.execute(' DELETE FROM tags '\
					   ' WHERE fid in (SELECT id FROM items WHERE path = ?)', (file,))
		self.connection.commit()
		
	def resetTagsForDirectoryTo(self,path,taglist):
		"removes all tags from directory and tags it with taglist"
		self.removeAllTagsFromDirectory(path)
		for tag in taglist:
			self.addTagToDirectory(tag, path)  
			
	def resetTagsForFileTo(self,file,taglist):
		"removes all tags from file and tags it with taglist"
		self.removeAllTagsFromFile(file)
		for tag in taglist:
			self.addTagToFile(tag, file)
	
	def getDirectoryItems(self, path):
		cursor = self.connection.cursor()
		
		id = 0
		if path != '/':
			cursor.execute('SELECT id FROM items where path = ? AND type = \'D\'', (path,))
			r = cursor.fetchone()
			if r == None:
				return ([], [])
			id = r[0]
			
		cursor.execute('SELECT path FROM items WHERE id in (SELECT cid FROM hierarchy where pid = ' + str(id) +' AND type = \'D\' AND yn_direct_child = \'Y\')')
		dirs = [row[0] for row in cursor]
		cursor.execute('SELECT path FROM items WHERE id in (SELECT cid FROM hierarchy where pid = ' + str(id) +' AND type = \'F\' AND yn_direct_child = \'Y\')')
		files = [row[0] for row in cursor]
		return (dirs, files)
		
	def getTagsForItem(self, path):
		"returns a list of all tags for given file/directory"
		cursor = self.connection.cursor()
		ret = []
		cursor.execute(' SELECT b.tag FROM '\
					   ' tags b '\
					   ' WHERE b.fid in (SELECT a.pid FROM hierarchy a, items b '\
					   ' 				 WHERE b.path = ? '\
					   '                 AND   a.cid = b.id ' \
					   					' UNION SELECT id FROM items where path = ? )', (path, path))
		
		for row in cursor:
			ret.append(row[0])
		
		return ret	
	
	def isValidTagCombination(self, tags):
		"""checks if a combination of tags is valid for any file in the database
		   tags is a [list of AND linked tags] all sub lists are linked with or"""
		cursor = self.connection.cursor()
		cursor.execute('SELECT COUNT(*) from ('+self.getSourceFileSQL(tags)+')')	
		
		return cursor.fetchone()[0] >0
	
	def getTagsForTagCloud(self):
		"""returns all tags"""
		cursor = self.connection.cursor()
		ret = []
		cursor.execute('SELECT tag FROM tags')

		for row in cursor:
			ret.append(row[0])

		return ret 
	
	def listFilesForPath(self, tags):
		"""returns all files which are tagged with tags"""
		stmt = ''
		ret = []
		cursor = self.connection.cursor()
		
		if tags == [[]]:
			stmt = 'SELECT path FROM ITEMS where type = \'F\''
		else:
			sqlpart = self.getSourceFileSQL(tags)
			stmt  = ' SELECT a.path FROM '
			stmt += ' items a, ( '
			stmt += sqlpart
			stmt += ' ) b '
			stmt += ' WHERE a.id = b.fid '
			stmt += ' AND a.type = \'F\''
			
		cursor.execute(stmt)
		
		for row in cursor:
			tmp=row[0]
			ret.append(tmp.split('/')[-1:][0])
		
		return list(set(ret))
	
	def isFile(self, tags, filename):
		"""returns true if the given filename is unique for the given list of tags, if there are multiple files which match
		   then false is returned else null"""
		sqlpart = self.getSourceFileSQL(tags)
		cursor = self.connection.cursor()
		stmt =  ' SELECT  COUNT(*) FROM ( '
		stmt += ' SELECT a.path FROM '
		stmt += ' items a, ( '
		stmt += sqlpart
		stmt += ' ) b '
		stmt += ' WHERE a.id = b.fid '
		stmt += ' AND a.type = \'F\' '
		stmt += ' AND   a.path like ? '
		stmt += ' ) '
		cursor.execute(stmt, ('%'+filename,))
		
		ret = cursor.fetchone()[0]
		if ret == 0:
			return None
		
		return ret == 1
	
	def getDuplicatePaths(self, tags, filename):
		"""returnes the path for all files which are not unique for the given list of tags"""
		ret = []
		
		sqlpart = self.getSourceFileSQL(tags)
		cursor = self.connection.cursor()
		stmt = ' SELECT a.id, a.path FROM '
		stmt += ' items a, ( '
		stmt += sqlpart
		stmt += ' ) b '
		stmt += ' WHERE a.id = b.fid '
		stmt += ' AND a.type = \'F\' '
		stmt += ' AND   a.path like ? '
		cursor.execute(stmt, ('%'+filename,))
		
		for row in cursor:
			ret.append(str(row[0])+'.'+row[1].replace('/','.')[1:])

		return ret 
	
	def getSourceFile(self, tags, filename):
		
		sqlpart = self.getSourceFileSQL(tags)
		cursor = self.connection.cursor()
		stmt = ' SELECT a.path FROM '
		stmt += ' items a, ( '
		stmt += sqlpart
		stmt += ' ) b '
		stmt += ' WHERE a.id = b.fid '
		stmt += ' AND a.type = \'F\' '
		stmt += ' AND   a.path like ? '
		cursor.execute(stmt, ('%'+filename,))
		
		ret = cursor.fetchone()
		
		if ret == None:
			return None

		return ret[0] 
	
	def getDuplicateSourceFile(self, path):
		filename = path.rsplit('/',1)[-1]
		id = int(filename.split('.',1)[0])
		q = 'SELECT path FROM items WHERE id=%d and type=\'F\''
		cursor = self.connection.cursor()
		cursor.execute(q % id)
		return cursor.fetchone()[0]
	
	@staticmethod
	def getSourceFileSQL(tags):
		if tags == [[]]:
			return ' SELECT id as fid FROM items '
		
		q = ' SELECT fid, COUNT(*) FROM ( SELECT DISTINCT a.id as fid, b.tag FROM (SELECT a.id, b.pid FROM items a LEFT JOIN hierarchy b ON (a.id = b.cid)) a, tags b WHERE b.tag IN(%s) AND (b.fid = a.id OR b.fid = a.pid)) GROUP BY fid HAVING count(*)=%d '
		query = ' UNION '.join([q % ("'"+"', '".join(x)+"'", len(x)) for x in tags])
		return query
	
	def getAvailableTagsForPath(self, tags):
		# we are only interested in the part after the last OR
		tags = tags[-1:]
		
		# no condition - list all tags
		if len(tags[0]) == 0:
			return self.getTagsForTagCloud()
		
		#IN condition for all already selected tags
		in_cond = "'"+"', '".join(tags[0])+"'"
		
		cursor = self.connection.cursor()
		ret = []
		
		stmt =  ' SELECT distinct tag FROM ('
		stmt += ' SELECT tag FROM tags a, ( '
		stmt += self.getSourceFileSQL(tags)
		stmt += ' ) b \n'
		stmt += ' WHERE a.fid = b.fid '
		stmt += ' AND a.tag not in (' + in_cond + ' ) '
		stmt += ' UNION '
		stmt += ' SELECT tag FROM tags a, ( '
		stmt += self.getSourceFileSQL(tags)
		stmt += ' ) b, hierarchy c '
		stmt += ' WHERE c.pid = b.fid '
		stmt += ' AND   (a.fid = c.cid OR a.fid = c.pid)'
		stmt += ' AND a.tag not in (' + in_cond + ' ) '
		stmt += ' ) '
		
		cursor.execute(stmt)
		
		for row in cursor:
			ret.append(row[0])

		return ret 
		
		
		


