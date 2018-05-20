# -encoding:utf-8
from template import *
from request import *
from gitignore import *
from google.appengine.api import urlfetch


def httpfunc(method, url, params, payload, header):
	if params:
		url+="?"+urllib.urlencode(params)
	r = urlfetch.fetch(url=url, payload=payload, method=urlfetch.POST if method=="POST" else urlfetch.GET, headers=header)
	return (r.status_code, r.content)


class work(workhandler):

	def get_token(text):
		data = {
			"document": {
				"type": "PLAIN_TEXT",
				"content": text
			},
			"encodingType": "UTF8",
		}
		params = {
			"key": google
		}
		headers = {
			'content-type': 'application/json'
		}
		req = request("post", "https://language.googleapis.com/v1beta2/documents:analyzeSyntax?key=" + google, data, None)
		j = req.json()
		r = [[i["partOfSpeech"]["tag"], i["text"]["content"]] for i in j["tokens"]]
		start = 0
		for w in r:
			tmp = text.find(w[1], start) + len(w[1])
			w[1] = text[start:tmp]
			start = tmp
		return r

	def work(s, i):
		sethttpfunc(httpfunc)
		if i.path == "/":
			s.write_temp("home.html", None)
		if i.path == "/admn":
			out = {
				"account": base.query(base.cate == "account").order(-base.bone).fetch(),
				"main": i.safe and base.get(urlsafe=i.safe)
			}
			s.write_temp("admn.html", out)
		if i.path == "/oauth":
			m = base.query(base.mail == i.oauth_token).get()
			m.temp["oauth_verifier"] = i.oauth_verifier
			r = request_oauth10(consumer_key, consumer_sec, None, None, "GET", "https://api.twitter.com/oauth/access_token", m.temp).getquery()
			m.data.update(r)
			m.name = r["screen_name"]
			m.put()
			s.redirect("/admn")
		if i.path == "/set":
			m = base(cate="account")
			if i.safe:
				m = base.get(urlsafe=i.safe)
			if i.command == "set":
				m.data = m.data or {}
				m.data.update({
					"positive": i.positive,
					"negative": i.nagative
				})
				m.put()
				s.redirect("/admn")
			if i.command == "acc":
				r = request_oauth10(consumer_key, consumer_sec, None, None, "POST", "https://api.twitter.com/oauth/request_token", {"oauth_callback": i.hosturl + "/oauth"})
				data = r.getquery()
				m.populate(temp=data, mail=data["oauth_token"])
				m.put()
				s.redirect("https://api.twitter.com/oauth/authorize?" + r.body)
			if i.command == "del":
				m.key.delete()
				s.redirect("/admn")
		if i.path == "/study":
			accounts = base.query(base.cate == "account").order(-base.bone).fetch()
			for i in accounts:
				r = "https://api.twitter.com/1.1/statuses/home_timeline.json", {"count": 10}
				r = request_oauth10(consumer_key, consumer_sec, i.data["oauth_token"], i.data["oauth_token_secret"], "GET", r[0], r[1])
				for j in r.getjson():
					if all(j["source"].find(k) < 0 for k in source):
						continue
					if "retweeted_status" in j:
						continue
					entity = j["entities"]
					if entity.get("media", None) or entity.get("urls", None):
						continue
					data = {
						"document": {"type": "PLAIN_TEXT", "content": "I am a Kyoto University student"},
						"encodingType": "UTF8",
					}
					headers = {
						'content-type': 'application/json'
					}
					req = request("post", "https://language.googleapis.com/v1beta2/documents:analyzeSyntax", {"key": google}, data, headers).getjson()
					pass
				pass
		if False:
			print(r.getjson())
			pass


app = work.getapp()
