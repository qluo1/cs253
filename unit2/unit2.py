#!/usr/bin/env python
#
#
import os
import cgi
import datetime
import webapp2

from google.appengine.ext import db
from google.appengine.api import users

from jinja2 import FileSystemLoader,Environment

ROOT=os.path.dirname(os.path.abspath(__file__))

env = Environment(loader = FileSystemLoader(os.path.join(ROOT,"templates")))

def rot13(s):
	"""
	 Map upper case A-Z to N-ZA-M and lower case a-z to n-za-m
	"""
	
	A_Z= map(chr,range(65,91))
	NZAM = map(chr,range(78,91) + range(65,78))
	a_z = map(chr,range(97,123))
	nzam = map(chr,range(110,123) + range(97,110))
	m = dict(zip(A_Z + a_z, NZAM + nzam))
	ret = ""
	for i in s:
		ret = ret + m.get(i,i)

	return ret
	

class MainPage(webapp2.RequestHandler):
	def get(self,value=""):
		self.response.headers['Content Type'] = "text/html"
		
		out = "Hello world"

		self.response.out.write(out)
	
	def post(self):
		
		text = self.request.get("text")
		value = rot13(text)
		self.response.headers['Content Type'] = "text/html"
		context = {"value": cgi.escape(value)}
		temp = env.get_template("unit2.html")
		self.response.out.write(temp.render(context))
		
class Unit2_rot13(webapp2.RequestHandler):
	def get(self,value=""):
		self.response.headers['Content Type'] = "text/html"
		context = {"value": ""}
		temp = env.get_template("unit2.html")
		self.response.out.write(temp.render(context))	

	def post(self):
		text = self.request.get("text")
		value = rot13(text)
		self.response.headers['Content Type'] = "text/html"
		
		context = {"value": cgi.escape(value)}
		temp = env.get_template("unit2.html")
		self.response.out.write(temp.render(context))

class TestHandler(webapp2.RequestHandler):
	def post(self):
		q = self.request.get("q")
		self.response.out.write(q)
		self.response.out.write(self.request)


app = webapp2.WSGIApplication([
  ('/', MainPage),
  ('/unit2/rot13', Unit2_rot13),
  ('/testform', TestHandler),
], debug=True)

