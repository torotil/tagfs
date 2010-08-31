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
		
			
		cursor.execute('CREATE TABLE IF NOT EXISTS hierarchy   (yn_direct_child VARCHAR(1), pid INTEGER, cid INTEGER)')
		cursor.execute('CREATE TABLE IF NOT EXISTS items       (type VARCHAR(1), id INTEGER PRIMARY KEY, path VARCHAR UNIQUE)')
		cursor.execute('CREATE TABLE IF NOT EXISTS tags        (tid INTEGER,fid INTEGER, type VARCHAR(1), tag VARCHAR)')
		cursor.execute('CREATE TABLE IF NOT EXISTS tagvalues   (tid INTEGER,value VARCHAR)')
		cursor.execute('INSERT OR IGNORE INTO items(path,type,id) VALUES(\'/\', \'D\',0)')
		
		#cursor.execute('INSERT or IGNORE INTO items (id, type, path) VALUES (1, \'D\', \'/\')')
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
		
		yn_direct_child = ''
		
		if len(subdirs) > 2 :
			cursor.execute(' INSERT INTO hierarchy(pid, cid, yn_direct_child) '\
						' SELECT a.id, b.id, CASE WHEN a.path = \'' + path + '\' THEN \'Y\' ELSE \'N\' END FROM items a, items b '\
					   	' WHERE b.path = \'' + file + '\' '\
					   	' AND   b.path like a.path || \'%\' '\
					   	' AND   a.type = \'D\' '\
					  		)
			yn_direct_child = 'N'
		else:
			yn_direct_child = 'Y'
			
			
		cursor.execute(' INSERT INTO hierarchy(pid, cid, yn_direct_child) '\
					   ' SELECT 0, id,\''+yn_direct_child+'\'  FROM items WHERE path = \'' + file + '\' ')
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
		
		yn_direct_child = ''
		
		if len(subdirs) > 2 :
			cursor.execute(' INSERT INTO hierarchy(pid, cid, yn_direct_child) '\
						' SELECT a.id, b.id, CASE WHEN a.path = \'' + subdirpath + '\' THEN \'Y\' ELSE \'N\' END FROM items a, items b '\
						' WHERE b.path = \'' + path + '\' '\
						' AND   b.path like a.path || \'%\' '\
						' AND   b.path != a.path '\
						' AND   a.type = \'D\' '\
						)
			yn_direct_child = 'N'
		else:
			yn_direct_child = 'Y'
		
		cursor.execute(' INSERT INTO hierarchy(pid, cid, yn_direct_child) SELECT 0, id,\''+yn_direct_child+'\' FROM items WHERE path = \'' + path + '\' ')
		self.connection.commit()
		
	def truncateAll(self):
		cursor = self.connection.cursor()
		cursor.execute('DELETE FROM tagvalues')  
		cursor.execute('DELETE FROM tags') 
		cursor.execute('DELETE FROM items') 
		cursor.execute('DELETE FROM hierarchy')
		self.connection.commit()
		
	def removeDirectory(self, path):
		
		if path == '/':
			self.truncateAll()
			return
		
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
		
		if path == '/':
			cursor.execute(' INSERT INTO tags (fid, tag) VALUES (0, \'' + tag + '\')')
		
		else:
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
		
		if path == '/':
			cursor.execute(' DELETE FROM tags where fid = 0 AND tag = \''+tag+'\'') 
		else:
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
		
		if path == '/':
			cursor.execute(' DELETE FROM tags where fid = 0') 
		else:
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
	
	def getDirectoryItems(self, path):
		cursor = self.connection.cursor()
		
		id = 0
		if path != '/':
			cursor.execute('SELECT id FROM items where path = \'' + path +'\' AND type = \'D\'')
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
	
	def listFilesForPath(self, tags):
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
		sqlpart = self.getSourceFileSQL(tags)
		cursor = self.connection.cursor()
		stmt =  ' SELECT  COUNT(*) FROM ( '
		stmt += ' SELECT a.path FROM '
		stmt += ' items a, ( '
		stmt += sqlpart
		stmt += ' ) b '
		stmt += ' WHERE a.id = b.fid '
		stmt += ' AND a.type = \'F\' '
		stmt += ' AND   a.path like \'%/' + filename +'\' '
		stmt += ' ) '
		cursor.execute(stmt)
		
		return cursor.fetchone()[0] == 1
	
	def getDuplicatePaths(self, tags, filename):
		ret = []
		
		sqlpart = self.getSourceFileSQL(tags)
		cursor = self.connection.cursor()
		stmt = ' SELECT a.id, a.path FROM '
		stmt += ' items a, ( '
		stmt += sqlpart
		stmt += ' ) b '
		stmt += ' WHERE a.id = b.fid '
		stmt += ' AND a.type = \'F\' '
		stmt += ' AND   a.path like \'%/' + filename +'\' '
		cursor.execute(stmt)
		
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
		stmt += ' AND   a.path like \'%/' + filename +'\' '
		cursor.execute(stmt)
		
		ret = cursor.fetchone()

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
		
		
		


