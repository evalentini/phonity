

#imports#####################################################################################################
#############################################################################################################

#import data model 
from data_model import Users
from data_model import Cards

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
import sys

##configure jinja2 templates#################################################################################
#############################################################################################################

template_dir=os.path.join(os.path.dirname(__file__), 'templates')
jinja2_env=jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=True)

##define error classes#######################################################################################
#############################################################################################################

#class DuplicatedInstanceError(Exception):
#	def __init__(self, value):
#		self.value=value 
#	def __str__(self):
#		return repr(self.value)


##define database objects###################################################################################
###########################################################################################################
#class Users(db.Model):
#	phone=db.IntegerProperty()
#	pwd=db.StringProperty()
#
#	def put(self):
#		if (not self.is_saved()) and (Users.gql('WHERE phone = :1', self.phone).count()>0):
#			raise DuplicatedInstanceError (self.phone)
#		db.Model.put(self)
#
#class Cards(db.Model):
#	phone=db.IntegerProperty()
#	email=db.StringProperty()
#	name=db.StringProperty()
#
#	def put(self):
#		if (not self.is_saved()) and (Cards.gql('WHERE phone = :1', self.phone).count()>0):
#			raise DuplicatedInstanceError (self.phone)
#		db.Model.put(self)
#
#class Connections(db.Model):
#	user_phone=db.IntegerProperty()
#	connection_phone=db.IntegerProperty()
#	connection_status=db.StringProperty()	
#	def put(self):
#		user_phone=self.user_phone
#		connection_phone=self.connection_phone
#		query="WHERE user_phone = %s AND connection_phone = %s" %(user_phone, connection_phone)
#		if (not self.is_saved()) and (Connections.gql(query).count()>0):
#			raise DuplicatedInstanceError (self.phone)
#		db.Model.put(self)
#
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
	
	def check_user_login(self):
		#pull mobile phone # and password from cookies 
		phone=self.request.get("phone")
		pwd=self.request.get("pwd")
		#if cookies dont exist pull from get request 
		if not phone:
			phone=self.request.cookies.get("phone")
		if not pwd:
			pwd=self.request.cookies.get("pwd")
		#if they still dont exist then redirect to login screen 
		if not phone or not pwd:
			self.response.out.write(render("login.html", error="please log in"))
			return False
		else:
			#otherwise check whether login exists
			phone=int(phone)
			query="SELECT * FROM Users WHERE phone=%s AND pwd='%s'" %(phone, pwd)
			users=db.GqlQuery(query)
			user_count=users.count()
			if user_count>0:
				#set cookies 
					self.response.set_cookie("phone", str(phone))
					self.response.set_cookie("pwd", pwd)
					return True
			else:
				self.response.out.write(render("login.html", error="invalid number/password"))
				return False
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
		PHONE_RE=re.compile(r'[0-9]{10}$')
		if PHONE_RE.match(phone_number):
			#store phone # in a cookie 
			self.response.set_cookie("phone", phone_number)
			
			#generate random pin
			pin=GLOBAL_PIN
			#text pin to entered number
			nil=text("Your pin is "+pin, phone_number) 
			self.redirect("/confirm")
		else:
			self.response.out.write(render("signup.html", error="phone number must be 10 digits with no dashes"))
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

	def get(self, error=""):
		#check admin login for beta
		nil=PageHandler.check_admin_login(self)
		#render the login form 
		self.response.out.write(render("login.html", error=error, banner_message="dont have an account?  click sign up link above."))

	def post(self):
		#check admin login for beta
		nil=PageHandler.check_admin_login(self)
		#check login credentials
		valid_login=PageHandler.check_user_login(self) 
		if valid_login==True:
			self.redirect('/')

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
		#check admin login
		nil=PageHandler.check_admin_login(self)
		#check user login 
		valid_login=PageHandler.check_user_login(self)
		#render the main template
		if valid_login==True:
			self.response.out.write(render("main.html"))	
			

class ViewContacts(PageHandler):
	
	def get(self):
		#check if logged in 
		nil=PageHandler.check_admin_login(self)
		#render the view_contact template 
		self.response.out.write(render("view_contacts.html"))

class AddContact(PageHandler):

	def get(self):
		#check admin login 
		nil=PageHandler.check_admin_login(self)
		#check user login 
		valid_login=PageHandler.check_user_login(self)
		if valid_login==True:
			#rendner the add_contact template
			self.response.out.write(render("add_contact.html"))

	def post(self):
		#check admin login 
		nil=PageHandler.check_admin_login(self)
		#check user login
		valid_login=PageHandler.check_user_login(self)
		if valid_login==True:
			#check that we were provided with contact phone # and that it is valid phone #
			contact_phone=self.request.get("contact_phone")
			if contact_phone:
				PHONE_RE=re.compile(r'[0-9]{10}$')
				if PHONE_RE.match(contact_phone):
					#add the phone # as a requested contact 
					#INSERT CODE HERE
					#we were given valid phone # and can now check if number exists on the site 
					contact_phone=int(contact_phone)
					query="SELECT * FROM Users WHERE phone = %s" %contact_phone
					contact=db.GqlQuery(query)
					if contact.count()>0:
						#they exist and so we pass message saying connection request has been sent 
						self.response.out.write(render("main.html", content_override="connection request sent"))
					else:
						#they dont exist so we pass to the InviteContact handler 
						contact_phone=str(contact_phone)
						redirect_str="invite_contact/%s" %contact_phone
						self.redirect(redirect_str)
				else:
					self.response.out.write(render("add_contact.html", error="contact phone must be 10 digit number"))
			else:
				self.response.out.write(render("add_contact.html"), error="you didn't enter a phone number")
		 
		

class EditCard(PageHandler):

	def pull_fields(self, phone):
		#check whether there is already a linkedin email associated with the phone # 
		query="SELECT * FROM Cards WHERE phone = %s" %phone
		card=db.GqlQuery(query)
		if card.count()>0:
			for c in card:
				fields={'email': c.email, 'name': c.name}
				return fields
		

	def get(self):
		#check admin login 
		nil=PageHandler.check_admin_login(self)
		#check user login
		valid_login=PageHandler.check_user_login(self)
		if valid_login==True:
			#pull phone # 
			phone=int(self.request.cookies.get("phone"))
			#pull old email if it exists 
			fields=self.pull_fields(phone)
			if fields:
				email=fields['email']
				name=fields['name']
				if not email:
					email=""
				if not name:
					name=""
			else:
				email=""
				name=""
			#rendner the add_contact template
			#add the login cookie
			phone=self.request.cookies.get("phone")
			self.response.out.write(render("edit_card.html", phone=phone, email=email, name=name))

	def post(self):
		#check admin login 
		nil=PageHandler.check_admin_login(self)
		#check user login
		valid_login=PageHandler.check_user_login(self)
		if valid_login==True:
			#store the linkedin email and name
			email=self.request.get("email")
			name=self.request.get("name")
			#pull the phone number cookie 
			phone=self.request.cookies.get("phone")
			#check that both exist
			if not email or not phone or not name:
				self.response.out.write(render("edit_card.html", error="invalid phone/email/name"))
			else:
				#pull old email if it exists 
				phone=int(phone)
				old_fields=self.pull_fields(phone)
				if old_fields:
					old_email=old_fields['email']
					old_name=old_fields['name']
					query="SELECT * FROM Cards WHERE phone=%s" %phone
					card=db.GqlQuery(query)
					for c in card:
						c.email=email
						c.name=name
						db.put(c)	
				#update if already exists 
				#add data to the model
				else:
					card=Cards(phone=phone, email=email, name=name)
					card.put()
				self.response.out.write(render("main.html", content_override="update saved"))
				 	

class InviteContact(PageHandler):
	def get(self, contact_phone):
		#check admin login 
		nil=PageHandler.check_admin_login(self)
		#check user login
		valid_login=PageHandler.check_user_login(self)
		if valid_login==True:
			self.response.out.write(render("invite_contact.html", contact_phone=contact_phone))
		
	def post(self, contact_phone):
		#check admin login 
		nil=PageHandler.check_admin_login(self)
		#check user login
		valid_login=PageHandler.check_user_login(self)
		if valid_login==True:
			invite_message="you have been invited to join phonity.  go to phonity.appspot.com to join." 
			nil=text(invite_message, contact_phone) 
			self.response.out.write(render("main.html", content_override="invitation sent"))
			
class GetCSS(PageHandler):

	def get(self):
		#check if logged in 
		nil=PageHandler.check_admin_login(self)
		#render the main.css template
		self.response.out.write(render("main.css"))

class Logout(PageHandler):
	
	def get(self):
		self.response.set_cookie("pwd", "")
		self.response.set_cookie("phone", "")
		self.response.out.write(render("login.html", error="you are now logged out.  log back in above."))

class Test(PageHandler):

	def get(self):
		self.response.out.write(tester())

app=webapp2.WSGIApplication([('/', Main),
				('/admin_login', AdminLogin),
				('/signup', Signup),
				('/confirm', Confirm),
				('/login', Login),
				('/view_contacts', ViewContacts),
				('/add_contact', AddContact),
				('/edit_card', EditCard),
				('/invite_contact/([0-9]{10}$)', InviteContact),
				('/main.css', GetCSS),
				('/invite_contact/main.css', GetCSS),
				('/logout', Logout),
				('/test', Test)
				], debug=True)



