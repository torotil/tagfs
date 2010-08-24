import sqlite3

class TagDB:

	#TODO Atomic commits
	#TODO MEMORY OPTION
	#TODO check for thread safety
	def __init__(self, location, sql="", memory=False) :
		self.connection = sqlite3.connect(location)
		cursor = self.connection.cursor()
		
		#TODO BETTER INDIZES + KEYs
		
		cursor.execute('CREATE TABLE IF NOT EXISTS files (id INTEGER PRIMARY KEY, path VARCHAR UNIQUE)')
		cursor.execute('CREATE TABLE IF NOT EXISTS tags  (tid INTEGER,fid INTEGER, tag VARCHAR)')
		cursor.execute('CREATE TABLE IF NOT EXISTS tagvalues  (tid INTEGER,value VARCHAR)')
		
		self.connection.commit()
		
		
	def addFile(self, file):
		cursor = self.connection.cursor()
		cursor.execute('INSERT INTO files(path) VALUES(\'' + file +'\')')
		
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
		cursor.execute('DELETE FROM tags '\
					   'WHERE fid in (SELECT id FROM FILES WHERE path like \''+path+'%\')')
		self.connection.commit()
		
	def removeTagFromFile(self,tag,file):
		cursor = self.connection.cursor()
		cursor.execute('DELETE FROM tags '\
					   'WHERE fid = (SELECT id FROM FILES WHERE path = \''+file+'\')')
		self.connection.commit()
		
		