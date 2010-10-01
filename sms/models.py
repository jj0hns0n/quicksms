from django.db import models
from datetime import datetime
import hashlib
import random


# Create your models here.


def get_random():
    return hashlib.sha1(str(random.random())).hexdigest()

class Pull(models.Model):
    date_pulled = models.DateTimeField(default=datetime.now())
    

class Outgoing(models.Model):
    guid = models.CharField(max_length=512)
    recipient = models.CharField(max_length=25)
    message = models.CharField(max_length=160)
    date_queued = models.DateTimeField(default=datetime.now)
    date_sent = models.DateTimeField(null=True, blank=True)
    receipt = models.CharField(max_length=512,null=True,blank=True)



class Incoming(models.Model):    
    guid = models.CharField(max_length=512,default=get_random)
    sender = models.CharField(max_length=25)
    message = models.CharField(max_length=255, null=True, blank=True)
    date_queued = models.DateTimeField(default=datetime.now)
    date_sent = models.DateTimeField(null=True, blank=True)
    receipt = models.CharField(max_length=512,null=True,blank=True)
    


    


    
    
                                   
                                   
