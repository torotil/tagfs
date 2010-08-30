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
#
# = tag fs =
# == glossary ==
# * item: An item is a directory in the item container directory. Items can be
# tagged using a tag file.
# * tag: A tag is a text string which can be assigned to an item. Tags can
# consist of any character except newlines.


#====================================================================
# first set up exception handling and logging

import logging
import sys

def setUpLogging():
    def exceptionCallback(eType, eValue, eTraceBack):
        import cgitb

        txt = cgitb.text((eType, eValue, eTraceBack))

        logging.fatal(txt)
    
        # sys.exit(1)

    # configure file logger
    logging.basicConfig(level = logging.DEBUG,
                        format = '%(asctime)s %(levelname)s %(message)s',
                        filename = '/tmp/tagfs.log',
                        filemode = 'a')
    
    # configure console logger
    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setLevel(logging.DEBUG)
    
    consoleFormatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    consoleHandler.setFormatter(consoleFormatter)
    logging.getLogger().addHandler(consoleHandler)

    # replace default exception handler
    sys.excepthook = exceptionCallback
    
    logging.debug('Logging and exception handling has been set up')

if __name__ == '__main__':
    from os import environ as env
    if 'DEBUG' in env:
        setUpLogging()
    
    pass

#====================================================================
# here the application begins

import os
import stat
import errno
import fuse
import exceptions
import time
import functools
import view
import threading
import offline_update
import notifyd
import pyinotify

if not hasattr(fuse, '__version__'):
    raise RuntimeError, \
        "your fuse-py doesn't know of fuse.__version__, probably it's too old."

fuse.fuse_python_api = (0, 2)
fuse.feature_assert('stateful_files', 'has_init')

from cache import cache
import item_access
import node
    
class Config(object):

    ENABLE_VALUE_FILTERS = False

    ENABLE_ROOT_ITEM_LINKS = False

    def __init__(self, enableValueFilters = ENABLE_VALUE_FILTERS, enableRootItemLinks = ENABLE_ROOT_ITEM_LINKS):
        self.enableValueFilters = enableValueFilters
        self.enableRootItemLinks = enableRootItemLinks

    def __str__(self):
        return '[' + ', '.join([field + ': ' + str(self.__dict__[field]) for field in self.__dict__]) + ']'

class TagFS(fuse.Fuse):

    def __init__(self, initwd, *args, **kw):
        fuse.Fuse.__init__(self, *args, **kw)
        
        self._initwd = initwd
        self._itemsRoot = None

        def getStoreAction(target):
            if target:
                return 'store_true'
            else:
                return 'store_false'
        
        self.parser.add_option('-i',
                               '--items-dir',
                               dest = 'itemsDir',
                               help = 'items directory',
                               metavar = 'dir')
        self.parser.add_option('-t',
                               '--tag-file',
                               dest = 'tagFile',
                               help = 'tag file name',
                               metavar = 'file',
                               default = '.tag')
        self.parser.add_option('--value-filter',
                               action = getStoreAction(not Config.ENABLE_VALUE_FILTERS),
                               dest = 'enableValueFilters',
                               help = 'Displays value filter directories on toplevel instead of only context entries',
                               default = Config.ENABLE_VALUE_FILTERS)
        self.parser.add_option('--root-items',
                               action = getStoreAction(not Config.ENABLE_ROOT_ITEM_LINKS),
                               dest = 'enableRootItemLinks',
                               help = 'Display item links in tagfs root directory.',
                               default = Config.ENABLE_ROOT_ITEM_LINKS)
        self.parser.add_option('--db-file',
                               dest = 'dbLocation',
                               help = 'location for the sqlite database',
                               default = '.tag-db.sqlite')

    def getItemAccess(self):
        # Maybe we should move the parser run from main here.
        # Or we should at least check if it was run once...
        opts, args = self.cmdline

        # Maybe we should add expand user? Maybe even vars???
        assert opts.itemsDir != None and opts.itemsDir != ''
        itemsRoot = os.path.normpath(
                os.path.join(self._initwd, opts.itemsDir))
        
        self.tagFileName = opts.tagFile
    
        # try/except here?
        try:
            return item_access.ItemAccess(itemsRoot, self.tagFileName)
        except OSError, e:
            logging.error("Can't create item access from items directory %s. Reason: %s",
                    itemsRoot, str(e.strerror))
            raise
    
    @property
    @cache
    def config(self):
        opts, args = self.cmdline

        c = Config()
        c.enableValueFilters = opts.enableValueFilters
        c.enableRootItemLinks = opts.enableRootItemLinks
        c.itemsDir = opts.itemsDir
        c.dbLocation = os.path.abspath(os.path.join(c.itemsDir, opts.dbLocation))
        c.fs = self

        return c

    @property
    @cache
    def view(self):
        itemAccess = self.getItemAccess()

        return view.View(itemAccess, self.config)

    def getattr(self, path):
        return self.view.getattr(path)

    def readdir(self, path, offset):
        return self.view.readdir(path, offset)
            
    def readlink(self, path):
        return self.view.readlink(path)

    def open(self, path, flags):
        return self.view.open(path, flags)

    def read(self, path, size, offset):
        return self.view.read(path, size, offset)

    def write(self, path, data, pos):
        return self.view.write(path, data, pos)

    def symlink(self, path, linkPath):
        return self.view.symlink(path, linkPath)
    
    def fsinit(self):
      ou = offline_update.OfflineUpdater(self.config)
      ou.scan()
    
      self.multithreaded = 1
      wm = pyinotify.WatchManager()
      mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE | pyinotify.IN_CLOSE_WRITE
      notifier = pyinotify.ThreadedNotifier(wm, notifyd.EventHandler(self.config))
      notifier.start()
      wdd = wm.add_watch(self.config.itemsDir, mask, rec=True)

def main():
    fs = TagFS(os.getcwd(),
            version = "%prog " + fuse.__version__,
            dash_s_do = 'setsingle')

    fs.parse(errex = 1)
    opts, args = fs.cmdline

    if opts.itemsDir == None:
        fs.parser.print_help()
        # items dir should probably be an arg, not an option.
        print "Error: Missing items directory option."
        sys.exit()
    
    fs.fsinit()
    return fs.main()

if __name__ == '__main__':
    import sys
    sys.exit(main())
