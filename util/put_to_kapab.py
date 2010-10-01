
import urllib
import urllib2

url = 'http://haiti.opensgi.net/mednet/api/0.1/rest/outsms/'


headers = {'Accept': 'application/json',
	   'Content-Type': 'application/x-www-form-urlencoded'	}

#values = {'status' : 'CM',
#          'sender' : '7602089488',
#          'message' : urllib.quote('test'),
#          'guid' : 'xxxxxxx',
#          'status_changed_date' : urllib.quote('2010-03-06 16:28:16')}


values = 'status=NW&sender=17602089488&message=frompythonfootime&guid=xxxx&status_changed_date=2010-10-06%2016:28:16&receipt=xxx'
	  
#data = urllib.urlencode(values)

data = values

req = urllib2.Request(url,data,headers)
req.get_method = lambda: 'PUT'

response = urllib2.urlopen(req)
print dir(response)
print "%d" % response.getcode()
print response.read()
