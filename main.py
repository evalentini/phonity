

#imports#####################################################################################################
#############################################################################################################

#import library for sending SMS through google voice
from voice import Voice
from util import input 
#import jinja2 template library 
import jinja2

#import python standard distribution libraries 
import webapp2
import settings
import os
import re

##configure jinja2 templates#################################################################################
#############################################################################################################

template_dir=os.path.join(os.path.dirname(__file__), 'templates')
jinja2_env=jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=True)

##define helper functions###################################################################################
############################################################################################################

def render(template, **params):
	t=jinja2_env.get_template(template)
	return t.render(params)

def text(message=None, number=None, email="evan.valentini@gmail.com", pwd="robots25"):
	voice=Voice()
	voice.login(email, pwd)
	voice.send_sms(number, message)
	
VALID_PWD="shabanaSnuggle"


###SIGN UP PAGE HANDLER###################################################################################################################################################################################

class Signup(webapp2.RequestHandler):
	def get(self):
		self.response.out.write(render("signup.html"))
	
	def post(self):
		#pull phone number entered
		phone_number=self.request.get("phone_number")
		admin_pwd=self.request.cookies.get("admin_pwd")
		pwd_check= admin_pwd==VALID_PWD
		#confirm admin password
		if pwd_check==False:
			self.redirect('/login') 
		#regex verify phone number  
		#should be 10 digits
		PHONE_RE=re.compile(r'[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]')
		if PHONE_RE.match(phone_number):
			#generate random pin
			pin="1592"
			#text pin to entered number
			nil=text("Your pin is "+pin, phone_number) 
		else:
			self.response.out.write(render("signup.html"))
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
				('/signup', Signup)
				], debug=True)



