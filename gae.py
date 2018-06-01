# -encoding:utf-8
import urllib
from template import *
from request import *
from gitignore import *
from datetime import timedelta, datetime
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
	start, result = 0, []
	for i in j["tokens"]:
		text = i["text"]["content"]
		type = i["partOfSpeech"]["tag"]
		end = alltext.find(text, start)
		result.append({
			"backtype": "", "backtext": "", "nexttype": "", "nexttext": "",
			"thistype": i["partOfSpeech"]["tag"],
			"thistext": i["text"]["content"],
			"before": alltext[start:end]
		})
		start = end + len(text)
	for i, x in enumerate(result):
		if i != 0:
			result[i - 1].update({"nexttext": x["thistext"], "nexttype": x["thistype"]})
		if i != len(result) - 1:
			result[i + 1].update({"backtext": x["thistext"], "backtype": x["thistype"]})
	return result


def friend(ck, cs, tk, ts, count, positive, negative):
	def find(ck, cs, tk, ts, target, count, positive, negative):
		# 条件に適合し未だフォローして無いならフォロー
		# 条件に適応せずフォローしているなら案フォロー
		if target:
			target = {"user_id": target}
		else:
			target = {}
		friends = request_oauth10(ck, cs, tk, ts, "GET", "https://api.twitter.com/1.1/friends/ids.json", target).getjson()
		friends = friends["ids"]
		friends = random.sample(friends, min(count, len(friends)))
		for n, i in enumerate(friends):
			user = request_oauth10(ck, cs, tk, ts, "GET", "https://api.twitter.com/1.1/users/show.json", {"user_id": i}).getjson()
			# 条件
			tmp = (user["screen_name"] + user["name"] + user["location"] + user["description"]).lower()
			flag = any(tmp.find(w.lower()) >= 0 for w in positive) and all(tmp.find(w.lower()) < 0 for w in negative)
			flag = flag and not user["protected"]
			flag = flag and (user["friends_count"] / user["followers_count"]) < 1.5
			# 処理
			print("num:{0} flag:{1} follow:{2} screen:{3}".format(n, flag, user["following"], user["screen_name"]))
			if flag and not user["following"]:
				request_oauth10(ck, cs, tk, ts, "POST", "https://api.twitter.com/1.1/friendships/create.json", {"user_id": i})
				print("follow")
			if user["following"] and not flag:
				request_oauth10(ck, cs, tk, ts, "POST", "https://api.twitter.com/1.1/friendships/destroy.json", {"user_id": i})
				print("unfollow")
		return friends

	if True:
		r = find(ck, cs, tk, ts, None, count, positive, negative)
	if r:
		r = find(ck, cs, tk, ts, random.choice(r), count, positive, negative)


def generate(every):
	generate = [{"thistype": "", "thistext": "", "before": ""}]
	while True:
		candidate=[range(len(every))]
		for i in range(len(generate)):
			next=[]
			for j in candidate[-1]:
				if j - i >=0:
					a,b = every[j - i],generate[-i-1]
					if (a.get("backtext", 1), a.get("backtype", 1)) == (b.get("thistext", 1), b.get("thistype", 1)):
						next.append(j)
			if next:
				candidate.append(next)
				if len(next)==1:
					break
			else:
				break
		if len(candidate)==1:
			return []#error
		elif len(candidate)==2:
			candidate=candidate[-1]
		else:
			if len(candidate[-1])>=2:
				candidate=candidate[-1]
			else:
				candidate=candidate[-2]
		generate.append(every[random.choice(candidate)])
		if generate[-1]["nexttext"] == "":
			break
	return generate


def synth(generate):
	return "".join(x["before"] + x["thistext"] for x in generate)


class work(workhandler):
	def work(s, i):
		sethttpfunc(httpfunc)
		if i.path == "/":
			out = {
				"account": base.query(base.cate == "account").order(-base.bone).fetch()
			}
			s.write_temp("home.html", out)
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
			m = base(cate="account", data={})
			if i.safe:
				m = base.get(urlsafe=i.safe)
			if i.command == "set":
				m.data.update({
					"positive": i.positive.split(),
					"negative": i.negative.split()
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
		if i.path == "/friend":
			accounts = base.query(base.cate == "account").order(-base.bone).fetch()
			for a in accounts:
				friend(consumer_key, consumer_sec, a.data["oauth_token"], a.data["oauth_token_secret"], 10, a.data["positive"], a.data["negative"])

		if i.path == "/timeline":
			accounts = base.query(base.cate == "account").order(-base.bone).fetch()
			for a in accounts:
				s.write(u",".join(a.data["positive"])+u"<br>")
				r = "https://api.twitter.com/1.1/statuses/home_timeline.json", {"count": 10}
				r = request_oauth10(consumer_key, consumer_sec, a.data["oauth_token"], a.data["oauth_token_secret"], "GET", r[0], r[1])
				r = r.getjson()
				if isinstance(r,list):
					for j in r:
						# 条件絞り込み
						if all(j["source"].find(k) < 0 for k in ["Twitter for iPhone", "Twitter for Android", "Twitter Web Client"]):
							continue
						if j.get("retweeted_status",0):
							continue
						if j.get("in_reply_to_status_id",0):
							continue
						entity = j["entities"]
						if entity.get("urls",0):
							continue
						m = base(cate="tweet", kusr=a.key, data=j, temp=gettoken(j["text"]))
						m.put()
						s.write(j["text"]+u"<br>")
				else:
					s.write_json(r)
			base.delete_multi(base.query(base.cate == "tweet", base.bone < datetime.now() - timedelta(days=15)).fetch(keys_only=True))
		if i.path == "/update":
			deadline = datetime.now() - timedelta(minutes=int(i.minutes))
			account = base.query(base.cate == "account").fetch()
			account = filter(lambda n: n.last < deadline, account)
			account = account and account[0]
			if account:
				s.write(u",".join(account.data["positive"])+u"<br>")
				tweets = base.query(base.cate == "tweet", base.kusr == account.key).order(-base.bone).fetch()
				if tweets[0].bone<datetime.now() - timedelta(hours=1):
					s.write(u"too old<br>")
				else:
					tokens = sum((t.temp for t in tweets), [])
					text1 = synth(tokens)
					output = generate(tokens)
					text2 = synth(output)
					r = "POST", "https://api.twitter.com/1.1/statuses/update.json", {"status": text2}
					r = request_oauth10(consumer_key, consumer_sec, account.data["oauth_token"], account.data["oauth_token_secret"], r[0], r[1], r[2])
					s.write(u"{name}\nstatus = {status}".format(name=account.name,status=text2))
				account.put()
			else:
				s.write(u"empty<br>")
		if i.path == "/forget":
			base.delete_multi(base.query(base.cate == "tweet").fetch(1000,keys_only=True))
			s.write("deletall")
		if i.path == "/test":
			gettoken(u"")



app = work.getapp()