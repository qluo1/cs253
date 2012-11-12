#!/usr/bin/env python
#
#
import os
import cgi
import datetime
import webapp2
import re

from google.appengine.ext import db
from google.appengine.api import users

from jinja2 import FileSystemLoader,Environment

ROOT=os.path.dirname(os.path.abspath(__file__))

env = Environment(loader = FileSystemLoader(os.path.join(ROOT,"templates")))

p = re.compile('^[_.0-9a-z-]+@([0-9a-z][0-9a-z-]+.)+[a-z]{2,4}$')
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

def validate_logon(name,passwd,password2,email):
	"""
	"""
	ret = {'name_error': None, 'passwd_error': None, 'email_error': None}
	if re.search("\s",name):
		ret['name_error'] = 'invalid name'
	elif passwd != passwrd2:
		ret['passwd_error'] 'password doesnot match'
	elif p.search(email) is None:
		ret['email_error'] = 'invalid email'
	else:
		return None

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

class Unit2_sigon(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Content Type'] = "text/html"
		temp = env.get_template("logon.html")
		self.response.out.write(temp.render({}))	
	def post(self):
		name = self.request.get("name")
		passwd = self.request.get("passwd")
		passwd2 = self.request.get("passwd2")
		email = self.request.get("email")
		# validation
		ret = validate_logon(name,passwd,passwd2,email)
		
		self.response.headers['Content Type'] = "text/html"
		if ret:
			temp = env.get_template("logon.html")
			return self.response.out.write(temp.render(ret))	
		else:
			return redirect("/unit2/welcome?%s" % name)

class Unit2_welcome(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Content Type'] = "text/html"
		name = self.request.get("name")
		temp = env.get_template("welcome.html")
		self.response.out.write(temp.render({'name':name}))


class TestHandler(webapp2.RequestHandler):
	def post(self):
		q = self.request.get("q")
		self.response.out.write(q)
		self.response.out.write(self.request)


app = webapp2.WSGIApplication([
  ('/', MainPage),
  ('/unit2/rot13', Unit2_rot13),
  ('/testform', TestHandler),
  ('/unit2/sigon', Unit2_sigon),
  ('/unit2/welcome', Unit2_welcome),
], debug=True)

