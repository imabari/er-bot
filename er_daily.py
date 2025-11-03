import datetime
import os

import logging

import requests
import tweepy

from atproto import Client

url = os.environ["URL"]

r = requests.get(url)
r.raise_for_status()

JST = datetime.timezone(datetime.timedelta(hours=+9))
today_in_japan = datetime.datetime.now(JST).strftime("%Y-%m-%d")

data = r.json().get(today_in_japan)

if data:

    hospital = []
    before = 0

    for i in data["hospitals"]:

        if before == i["type"]:

            kind = ""

        else:

            match i["type"]:
                case 15 | 70 | 80:
                    kind = f'【{i["medical"]}】'
                case 90:
                    kind = "【島しょ部】"
                case _:
                    kind = ""

        before = i["type"]

        hospital.append("\n".join([kind, i["name"], i["time"]]).strip())

    twit = "\n\n".join([data["date_week"]] + hospital + ["https://imabari.jpn.org/imabari119/"])
    bspost = "\n\n".join([data["date_week"]] + hospital)

    print(twit)

    bearer_token = os.environ["BEARER_TOKEN"]
    consumer_key = os.environ["CONSUMER_KEY"]
    consumer_secret = os.environ["CONSUMER_SECRET"]
    access_token = os.environ["ACCESS_TOKEN"]
    access_token_secret = os.environ["ACCESS_TOKEN_SECRET"]

    try:
        client = tweepy.Client(
            bearer_token,
            consumer_key,
            consumer_secret,
            access_token,
            access_token_secret,
        )
        
        client.create_tweet(text=twit)
    except Exception as e:
        logging.error(f"エラーが発生しました: {e}")
    
    try:
        at_user = os.environ["AT_USER"]
        at_pass = os.environ["AT_PASS"]
    
        api = Client()
        api.login(at_user, at_pass)
    
        api.send_post(bspost)

    except Exception as e:
        logging.error(f"エラーが発生しました: {e}")
