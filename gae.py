# -encoding:utf-8
from template import *
from request import *
from gitignore import *
from google.appengine.api import urlfetch


def httpfunc(method, url, params, payload, header):
	if params:
		url += "?" + urllib.urlencode(params)
	r = urlfetch.fetch(url=url, payload=payload, method=urlfetch.POST if method == "POST" else urlfetch.GET, headers=header)
	return (r.status_code, r.content)


def gettoken(alltext):
	data = json.dumps({"document": {"type": "PLAIN_TEXT", "content": alltext}, "encodingType": "UTF8", })
	r = request("post", "https://language.googleapis.com/v1beta2/documents:analyzeSyntax", {"key": google}, data, {'content-type': 'application/json'})
	j = r.getjson()
	start,result=0,[]
	for i in j["tokens"]:
		text=i["text"]["content"]
		type=i["partOfSpeech"]["tag"]
		end= alltext.find(text, start)
		result.append({"thistype":i["partOfSpeech"]["tag"],"thistext":i["text"]["content"],"before":alltext[start:end]})
		start=end+len(text)
	for i,x in enumerate(result):
		if i!=0:
			result[i-1].update({"nexttext":x["thistext"],"nexttype":x["thistype"]})
		if i!=len(result)-1:
			result[i+1].update({"backtext":x["thistext"],"backtype":x["thistype"]})
	return result


class work(workhandler):
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
		if i.path == "/store":
			accounts = base.query(base.cate == "account").order(-base.bone).fetch()
			for a in accounts:
				r = "https://api.twitter.com/1.1/statuses/home_timeline.json", {"count": 10}
				r = request_oauth10(consumer_key, consumer_sec, a.data["oauth_token"], a.data["oauth_token_secret"], "GET", r[0], r[1])
				for j in r.getjson():
					#条件絞り込み
					if all(j["source"].find(k) < 0 for k in source):
						continue
					if "retweeted_status" in j:
						continue
					entity = j["entities"]
					if entity.get("media", None) or entity.get("urls", None):
						continue
					m=base(cate="tweet", kusr=a.key, data=j, temp=gettoken(j["text"]))
					m.put()
			base.delete_multi(base.query(base.cate == "tweet", base.bone < datetime.datetime.now()-datetime.timedelta(days=30)).fetch(keys_only=True))
		if i.path=="/update":
			accounts = base.query(base.cate == "account").order(-base.bone).fetch()
			for a in accounts:
				tweets = base.query(base.cate == "tweet",base.kusr==a.key).order(-base.bone).fetch()
				every=[]
				original=tweets[0].temp
				for t in tweets:
					every.extend(t.temp)
				generate=list(original)
				for j,x in enumerate(original):
					choice=[]
					for k in every:
						if x.get("backtext",1)==k.get("backtext",1) and x.get("backtype",1)==k.get("backtype",1):
							if x.get("nexttext",1)==k.get("nexttext",1) and x.get("nexttype",1)==k.get("nexttype",1):
								choice.append(k)
					generate[j]=random.choice(choice)
				status="".join(x["before"]+x["thistext"] for x in generate)
				r = "POST","https://api.twitter.com/1.1/statuses/update.json", {"status": status}
				r = request_oauth10(consumer_key, consumer_sec, a.data["oauth_token"], a.data["oauth_token_secret"], r[0], r[1],r[2])


		if i.path == "/show":
			print(json.dumps([k.data for k in base.query(base.cate == "tweet").order(-base.bone).fetch()],indent=4))
		if i.path == "/test":
			base.query(base.cate == "tweet").order(-base.bone).fetch()


app = work.getapp()
