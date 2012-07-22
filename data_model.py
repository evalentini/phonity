

#imports#####################################################################################################
#############################################################################################################
#import library for sending SMS through google voice
#import datastore 
from google.appengine.ext import db

#import python standard distribution libraries
import webapp2
import settings
import os
import re
import sys


##define error classes#######################################################################################
#############################################################################################################

class DuplicatedInstanceError(Exception):
	def __init__(self, value):
		self.value=value 
	def __str__(self):
		return repr(self.value)


##define database objects###################################################################################
###########################################################################################################
class Users(db.Model):
	phone=db.IntegerProperty(required=True)
	pwd=db.StringProperty(required=True)

	def put(self):
		if (not self.is_saved()) and (Users.gql('WHERE phone = :1', self.phone).count()>0):
			raise DuplicatedInstanceError (self.phone)
		db.Model.put(self)

class Cards(db.Model):
	phone=db.IntegerProperty(required=True)
	email=db.StringProperty()
	linkedin_url=db.StringProperty()
	name=db.StringProperty()

	def put(self):
		if (not self.is_saved()) and (Cards.gql('WHERE phone = :1', self.phone).count()>0):
			raise DuplicatedInstanceError (self.phone)
		db.Model.put(self)

class Connections(db.Model):
	user_phone=db.IntegerProperty(required=True)
	connection_phone=db.IntegerProperty(required=True)
	connection_status=db.StringProperty(required=True)
	date_connected=db.DateProperty(auto_now_add=True)	
	def put(self):
		user_phone=self.user_phone
		connection_phone=self.connection_phone
		query="WHERE user_phone = %s AND connection_phone = %s" %(user_phone, connection_phone)
		if (not self.is_saved()) and (Connections.gql(query).count()>0):
			raise DuplicatedInstanceError (self.user_phone)
		db.Model.put(self)

	#connection status options
	#requested: user sent request to connect to connection but connection has not yet been confirmed
	#nd_app": someone else sent you a connection request but you need to approve
	#active: connection has been approved by both parties  
	#self: connection status for the user's own phone #

