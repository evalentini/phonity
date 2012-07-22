

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
	phone=db.IntegerProperty()
	pwd=db.StringProperty()

	def put(self):
		if (not self.is_saved()) and (Users.gql('WHERE phone = :1', self.phone).count()>0):
			raise DuplicatedInstanceError (self.phone)
		db.Model.put(self)

class Cards(db.Model):
	phone=db.IntegerProperty()
	email=db.StringProperty()
	name=db.StringProperty()

	def put(self):
		if (not self.is_saved()) and (Cards.gql('WHERE phone = :1', self.phone).count()>0):
			raise DuplicatedInstanceError (self.phone)
		db.Model.put(self)

class Connections(db.Model):
	user_phone=db.IntegerProperty()
	connection_phone=db.IntegerProperty()
	connection_status=db.StringProperty()	
	def put(self):
		user_phone=self.user_phone
		connection_phone=self.connection_phone
		query="WHERE user_phone = %s AND connection_phone = %s" %(user_phone, connection_phone)
		if (not self.is_saved()) and (Connections.gql(query).count()>0):
			raise DuplicatedInstanceError (self.phone)
		db.Model.put(self)


