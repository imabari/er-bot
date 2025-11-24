import os
import logging

import pandas as pd
import requests
import tweepy

from atproto import Client

url = os.environ["URL"]

df0 = pd.read_csv(url, parse_dates=["date"])

islands = [
    "喜多嶋診療所",
    "有津むらかみクリニック",
    "大三島中央病院",
    "斎藤クリニック",
    "片山医院",
    "はかた外科胃腸科",
    "しのざき整形外科",
    "松浦医院"
]

df0["medical"] = df0["medical"].mask(df0["name"].isin(islands), "島しょ部")
df0["medical"] = df0["medical"].mask(df0["medical"] == "指定なし", "")

df0["date_week"] = df0["date"].dt.strftime("%Y年%m月%d日").str.cat(df0["week"], sep=" ")

today = pd.Timestamp.now(tz="Asia/Tokyo").date().isoformat()

df1 = df0[df0["date"] == today].copy()

if not df1.empty:

    date_week = df1["date_week"].iloc[0]

    hospital = []
    before = ""

    for _, row in df1.iterrows():

        if row["medical"] == before or row["medical"] == "":

            kind = ""

        else:
            kind = f'【{row["medical"]}】'

        before = row["medical"]

        hospital.append("\n".join([kind, row["name"], row["time"]]).strip())

    twit = "\n\n".join([date_week] + hospital + ["https://imabari.jpn.org/imabari119/"])
    bspost = "\n\n".join([date_week] + hospital)

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
