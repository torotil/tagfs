
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
		return [split_list('AND', p) for p in split_list('OR', path.split('/')[1:])]
	
	def get_source_file(self, path):
		parts = self.parse(path)
		last = parts[-1][-1]
		if len(last) > 1:
			filename = last[-1]
			# TODO: exrtact path from optional "(in /path/in/itemsDir)"
		parts[-1][-1] = [last[0]]
		q = '(SELECT fid, count(*) FROM tags WHERE tag IN(%s) GROUP BY fid HAVING count(*)=%d)'
		query = ' UNION '.join([q % ("'"+"', '".join([y[0] for y in x])+"'", len(x)) for x in parts])
		return query
		
			