class AndNode:
	
	def __init__(self, left, right) :
		self.sqlstr = ' AND '
		self.left = left
		self.right = right
		
	def toSqlString(self, tableAlias, tableColumn):
		return self.left.toSqlString(tableAlias, tableColumn) + self.sqlstr + self.right.toSqlString(tableAlias, tableColumn)
	
class OrNode:
	
	def __init__(self, left, right) :
		self.sqlstr = ' OR '
		self.left = left
		self.right = right
		
	def toSqlString(self, tableAlias, tableColumn):
		return '(' + self.left.toSqlString(tableAlias, tableColumn) + self.sqlstr + self.right.toSqlString(tableAlias, tableColumn) + ')'
	
class TagNode:
	
	def __init__(self, tag) :
		self.sqlstr = tag
		
	def toSqlString(self, tableAlias, tableColumn):
		return tableAlias + '.' + tableColumn + '=\'' + self.sqlstr + '\''