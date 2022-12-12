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
    dt_now = datetime.datetime.now(JST)

    # 来月
    # dt_now = datetime.datetime.now(JST) + datetime.timedelta(days=28)

    # URL作成
    url = f"http://www.city.imabari.ehime.jp/kouhou/koho/{dt_now.year}{dt_now.month:02}/kyukyu.pdf"

    pdf_file = get_file(url)

    p = pdfbox.PDFBox()

    p.pdf_to_images(pdf_file, imageType="png", dpi=200)

    twit = f"{dt_now.month}月の救急病院などの当直表 #imabari\n{url}\n\n【子供の急な病気に困ったら】\n小児救急電話相談（#8000）へ電話\n\nこどもの救急\nhttp://kodomo-qq.jp/\n\n【救急車を呼んだ方がいいか？迷ったら】\n全国版救急受信アプリ　Ｑ助\n\nWeb https://www.fdma.go.jp/relocation/neuter/topics/filedList9_6/kyukyu_app/kyukyu_app_web/index.html\niOS https://itunes.apple.com/jp/app/id1213690742\nAndroid https://play.google.com/store/apps/details?id=jp.co.elmc.emergencyapp"

    consumer_key = os.environ["CONSUMER_KEY"]
    consumer_secret = os.environ["CONSUMER_SECRET"]
    access_token = os.environ["ACCESS_TOKEN"]
    access_token_secret = os.environ["ACCESS_TOKEN_SECRET"]

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth)
    
    media_id = api.media_upload("kyukyu1.png").media_id
    api.update_status(status=twit, media_ids=[media_id])
