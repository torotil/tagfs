#!/usr/bin/python

import pygtk
pygtk.require('2.0')
import gtk
import gtkmozembed
from tagdb import *
import os

# connect to the database
homedir = os.path.expanduser('~')
db = TagDB(homedir + "/.tagfs/db.sqlite")

class TagCloud:

	def delete_event(self,widget,data=None):
		return False

	def destroy(self,widget,data=None):
		gtk.main_quit()

	def button_clicked(self,widget,data):
		data.go_back()

	def __init__(self):
		self.moz = gtkmozembed.MozEmbed()
		#create a Vertical Box Container to whole the browser
		#and the "Back Button"
		box = gtk.VBox(False,0)
		
		#create a basic GTK+ window
		win = gtk.Window()
		win.add(box)

		#include both back button and the browser in the vertical box
		#and the GTK+ window
		box.pack_start(self.moz,True,True,0)

		tags = db.getTagsForTagCloud()

		words = {}
		for x in (' '.join(tags)).split():
			words[x] = 1 + words.get(x, 0)
		tagcloud = ' '.join([('<font size="%d">%s</font>'%(min(1+p*5/max(words.values()), 5), x)) for (x, p) in words.items()])

		outputf = open("/tmp/tagcloud.html", 'w')

		# TODO link the tags to a fileview
		outputf.write(tagcloud)
		outputf.close()

		#load the URL
		# TODO maybe no file is needed
		self.moz.load_url('/tmp/tagcloud.html')		
		
		#set the window title
		title=self.moz.get_title()		
		win.set_title("tagfs")
		
		#show all the stuffs on screen
		win.show_all()
		
		#connect the delete_event and destroy event to make sure
		#the app quits when the window is closed
		win.connect("delete_event",self.delete_event)
		win.connect("destroy",self.destroy)
		
if __name__ == "__main__":
	TagCloud()
	gtk.main()

