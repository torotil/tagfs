#!/usr/bin/env python
#
# Copyright 2009, 2010 Markus Pielmeier
#
# This file is part of tagfs.
#
# tagfs is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# tagfs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with tagfs.  If not, see <http://www.gnu.org/licenses/>.
#

from cache import cache
import errno
import log
import logging
import node
import os
from transient_dict import TransientDict
from tagdb import TagDB
import fuse
from stat import S_IFDIR, S_IFLNK, S_IFREG
from time import time

class MyStat(fuse.Stat):
    
    def __init__(self, fs):
        self.st_mode = 0
        self.st_ino = 0
        self.st_dev = 0
        self.st_nlink = 0
        context = fs.GetContext()
        self.st_uid, self.st_gid = context['uid'], context['gid']
        self.st_size = 0
        self.st_atime = 0
        self.st_mtime = 0
        self.st_ctime = 0

    def __str__(self):
        return '[' + ', '.join([field + ': ' + str(self.__dict__[field]) for field in self.__dict__]) + ']'


class View(object):
    """Abstraction layer from fuse API.

    This class is an abstraction layer from the fuse API. This should ease
    writing test cases for the file system.
    """

    DEFAULT_NODES = {
        '.DirIcon': None,
        'AppRun': None
        }
    
    def __init__(self, itemAccess, config):
        self.itemAccess = itemAccess
        self.config = config
        self._nodeCache = TransientDict(100)
        
    def getDB(self):
        return TagDB(self.config.dbLocation) 


    @cache
    def getRootNode(self):
        return node.RootNode(self.itemAccess, self.config)

    def getNode(self, path):
        if path in self._nodeCache:
            # simple path name based caching is implemented here

            logging.debug('tagfs _nodeCache hit')

            return self._nodeCache[path]

        # ps contains the path segments
        ps = [x for x in os.path.normpath(path).split(os.sep) if x != '']

        psLen = len(ps)
        if psLen > 0:
            lastSegment = ps[psLen - 1]
            
            if lastSegment in View.DEFAULT_NODES:
                logging.debug('Using default node for path ' + path)

                return View.DEFAULT_NODES[lastSegment]

        n = self.getRootNode()

        for e in path.split('/')[1:]:
            if e == '':
                continue

            n = n.getSubNode(e)

            if not n:
                # it seems like we are trying to fetch a node for an illegal
                # path

                break

        logging.debug('tagfs _nodeCache miss')
        self._nodeCache[path] = n

        return n

    @log.logCall
    def getattr(self, path):
        parts = path.rsplit('/', 1)
        type = self.path_type(parts[0])
        db = self.getDB()
        attr = MyStat(self.config.fs)
        if type == 'tags' and parts[1] == '':
          attr.st_mode |= S_IFDIR | 0500
          attr.st_nlink = 2
          logging.warn('for root: ' + '%s' % attr)
          return attr
        if type == 'files':
          if parts[1] not in ['OR', 'AND'] and db.isFile(path):
            attr.st_mode |= S_IFLNK | 0400
          else:
            attr.st_mode |= S_IFDIR | 0500
            attr.st_nlink = 2
        if type == 'tags':
          attr.st_mode |= S_IFDIR | 0500
          attr.st_nlink = 2
        if type == 'duplicates':
          attr.st_mode |= S_IFLNK | 0400
        logging.warn(attr)
        return attr


    def path_type(self, path):
      parts = path.rsplit('/', 2)
      if parts[-1] in ['AND', 'OR', '']:
        return 'tags'
      if parts[-2] in ['', 'AND', 'OR']:
        return 'files'
      return 'duplicates'

    @log.logCall
    def readdir(self, path, offset):
      type = self.path_type(path)
      
      yield fuse.Direntry('.')
      yield fuse.Direntry('..')
      
      if type == 'tags': 
        logging.debug('handling as tag-dir: '+path)
        files = self.getDB().getAvailableTagsForPath(path)
      if type == 'files':
        logging.debug('handling as files-dir')
        files = self.getDB().listFilesForPath(path)
      if type == 'duplicates':
        files = ['duplicates']
      
      logging.debug('answer from database: %s' % files)
      for n in files:
        logging.debug('yielding %s' % n)
        yield fuse.Direntry(n)

    @log.logCall
    def readlink(self, path):
        
        n = self.getNode(path)

        if not n:
            logging.warn('Try to read not existing link from node: ' + path)

            return -errno.ENOENT

        return n.readlink(path)

    @log.logCall
    def symlink(self, path, linkPath):
        linkPathSegs = linkPath.split('/')

        n = self.getNode('/'.join(linkPathSegs[0:len(linkPathSegs) - 2]))

        if not n:
            return -errno.ENOENT

        return n.symlink(path, linkPath)

    @log.logCall
    def open(self, path, flags):
        n = self.getNode(path)

        if not n:
            logging.warn('Try to open not existing node: ' + path)

            return -errno.ENOENT

        return n.open(path, flags)

    @log.logCall
    def read(self, path, len, offset):
        n = self.getNode(path)

        if not n:
            logging.warn('Try to read from not existing node: ' + path)

            return -errno.ENOENT

        return n.read(path, len, offset)

    @log.logCall
    def write(self, path, data, pos):
        n = self.getNode(path)

        if not n:
            logging.warn('Try to write to not existing node: ' + path)

            return -errno.ENOENT

        return n.write(path, data, pos)
	
