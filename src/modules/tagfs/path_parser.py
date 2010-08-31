
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

class PathParser:
	def __init__(self):
		pass
	
	def parse(self, path):
		ret = [split_list('AND', p) for p in split_list('OR', path.split('/')[1:])]
		last = ret[-1][-1]
		if len(last) > 1:
			filename = last[-1]
			if filename[-1] == ')':
				r = filename.rfind(' (in ')
				if r > 0:
					path = filename[r+5:-1]
					filename = filename[:r]
		else:
			filename = None
			path = None
		ret = [[y[0] for y in x] for x in ret]
		return (ret, path, filename)
	
	
	def get_source_file(self, path): 
		
		if path == '/':
			return ' SELECT id as fid FROM items '
		
		parts, path, filename = self.parse(path)
		# TODO: exrtact path from optional "(in /path/in/itemsDir)"
		q = ' SELECT fid, COUNT(*) FROM ( SELECT DISTINCT a.id as fid, b.tag FROM (SELECT a.id, b.pid FROM items a LEFT JOIN hierarchy b ON (a.id = b.cid)) a, tags b WHERE b.tag IN(%s) AND (b.fid = a.id OR b.fid = a.pid)) GROUP BY fid HAVING count(*)=%d '
		query = ' UNION '.join([q % ("'"+"', '".join(x)+"'", len(x)) for x in parts])
		return query
		
			