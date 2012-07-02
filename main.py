from voice import Voice
from util import input 
#import sms
import webapp2
import settings
import os

VALID_PWD="shabanaSnuggle"

class Login(webapp2.RequestHandler):
	def get(self):
		login_screen="""
			<html>
			<body>
			<form method="post">
				<input type="password" name="admin_pwd">
				<input type="submit" value="login">
			</form>
			</body>
			</html>"""
		self.response.out.write(login_screen)

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
			voice.send_sms(2015624311, "I am a machine")
			self.response.out.write("message sent")		
		else:
			self.redirect('/login')

app=webapp2.WSGIApplication([('/', Welcome),
				('/login', Login)
				], debug=True)



