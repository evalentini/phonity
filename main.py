

#imports#####################################################################################################
#############################################################################################################

#import data model
from data_model import DuplicatedInstanceError 
from data_model import Users
from data_model import Cards
from data_model import Connections 

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
jinja2_env=jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), extensions=['jinja2.ext.autoescape'], autoescape=True)
#extensions=['jinja2.ext.autoescape']

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
			#try to add the user 
			try:
				user.put()
				card=Cards(phone=phone)
				card.put()
				connection=Connections(user_phone=phone, connection_phone=phone, connection_status="self")
				connection.put()
				self.redirect('/')
			except DuplicatedInstanceError:
				error="you're already signed up.  click login (upper right) to login."
				self.response.out.write(render("confirm.html", error=error))
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
			#convert contact list to dictionary 
			#create empty list 
			contact_list=list()
			#loop through connections table and pull data for every connection 
			user_phone=self.request.cookies.get("phone")
			query="SELECT * FROM Connections WHERE user_phone=%s" %user_phone
			connections=db.GqlQuery(query)
			#pull connection information 
			for c in connections:
				#temporary solution: add stubs for all the fields we want to show
				entry={}
				entry["name"]="stub"
				entry["date_connected"]="stub"
				entry["phone"]=c.connection_phone
				entry["email"]="stub"
				entry["linkedin_url"]="http://www.linkedin.com"
				entry["status"]="stub"
				entry["status_action"]="stub"
				#add the date the connection was established 
				if c.date_connected: entry["date_connected"]=c.date_connected
				#check whether the connection status is requested (if so we dont want to display the connections info 
				if c.connection_status=="requested":
					entry["status"]="request sent"
					status_action="""<a href="/delete_connection/%s"> remove</a>""" %c.connection_phone 
					entry["status_action"]=status_action
				else:
					#if the connection is not pending approval then we can display everything
					if c.connection_status=="nd_app":
						#approval pending 
						entry["status"]="wants to connect"
						status_action="""<a href="/approve_connection/%s"> connect</a>""" %c.connection_phone
						entry["status_action"]=status_action
					if c.connection_status=="active":
						#connection is active, action is to delete connection
						entry["status"]="connected"
						status_action="""<a href="/delete_connection/%s"> remove</a>""" %c.connection_phone 
						entry["status_action"]=status_action
					if c.connection_status=="self":
						#this is the user.  Action is to edit card 
						entry["status"]="this is you"
						entry["status_action"]="""<a href="/edit_card">edit your card</a>"""
					#now add the connections information from their card (if available)
					query="SELECT * FROM Cards WHERE phone=%s" %c.connection_phone
					connection_card=db.GqlQuery(query)
					for card in connection_card:
						if card.email: entry["email"]=card.email
						if card.linkedin_url: entry["linkedin_url"]=card.linkedin_url
						if card.name: entry["name"]=card.name	 
				#add the entry to the contact list
				contact_list.append(entry)
			#draw the view contacts form 
			self.response.out.write(render("view_contacts.html", contact_list=contact_list))	
		else:
			self.redirect('/login')	
	
				

#class ViewContacts(PageHandler):
#	
#	def get(self):
#		#check if logged in 
#		nil=PageHandler.check_admin_login(self)
#		#render the view_contact template 
#		self.response.out.write(render("view_contacts.html"))

class AddContact(PageHandler):

	def get(self):
		#check admin login 
		nil=PageHandler.check_admin_login(self)
		#check user login 
		valid_login=PageHandler.check_user_login(self)
		if valid_login==True:
			#render the add_contact template
			self.response.out.write(render("add_contact.html"))

	def post(self):
		#check admin login 
		nil=PageHandler.check_admin_login(self)
		#check user login
		valid_login=PageHandler.check_user_login(self)
		if valid_login==True:
			#check that we were provided with contact phone # and that it is valid phone #
			c_phone=self.request.get("contact_phone")
			if c_phone:
				PHONE_RE=re.compile(r'[0-9]{10}$')
				if PHONE_RE.match(c_phone):
					#add the phone # as a requested contact 
					u_phone=self.request.cookies.get("phone")
					#convert phone #s to integer 
					c_phone=int(c_phone)
					u_phone=int(u_phone)
					try:
						conn=Connections(user_phone=u_phone, connection_phone=c_phone, connection_status="requested")
						conn.put()
						#add a second connection request associated with the connection's phone #
						conn2=Connections(user_phone=c_phone, connection_phone=u_phone, connection_status="nd_app")
						conn2.put()
						#we were given valid phone # and can now check if number exists on the site 
						query="SELECT * FROM Users WHERE phone = %s" %c_phone
						contact=db.GqlQuery(query)
						if contact.count()>0:
							#they exist and so we pass message saying connection request has been sent 
							self.response.out.write(render("main.html", content_override="connection request sent"))
						else:
							#they dont exist so we pass to the InviteContact handler 
							c_phone=str(c_phone)
							redirect_str="invite_contact/%s" %c_phone
							self.redirect(redirect_str)
					except DuplicatedInstanceError:
						error="you are already connected to %s" %c_phone
						self.response.out.write(render("add_contact.html", error=error))
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
				fields={'email': c.email, 'linkedin_url': c.linkedin_url, 'name': c.name}
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
				linkedin_url=fields['linkedin_url']
				name=fields['name']
				if not email: email=""
				if not linkedin_url: linkedin_url=""
				if not name: name=""
			else:
				email=""
				linkedin_url=""
				name=""
			#render the add_contact template
			#add the login cookie
			phone=self.request.cookies.get("phone")
			self.response.out.write(render("edit_card.html", phone=phone, email=email, linkedin_url=linkedin_url, name=name))

	def post(self):
		#check admin login 
		nil=PageHandler.check_admin_login(self)
		#check user login
		valid_login=PageHandler.check_user_login(self)
		if valid_login==True:
			#store the linkedin email and name
			email=self.request.get("email")
			linkedin_url=self.request.get("linkedin_url")
			name=self.request.get("name")
			#pull the phone number cookie 
			phone=self.request.cookies.get("phone")
			#check that both exist
			#if not email or not phone or not name:
			#	self.response.out.write(render("edit_card.html", error="invalid phone/email/name"))
			#else:
			#pull old email if it exists
			if not email: email=""
			if not linkedin_url: linkedin_url="http://www.linkedin.com"
			if not name: name="" 
			phone=int(phone)
			old_fields=self.pull_fields(phone)
			if old_fields:
				old_email=old_fields['email']
				old_linkedin_url=old_fields['linkedin_url']
				old_name=old_fields['name']
				query="SELECT * FROM Cards WHERE phone=%s" %phone
				card=db.GqlQuery(query)
				if card.count()>0:
					for c in card:
						c.email=email
						c.linkedin_url=linkedin_url
						c.name=name
						db.put(c)	
				#update if already exists 
				#add data to the model
				else:
					card=Cards(phone=phone, email=email, linkedin_url=linkedin_url,  name=name)
					card.put()
				self.response.out.write(render("main.html", content_override="update saved"))
				 	

class ApproveConnection(PageHandler):
	def get(self, connection_phone):
		#check admin login 
		nil=PageHandler.check_admin_login(self)
		#check user login 
		valid_login=PageHandler.check_user_login(self)
		if valid_login==True:
			#get user phone and check whether connection status is pending approval from user 
			user_phone=self.request.cookies.get("phone")
			query="SELECT * FROM Connections WHERE user_phone=%s AND connection_phone=%s" %(user_phone, connection_phone)
			#check whether connection status exists 
			connection=db.GqlQuery(query)
			if connection.count()>0:
				for c in connection:
					if c.connection_status=="nd_app":
						c.connection_status="active"
						db.put(c)
				#redirect to the view contacts page
				self.redirect('/view_contacts')	
			else:	
				self.response.out.write(query)
		else:
			self.redirect('/login') 

class DeleteConnection(PageHandler):
	def get(self, c_phone):
		#check admin login 
		nil=PageHandler.check_admin_login(self)
		#check user login 
		valid_login=PageHandler.check_user_login(self)
		if valid_login==True:
			#get user phone and delete connection entry if users are connected 
			u_phone=self.request.cookies.get("phone")
			#convert phone #s to integer
			u_phone=int(u_phone)
			c_phone=int(c_phone)
			#check whether users are connected 
			query="SELECT * FROM Connections WHERE user_phone=%s AND connection_phone=%s" %(u_phone, c_phone)
			connection=db.GqlQuery(query)
			if connection.count()>0:
				db.delete(connection)
				#delete the associated connection (between the logged in user and the connected user)
				assoc_query="SELECT * FROM Connections WHERE user_phone=%s AND connection_phone=%s" %(c_phone, u_phone)
				assoc_connection=db.GqlQuery(assoc_query)
				db.delete(assoc_connection)
				#redirect to the view contacts page
				self.redirect('/view_contacts')
			else:
				self.response.out.write(query)
		else:
			self.redirect('/login')

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
			#fix message below so that person's name shows up 
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

class Cancel(PageHandler):
	
	def get(self):
		#check admin login 
		nil=PageHandler.check_admin_login(self)
		#check user login 
		valid_login=PageHandler.check_user_login(self)
		if valid_login==True:
			phone=self.request.cookies.get("phone")
			#delete all the information in database tables attached to user
			#in the Users table 
			query="SELECT * FROM Users WHERE phone=%s" %phone
			user=db.GqlQuery(query)
			db.delete(user)
			#in the Cards table 
			query="SELECT * FROM Cards WHERE phone=%s" %phone 
			card=db.GqlQuery(query)
			db.delete(card)
			#in the Connections table
			query="SELECT * FROM Connections WHERE user_phone=%s" %phone
			connections=db.GqlQuery(query)
			db.delete(connections)
			self.response.out.write(render("cancel.html")) 	
				
		else:
			self.redirect('/login')

app=webapp2.WSGIApplication([('/', Main),
				('/admin_login', AdminLogin),
				('/signup', Signup),
				('/confirm', Confirm),
				('/login', Login),
				('/view_contacts', Main),
				('/add_contact', AddContact),
				('/edit_card', EditCard),
				('/delete_connection/([0-9]{10}$)', DeleteConnection),
				('/approve_connection/([0-9]{10}$)', ApproveConnection),
				('/invite_contact/([0-9]{10}$)', InviteContact),
				('/main.css', GetCSS),
				('/invite_contact/main.css', GetCSS),
				('/logout', Logout),
				('/cancel', Cancel)
				], debug=True)



