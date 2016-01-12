# Open Global Server Load Balancer (ogslb)
# Copyright (C) 2010 Mitchell Broome
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import socket
import time
import re
import pprint
import logging
import string 
import subprocess
from random import Random

# fire up the logger
logger = logging.getLogger("ogslb")

# timeout in seconds
timeout = 10
socket.setdefaulttimeout(timeout)

import urllib2

# setup pprint for debugging
pp = pprint.PrettyPrinter(indent=4)

# this is the HTTP test.  Here, we actually make a http request 
# and figure out assorted important things about what we found.

# do the actual http get and return headers
def getUrl(url, headers):
   rheaders = {}
   ret = None
   code = 0
   req = urllib2.Request(url,None,headers)
   try:
      response = urllib2.urlopen(req)
      code = response.code
      rheaders = response.info()
   except urllib2.HTTPError, e:
      code = e.code
      rheaders = e.info()
      ret = e.read()
   except IOError, e:
      if hasattr(e, 'reason'):
         reason = e.reason
      elif hasattr(e, 'code'):
         code = e.code
         rheaders = e.info()
      else:
         pp.pprint(e)
         pp.pprint(e.reason)

   try:
      ret = response.read()
   except:
      # response error
      pass
   return((ret,code,rheaders))

      
# deal with preparing to get the content and handling it's response
def get(data, queue, passCount, Config):
   reason = ''
   # we create a Host: header for the hostname we are testing.
   # this makes http/1.1 happy
   headers = {'Host': data['name']}
   
   try: # if there was a response defined to look for, make a regex
      prog = re.compile(data['response']);
      checkResponse = 1
   except: # otherwise disable the content match and just look at status codes
      checkResponse = 0

   # format the url
   try:
      url = 'http://' + data['address'] + ":" + data['port'] + data['url']
   except:
      url = 'http://' + data['address'] + data['url']
      data['port'] = 80

   # do the get and time it
   t1 = time.time()
   r, code, rheaders = getUrl(url, headers)
   t2 = time.time()

   # Test by TMA
   output = subprocess.Popen(["httping", "-G", "-h", data['name'], data['address'], "-c", "1"], stdout=subprocess.PIPE).communicate()[0]
   t3 = re.search("time=([0-9].*\.[0-9]*) ms", output).group(1)


   # if we are doing a content match, get busy
   if checkResponse == 1:
      try:
         if code >= 400:
            found = 0
         elif prog.search(r):
            found = 1
         else:
            found = 0
      except:
         found = 0
   else: # otherwise, handle the return code
      if code >= 400:
         found = 0
      else:
         found = 1

   # now figure out how long it took to do the test
   data['speed'] = ((t2-t1)*1000.0)
   data['speed'] = (t3)

   # If the get wasn't sucessful, figure out why
   if found == 0:
      errorID = ''.join( Random().sample(string.letters+string.digits, 12) )
      if data['speed'] >= 10000: # too slow
         reason = 'timeout'
      elif code >= 400: # got a status code over 400
         reason = "status: \"" + str(code) + "\" saved error: " + data['Type'] + '-' + str(data['port']) + '/' + data['name'] + '/' + errorID

      elif r != None: # got content but it didn't match
         reason = "content match: \"" + data['response'] + "\" saved error: " + data['Type'] + '-' + str(data['port']) + '/' + data['name'] + '/' + errorID
      elif (code == 0) and (data['speed'] < 10000):
         reason = "funk: code=0 and speed: " + str(data['speed'])
      else: # what the heck happened...
         reason = "content match error" + " saved error: " + data['Type'] + '-' + str(data['port']) + '/' + data['name'] + '/' + errorID


   # build up data with what we have discovered
   data['status'] = found
   data['when'] = t1
   data['pass'] = passCount
   data['reason'] = reason

   # throw the collected data in the queue to be jammed into the database
   queue.put(data)

   if found == 0:
      logger.debug("test failed: %s" % reason)

