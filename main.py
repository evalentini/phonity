

#imports#####################################################################################################
#############################################################################################################

#import library for sending SMS through google voice
from voice import Voice
from util import input 
#import jinja2 template library 
import jinja2
#import datastore 
from google.appengine.ext import db

#import python standard distribution libraries 
import webapp2
import settings
import os
import re

##configure jinja2 templates#################################################################################
#############################################################################################################

template_dir=os.path.join(os.path.dirname(__file__), 'templates')
jinja2_env=jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=True)

##define database objects###################################################################################
###########################################################################################################
class Users(db.Model):
	phone=db.IntegerProperty
	pwd=db.StringProperty

##define helper functions###################################################################################
############################################################################################################

def render(template, **params):
	t=jinja2_env.get_template(template)
	return t.render(params)

def text(message=None, number=None, email="evan.valentini@gmail.com", pwd="robots25"):
	voice=Voice()
	voice.login(email, pwd)
	voice.send_sms(number, message)
	
##define global variables#################################################################################
##########################################################################################################

VALID_PWD="shabanaSnuggle"
#placeholder until we code random pin generator and store randomly generated pin in datastore
GLOBAL_PIN="1592"


###PAGE HANDLER HELPERS#################################################################################################################################################################################

class PageHandler(webapp2.RequestHandler):
	def check_admin_login(self):
		admin_pwd=self.request.cookies.get("admin_pwd")
		if admin_pwd:
			if admin_pwd!=VALID_PWD:
				self.redirect('/login')
		else:
			self.redirect('/login')


#######PAGE HANDLERS########################################################################################

class Signup(PageHandler):
	def get(self):
		#check if we are logged in 
		nil=PageHandler.check_admin_login(self)
		self.response.out.write(render("signup.html"))
	
	def post(self):
		#check for login 
		nil=PageHandler.check_admin_login(self)
		#pull phone number entered
		phone_number=self.request.get("phone_number")
		#regex verify phone number  
		#should be 10 digits
		PHONE_RE=re.compile(r'[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]')
		if PHONE_RE.match(phone_number):
			#store phone # in a cookie 
			self.response.set_cookie("phone", phone_number)
			
			#generate random pin
			pin=GLOBAL_PIN
			#text pin to entered number
			nil=text("Your pin is "+pin, phone_number) 
			self.redirect("/confirm")
		else:
			self.response.out.write(render("signup.html"))
			#add error message later	

#confirm user provided valid mobile number @ signup by prompting for pin
class Confirm(PageHandler):
	def get(self):
		nil=PageHandler.check_admin_login(self)
		self.response.out.write(render("confirm.html"))

	def post(self):
		#check for login 
		nil=PageHandler.check_admin_login(self)
		#get the pin entered 
		pin=self.request.get("pin")
		#check for pin match  
		if pin==GLOBAL_PIN:
			#save the mobile # and the password to the database
			#get the password, mobile #
			pwd=self.request.get("pwd")
			phone=self.request.cookies.get("phone")
			user=Users(phone=phone, pwd=pwd)
			user.put()
			self.redirect('/')
		else:
			self.response.out.write(render("confirm.html"))
			#add error message later
			
class Login(webapp2.RequestHandler):

	def get(self):
		self.response.out.write(render("login.html"))

	def post(self):
		admin_pwd=self.request.get("admin_pwd")
		if admin_pwd==VALID_PWD:
			self.response.set_cookie("admin_pwd", admin_pwd)
			self.redirect('/')
		else:
			self.response.out.write("invalid password")
	

class Welcome(webapp2.RequestHandler):
	def get(self):
		phone="""
			<html>
			<body>
			This is the Main Page
			<form method="post">
				<input type="submit" value="text!">
			</form>
			</body>
			</html>"""
		#check if logged in 
		admin_pwd=self.request.cookies.get("admin_pwd")
		if admin_pwd==VALID_PWD:
			self.response.out.write(phone)
		else:
			self.redirect('/login')	

	def post(self):
		#check if logged in 
		admin_pwd=self.request.cookies.get("admin_pwd")
		if admin_pwd==VALID_PWD:
			#send dummy text 
			voice=Voice()
			voice.login("evan.valentini@gmail.com", "robots25")
			voice.send_sms(7865533061, "I am a machine")
			self.response.out.write("message sent")		
		else:
			self.redirect('/login')

app=webapp2.WSGIApplication([('/', Welcome),
				('/login', Login),
				('/signup', Signup),
				('/confirm', Confirm)
				], debug=True)



