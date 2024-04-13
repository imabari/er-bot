import datetime
import os

import requests
import tweepy

from atproto import Client

url = "https://imabari.github.io/er-bot/data.json"

r = requests.get(url)
r.raise_for_status()

JST = datetime.timezone(datetime.timedelta(hours=+9))
today_in_japan = datetime.datetime.now(JST).strftime("%Y-%m-%d")

for data in r.json():
    if data["date"] == today_in_japan:
        hospital = []

        for i in data["hospital"]:
            
            match i["type"]:
                case 0:
                    kind = ""
                case 9:
                    kind = "【島しょ部】"
                case _:
                    kind = f'【{i["medical"]}】'

            hospital.append("\n".join([kind, i["name"], i["time"]]).strip())

        twit = "\n\n".join([data["date_week"]] + hospital)

        print(twit)

        bearer_token = os.environ["BEARER_TOKEN"]
        consumer_key = os.environ["CONSUMER_KEY"]
        consumer_secret = os.environ["CONSUMER_SECRET"]
        access_token = os.environ["ACCESS_TOKEN"]
        access_token_secret = os.environ["ACCESS_TOKEN_SECRET"]

        client = tweepy.Client(
            bearer_token,
            consumer_key,
            consumer_secret,
            access_token,
            access_token_secret,
        )
        client.create_tweet(text=twit)

        at_user = os.environ["AT_USER"]
        at_pass = os.environ["AT_PASS"]

        api = Client()
        api.login(at_user, at_pass)

        api.send_post(twit)

        break

    else:
        continue
