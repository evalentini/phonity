

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
	phone=db.IntegerProperty()
	pwd=db.StringProperty()

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
				self.redirect('/admin_login')
		else:
			self.redirect('/admin_login')


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
		self.response.out.write("hello")
		#check for admin login 
		nil=PageHandler.check_admin_login(self)
		#check for phone 
		phone=self.request.cookies.get("phone")
		if not phone:
			self.redirect('/signup')
		#get the pin entered 
		pin=self.request.get("pin")
		#check for pin match  
		if pin==GLOBAL_PIN:
			#save the mobile # and the password to the database
			#get the password, mobile #
			pwd=self.request.get("pwd")
			phone=self.request.cookies.get("phone")
			phone=int(phone)
			user=Users(phone=phone, pwd=pwd)
			user.put()
			self.redirect('/')
		else:
			self.response.out.write(render("confirm.html"))
			#add error message later
			
class Login(PageHandler):

	def get(self):
		#check admin login for beta
		nil=PageHandler.check_admin_login(self)
		#render the login form 
		self.response.out.write(render("login.html"))

	def post(self):
		#check admin login for beta
		nil=PageHandler.check_admin_login(self)
		#pull phone and password 
		phone=self.request.get("phone")
		pwd=self.request.get("pwd")
		if phone and pwd:
			#check whether we have right phone and pwd 
			query="SELECT * FROM Users"
			users=db.GqlQuery(query)
			self.response.out.write(render("test.html", users=users))
		else:
		#add error message
			self.redirect('/login')

class AdminLogin(PageHandler):

	def get(self):
		self.response.out.write(render("admin_login.html"))

	def post(self):
		admin_pwd=self.request.get("admin_pwd")
		if admin_pwd==VALID_PWD:
			self.response.set_cookie("admin_pwd", admin_pwd)
			self.redirect('/')
		else:
			self.response.out.write("invalid password")
	

class Main(PageHandler):

	def get(self):
		#check if logged in 
		nil=PageHandler.check_admin_login(self)
		#render the main template 
		self.response.out.write(render("main.html"))	
		

class ViewContacts(PageHandler):
	
	def get(self):
		#check if logged in 
		nil=PageHandler.check_admin_login(self)
		#render the view_contact template 
		self.response.out.write(render("view_contacts.html"))

class AddContact(PageHandler):

	def get(self):
		#check if logged in 
		nil=PageHandler.check_admin_login(self)
		#rendner the add_contact template
		self.response.out.write(render("add_contact.html"))
		
class EditCard(PageHandler):

	def get(self):
		#check if logged in 
		nil=PageHandler.check_admin_login(self)
		#rendner the add_contact template
		self.response.out.write(render("edit_card.html"))

class GetCSS(PageHandler):

	def get(self):
		#check if logged in 
		nil=PageHandler.check_admin_login(self)
		#render the main.css template
		self.response.out.write(render("main.css"))


app=webapp2.WSGIApplication([('/', Main),
				('/admin_login', AdminLogin),
				('/signup', Signup),
				('/confirm', Confirm),
				('/login', Login),
				('/view_contacts', ViewContacts),
				('/add_contact', AddContact),
				('/edit_card', EditCard),
				('/main.css', GetCSS)
				], debug=True)



