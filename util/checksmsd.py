#!/usr/bin/env python2.6
#
# Kapab MedNet SMS-checking daemon
#
# by Jeffery Johnson, Travis Pinney and Armen Babikyan

import sys, os
import time
import httplib
import urllib
import urllib2
import simplejson

import hashlib
import random

import serial

sys.path.append('/home/mednet/build')
os.environ['DJANGO_SETTINGS_MODULE'] ='quicksms.settings'

from quicksms.sms.models import Outgoing
from quicksms.sms.models import Incoming
from quicksms.sms.models import Pull
import pygsm
from datetime import datetime

def main(argv):
    # XXXX replace this with OptionParser()
    class Dummy:
        pass
    options = Dummy()


    options.debug = True

    options.port = "/dev/ttyUSB2"
    options.baudrate = 115200     # ***Required for MTCBA-G-U-F4 modem***
    options.outsms_url = "http://haiti.opensgi.net/mednet/api/0.1/rest/outsms/"
    options.insms_url = "http://haiti.opensgi.net/mednet/api/0.1/rest/insms/"
    options.polltime = 2          # in seconds


    if(options.outsms_url[-1] != '/'):
        options.outsms_url += '/'

    if(options.insms_url[-1] != '/'):
        options.insms_url += '/'

    run_forever(options)
    
def run_forever(options):

    modem = None

    jsonheaders = {'Accept': 'application/json',
                   'Content-Type': 'application/x-www-form-urlencoded'
                   }
        
    # Run forever
    while True:
        if(modem == None):
            # Open device
            print "Opening modem..."
            modem = pygsm.GsmModem(port=options.port,
                                   baudrate=options.baudrate)
            print "Loaded modem."

        print "Getting pull time..."

        #### Pull outgoing from EC2 ####

        # If there are outgoing messages to be pulled from the EC2
        # instance, download new messages and put them in the incoming queue
        # Find the last time that the pull occured 
        # Check for the special case that no pulls occured
        ps = Pull.objects.all().order_by('pull_date')
        if ps.count() == 0:
            pull_date = datetime.now()
        else:
            pull_date = ps.pull_date

        print pull_date

        # Convert datetime objects to seconds since epoch integer
        secs = time.mktime(datetime.timetuple(pull_date))
        # Convert to floats
        secs = float(secs)
        # NOTE: options.outsms_url should have a trailing / char
        outsms_url = "%s%s/" % (options.outsms_url, secs)

        print "outsms_url = %s" % outsms_url

        print "Getting outgoing messages from EC2"
        try:
            url_file = urllib2.urlopen(outsms_url)
            json = url_file.read()
            url_file.close()
            
            msg_list = simplejson.loads(json)
            print "len(msg_list) = %d" % len(msg_list)
            for msg in msg_list:
                # Create Django object from dict object and save to DB.
                try:
                    Outgoing.objects.get(guid=msg['guid'])
                    print "object already exists"
                except Outgoing.DoesNotExist:
                    print msg
                    o = Outgoing(**msg)
                    o.save()
                    
        except urllib2.URLError, e:
            print "ERROR: %s" % str(e)
            pass
        
        #### Send outgoing SMS to modem ####
        print "Sending outgoing messages"
        
        # If there are messages in the outgoing queue, send them to
        # the GPRS modem
        outgoing_msgs = Outgoing.objects.filter(receipt=None)
        
        print "outgoing_msgs = %s" % str(outgoing_msgs)
        print "len(outgoing_msgs) = %d" % len(outgoing_msgs)
        
        for msg in outgoing_msgs:
            print msg
            # Prepend "+" to sms number if it's not there
            if(msg.recipient[0] == "+"):
                smsnumber = msg.recipient
            else:
                smsnumber = "+%s" % (msg.recipient)

            # send_sms() doesn't return anything, but can throw:
            # * ValueError if the the sms text is too long
            # * serial.serialutil.SerialException if there's a problem
            # accessing the tty device
            try:
                modem.send_sms(smsnumber, msg.message)

                msg.device = "dell"
                msg.date_sent = datetime.now()
                msg.receipt = "SENT"
                msg.save()
            except ValueError, e:
                # SMS text is too long
                print str(e)
                print "continuing..."
                pass
            except serial.serialutil.SerialException, e:
                # Raise these and crash the program. Something external
                # should restart it.
                raise serial.serialutil.SerialException(e)

        #### Send receipts for outgoing SMSes to EC2 ####
        print "Sending outgoing receipts"
        #
        
        # If there are messages in the outgoing queue, send them to
        # the GPRS modem
        msgs = Outgoing.objects.filter(receipt="SENT")
        
        print "msgs = %s" % str(msgs)
        print "len(msgs) = %d" % len(msgs)

        for msg in msgs:
            date_sent = str(msg.date_queued).split('.')[0]

            values = {#'status' : 'NW',
                      #'sender' : msg.recipient,
                      #'message' : urllib.quote(msg.message),
                      'guid' : msg.guid,
                      'receipt' : hashlib.sha1(str(random.random())).hexdigest(),
                      'date_sent' : date_sent
                      }

            # Convert set of values to &-separated fields:
            data = urllib.urlencode(values)
            print "values['date_sent'] = %s, data = %s" % (values['date_sent'], data)

            #data = data.replace(" ", "%20")
            
            req = urllib2.Request(options.outsms_url, data, jsonheaders)
            # We use HTTP PUT here to update the object on the server side.
            req.get_method = lambda: 'PUT'

            try:
                response = urllib2.urlopen(req)
            except urllib2.URLError, e:
                print "ERROR: %s" % str(e)
                # TODO: add logic for what to do in the long term when
                # the medbook laptop can't phone home.
                raise

            code = response.getcode()
            if(code != httplib.OK):
                print "ERROR: bad http status code: %d" % code
                # continue to next message
                continue

            # here, we assume that we successfully sent a receipt.
            # change the state to SAA = Send And Acknowledged
            #msg.receipt = "SAA"

            # update the receipt in the database
            msg.receipt = values['receipt']
            
            print "saving receipt change..."
            msg.save()
            
        #### Receive incoming SMSes from modem ####
        print "Receiving incoming messages..."

        # If there are messages available at the GPRS modem, receive them
        # and put them in the incoming queue
        while(True):
            try:
                pygsm_msg = modem.next_message()
            except serial.serialutil.SerialException, e:
                # Raise these and crash the program. Something external
                # should restart it.
                print str(e)
                raise serial.serialutil.SerialException(e)
    
            if(pygsm_msg == None):
                # No messages are available. break.
                break

            msg = Incoming()
            msg.sender = pygsm_msg.sender    # string, sending phone number
            msg.message = pygsm_msg.text     # string, actual message
            msg.date_sent = pygsm_msg.sent   # datetime object, reported by modem
            msg.date_queued = datetime.now()
            #pygsm_msg.device    # string, device that received the SMS
            msg.save()

        # If there are incoming messages to be pushed (i.e. POST) to the EC2
        # instance, identify those messages from the incoming queue, pickle them
        # urlencode (NOT to json), and POST (with mime-type as JSON).  Yeah, this
        # last part is weird.

        #### POST incoming SMS to EC2 ####
        print "Posting incoming messages to EC2"

        incoming_msgs = Incoming.objects.filter(receipt=None)
        
        print "incoming_msgs = %s" % str(incoming_msgs)
        print "len(incoming_msgs) = %d" % len(incoming_msgs)

        for msg in incoming_msgs:
            date_sent = str(msg.date_queued).split('.')[0]

            values = {'status' : 'NW',
                      'sender' : msg.sender,
                      'message' : urllib.quote(msg.message),
                      'guid' : msg.guid,
                      'date_sent' : date_sent,
                      }

            # Convert set of values to &-separated fields:
            data = urllib.urlencode(values)
            #data = data.replace(" ", "%20")
            print "values['date_sent'] = %s, data = %s" % (values['date_sent'], data)

            req = urllib2.Request(options.insms_url, data, jsonheaders)

            try:
                response = urllib2.urlopen(req)
            except urllib2.URLError, e:
                print "ERROR: %s" % str(e)
                # TODO: add logic for what to do in the long term when
                # the medbook laptop can't phone home.
                raise

            code = response.getcode()
            if(code != httplib.OK):
                print "ERROR: bad http status code: %d" % code
                # continue to next message
                continue

            try:
                # Parse the body of the HTTP response
                # We get the same json object back, with the receipt field filled in
                json = response.read()
                msg2 = simplejson.loads(json)
                a = msg2['receipt']
                msg.receipt = a

                # If we got this far, we assume the incoming message has
                # been successfully sent to EC2
                msg.date_sent = datetime.now()

                msg.save()
            except:
                raise

        # Sleep
        time.sleep(options.polltime)


if(__name__ == "__main__"):
    sys.exit(main(sys.argv))
    
