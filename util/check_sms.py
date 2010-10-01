
import sys, os
import time
import urllib2
import simplejson



sys.path.append('/home/mednet/build')
os.environ['DJANGO_SETTINGS_MODULE'] ='quicksms.settings'

from quicksms.sms.models import Incoming,Outgoing,Pull 
import pygsm
from datetime import datetime

modem = pygsm.GsmModem(port="/dev/ttyUSB0", baudrate=115200)

print "loaded modem"




while True:

    # find the last time that the pull occured 

    # check for the special case that no pulls occured
    ps = Pull.objects.all().order_by('pull_date')
    if ps.count() == 0:
	pull_date = datetime.now()
    else:
	pull_date = ps.pull_date

    # send the incoming ( sms to be sent to kapab ) messages

    msg = modem.next_message()
    while msg:
        print msg


    #outgoing = Outgoing.objects.filter(date_sent=None)
    #print outgoing 
    #for o in outgoing:
    #    print o
    #    modem.send_sms("+1%s" % (o.sender), o.text)
    #    o.sent_date = datetime.now()
    #    o.save()

    # download new messages from other website

    url_file = urllib2.urlopen("http://haiti.opensgi.net/mednet/api/0.1/rest/outsms/")
    json = url_file.read()
    obj = simplejson.loads(json)
    print obj
    #if Outgoing.objects.filter(
        
    


    time.sleep(2)
