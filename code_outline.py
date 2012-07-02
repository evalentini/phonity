

###################### outline of code for google voice python library #######

## 2 key pieces of functionality to understand:
	#1.) login function  -> log in to gv account (i.e. google account) 
	#2.) sms function (send sms via gvoice)

##1.) Login

##a.) setting special attribute information (which is irrelevant)
##b.) setting username and password (prompts user if not set)
##C.) send http request for user authentication (the important part):
	#C1.) calls separate function (__do__page) 
	#C2.) passes following info:
		#C2A.) 'login' => action to be completed
		#C2B.) dictionary setting acct type, email, pwd, service headers
		 
