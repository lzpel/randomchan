#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time, random, json, os, hmac, hashlib, base64, json, re
import urllib2
from urllib import quote, urlencode

class response:
	def __init__(self, r):
		self.code = r[0]
		self.body = r[1]

	def getjson(self):
		return json.loads(self.body)

	def getquery(self):
		return {k: v for k, v in [i.split("=") for i in self.body.split("&")]}
#
def httpfunc(method, url, params, payload, header):
	if params:
		url+="?"+urlencode(params)
	h = urllib2.urlopen(urllib2.Request(url, payload, header))
	return h.getcode(),h.read()

def sethttpfunc(func):
	global httpfunc
	httpfunc=func

def request(method, url, params, payload, header):
	return response(httpfunc(method.upper(),url,params,payload,header or {}))

def request_oauth10(consumer_key, consumer_secret, access_token, access_token_secret, method, url, param):
	method=method.upper()
	access_token, access_token_secret = access_token or "", access_token_secret or ""
	param = {k: str(v.encode("utf-8") if isinstance(v, unicode) else v) for k, v in (parse_qs(param) if isinstance(param, str) else param).items()}
	baseparam = {
		"oauth_token": access_token,
		"oauth_consumer_key": consumer_key,
		"oauth_signature_method": "HMAC-SHA1",
		"oauth_timestamp": str(int(time.time())),
		"oauth_nonce": str(random.getrandbits(64)),
		"oauth_version": "1.0"
	}
	signature = dict(baseparam)
	signature.update(param)
	signature = '&'.join('{0}={1}'.format(quote(key, ''), quote(signature[key], '~')) for key in sorted(signature))
	signature = ("{0}&{1}".format(consumer_secret, access_token_secret), '{0}&{1}&{2}'.format(method, quote(url, ''), quote(signature, '')))
	signature = base64.b64encode(hmac.new(signature[0], signature[1], hashlib.sha1).digest())
	header = dict(baseparam)
	header.update({"oauth_signature": signature})
	header = ",".join("{0}={1}".format(quote(k, ''), quote(header[k], '~')) for k in sorted(header))
	header = {"Authorization": 'OAuth {0}'.format(header)}
	if method=="GET":
		return request(method, url, param, None, header)
	if method=="POST":
		return request(method, url, None, urlencode(param), header)


def twitter_post_test(consumer_key, consumer_secret,callback):
	r = request_oauth10(consumer_key, consumer_secret, None, None, "POST", "https://api.twitter.com/oauth/request_token", callback or {"oauth_callback":callback})
	print "open {0}?{1}".format("https://api.twitter.com/oauth/authorize", r.body)
	r = r.getquery()
	r["oauth_verifier"] = raw_input("varifier:")
	r = request_oauth10(consumer_key, consumer_secret, None, None, "GET", "https://api.twitter.com/oauth/access_token", r).getquery()
	tk, ts = r["oauth_token"], r["oauth_token_secret"]
	r = request_oauth10(consumer_key, consumer_secret, tk, ts, "POST", "https://api.twitter.com/1.1/statuses/update.json", {"status": "そろそろ大阪へ向かおう"})
	print(r.getjson())
