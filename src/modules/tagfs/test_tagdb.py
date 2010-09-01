from tagdb import *
import unittest

class TagDBTest(unittest.TestCase):
	
	def setUp(self):
		self.db = TagDB('/tmp/test')
		
	def tearDown(self):
		self.db.truncateAll()
		
	def testTempPaths(self):
		self.db.createTempPath('/tmp/test')
		self.assertTrue('/tmp/test' in self.db.getTempPaths())
		self.db.removeTempPath('/tmp/test')
		self.assertTrue(len(self.db.getTempPaths()) == 0)
		
	def testModtime(self):
		self.db.setModtime(10)
		self.assertTrue(self.db.getModtime() == 10)
		
	def testAdd(self):
		self.db.addFile('/A/B/test')
		self.db.addDirectory('/A/C')
		self.db.addTagToDirectory('tag1', '/')
		self.db.addTagToFile('tag2', '/A/B/test')
		self.db.addTagToDirectory('tag3', '/A/C')
		self.db.addFile('/A/C/test2')
		self.assertTrue('test' in self.db.listFilesForPath([['tag1']]))
		self.assertTrue('test2' in self.db.listFilesForPath([['tag1']]))
		self.assertTrue('test' in self.db.listFilesForPath([['tag2']]))
		self.assertTrue('test2' not in self.db.listFilesForPath([['tag2']]))
		self.assertTrue('test2' in self.db.listFilesForPath([['tag1'],['tag2']]))
		
	def testCombination(self):
		self.assertFalse(self.db.isValidTagCombination([['test2','test3']]))
		self.db.addFile('/A/B/test')
		self.db.addDirectory('/A/C')
		self.db.addTagToDirectory('tag1', '/')
		self.db.addTagToFile('tag2', '/A/B/test')
		self.db.addTagToDirectory('tag3', '/A/C')
		self.db.addFile('/A/C/test2')
		self.assertTrue(self.db.isValidTagCombination([['tag1','tag2']]))
	