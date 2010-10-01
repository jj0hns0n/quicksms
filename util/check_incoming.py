
import sys, os
import time
import urllib2
import simplejson



sys.path.append('/home/mednet/build')
os.environ['DJANGO_SETTINGS_MODULE'] ='quicksms.settings'

from quicksms.sms.models import Incoming,Outgoing,Pull 
import pygsm
from datetime import datetime

modem = pygsm.GsmModem(port="/dev/ttyUSB1", baudrate=115200)

print "loaded modem"

while True:
    # check for new messages
    msg = modem.next_message()
    
    while msg:
        print msg
	i = Incoming()
        i.message = msg.text
        i.date_queued = datetime.now()
        i.date_sent = None
        i.sender = msg.sender
        i.save()
        
	
        #import code; code.interact(local=locals())
        
    # get all the data the incoming messages that haven't been sent to the ec2

    
        
    #url_file = urllib2.urlopen("http://haiti.opensgi.net/mednet/api/0.1/rest/outsms/")
    #json = url_file.read()
    #obj = simplejson.loads(json)
    #print obj
    #if Outgoing.objects.filter(
        
    


    time.sleep(2)
