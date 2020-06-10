import datetime
import os
import pathlib

import pdfbox
import requests
import tweepy


def get_file(url):

    r = requests.get(url)

    p = pathlib.Path(pathlib.PurePath(url).name)

    with p.open(mode="wb") as fw:
        fw.write(r.content)

    return p


if __name__ == "__main__":

    JST = datetime.timezone(datetime.timedelta(hours=+9), "JST")

    # 今月
    # dt_now = datetime.datetime.now(JST)

    # 来月
    dt_now = datetime.datetime.now(JST) + datetime.timedelta(days=28)

    # URL作成
    url = f"http://www.city.imabari.ehime.jp/kouhou/koho/{dt_now.year}{dt_now.month:02}/kyukyu.pdf"

    pdf_file = get_file(url)

    p = pdfbox.PDFBox()

    p.pdf_to_images(pdf_file, imageType="png", dpi=200)

    twit = f"{dt_now.month}月の救急病院などの当直表 #imabari\n{url}"

    consumer_key = os.environ["CONSUMER_KEY"]
    consumer_secret = os.environ["CONSUMER_SECRET"]
    access_token = os.environ["ACCESS_TOKEN"]
    access_token_secret = os.environ["ACCESS_TOKEN_SECRET"]

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth)
    api.update_with_media(status=twit, filename="kyukyu1.png")
