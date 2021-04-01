import datetime
import os
import re
import time
from urllib.parse import urljoin

import requests
import tweepy
from bs4 import BeautifulSoup


consumer_key = os.environ["CONSUMER_KEY"]
consumer_secret = os.environ["CONSUMER_SECRET"]
access_token = os.environ["ACCESS_TOKEN"]
access_token_secret = os.environ["ACCESS_TOKEN_SECRET"]


def scraping(html):

    soup = BeautifulSoup(html, "html.parser")

    # スクレイピング
    tables = soup.find_all(
        "table", class_="comTblGyoumuCommon", summary="検索結果一覧を表示しています。"
    )

    JST = datetime.timezone(datetime.timedelta(hours=+9), "JST")
    dt_now = datetime.datetime.now(JST)

    for table in tables:

        date, week = table.td.get_text(strip=True).split()
        day = datetime.datetime.strptime(date, "%Y年%m月%d日")

        if day.date() == dt_now.date():

            result = []

            # 前データ　初期値
            dprev = ["今治市医師会市民病院", "今治市別宮町７－１－４０"]

            for trs in table.find_all("tr", id=[1, 2, 3]):

                id = trs.get("id")

                data = list(trs.stripped_strings)

                # 市町村を削除
                if id == "1" and data[0] == "今治市":
                    del data[0]

                # 電話番号を削除
                for _ in range(2):
                    if len(data) > 4 and data[2].startswith("TEL"):
                        del data[2:4]

                # id=2の場合は病院名と住所を結合
                if id == "2":
                    data = dprev[:2] + data

                # print(id, data)

                # 前データとしてセット
                dprev = data

                hospital = dict(zip(["name", "address", "subject"], data[0:4]))

                hospital["class"] = 8

                # 外来受付時間を分割
                t = [j for i in data[3:] for j in i.split("〜")]

                # 外来受付時間の前半開始時間と後半終了時間をセット
                hospital["time"] = "～".join([t[0], t[-1]])

                # 外来受付時間の前半終了時間と後半開始時間が違う場合
                if len(t) == 4 and t[1] != t[2]:
                    hospital["time"] = "\n".join(["～".join(t[:2]), "～".join(t[2:])])

                # 診療科目
                # 救急   : 0
                # 外科系 : 1
                # 内科系 : 2
                # 小児科 : 4
                # その他 : 8
                # 島嶼部 : 9

                # 外科系
                if "外科" in hospital["subject"]:
                    hospital["class"] = 1

                # 内科系
                elif "内科" in hospital["subject"]:
                    hospital["class"] = 2

                # 小児科
                elif hospital["subject"] == "小児科":
                    hospital["class"] = 4

                # 救急
                elif hospital["subject"] == "指定なし":
                    hospital["class"] = 0
                    hospital["subject"] = ""

                # 住所が島嶼部の場合は、診療科目を島嶼部に変更
                match = re.search("(吉海町|宮窪町|伯方町|上浦町|大三島町|関前)", hospital["address"])

                if match:

                    hospital["class"] = 9
                    hospital["subject"] = "島嶼部"

                # 診療科目に【】を追加
                if hospital["subject"]:
                    hospital["subject"] = f'【{hospital["subject"]}】'

                # 病院情報をテキスト化
                hospital["text"] = "\n".join(
                    [hospital["subject"], hospital["name"], hospital["time"]]
                ).strip()

                # リストに追加
                result.append(hospital)

            # 診療科目、時間でソート
            result.sort(key=lambda x: (x["class"], x["time"]))

            # 日付をテキスト化
            twit_date = f"{date} {week}"

            # 陸地部で結合
            twit_riku = "\n\n".join(
                [i["text"] for i in result if i["class"] < 9]
            ).strip()

            # 島嶼部で結合
            twit_sima = "\n\n".join(
                [i["text"] for i in result if i["class"] > 8]
            ).strip()

            # 日付、陸地部、島嶼部を結合
            twit_all = "\n\n".join([twit_date, twit_riku, twit_sima]).strip()

            # print(twit_all)
            # print("-" * 20)

            auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
            auth.set_access_token(access_token, access_token_secret)

            api = tweepy.API(auth)

            # 140文字以内か
            if len(twit_all) <= 140:
                # 全文ツイート
                api.update_status(twit_all)

            else:
                # 陸地部ツイート
                api.update_status("\n\n".join([twit_date, twit_riku]).strip())
                
                time.sleep(30)
                
                # 島嶼部他ツイート
                api.update_status("\n\n".join([twit_date, twit_sima]).strip())


            break


if __name__ == "__main__":

    base_url = "http://www.qq.pref.ehime.jp/qq38/WP0805/RP080501BL"

    payload = {
        "blockCd[3]": "",
        "forward_next": "",
        "torinBlockDetailInfo.torinBlockDetail[0].blockCheckFlg": "0",
        "torinBlockDetailInfo.torinBlockDetail[1].blockCheckFlg": "0",
        "torinBlockDetailInfo.torinBlockDetail[2].blockCheckFlg": "0",
        "torinBlockDetailInfo.torinBlockDetail[3].blockCheckFlg": "1",
        "torinBlockDetailInfo.torinBlockDetail[4].blockCheckFlg": "0",
        "torinBlockDetailInfo.torinBlockDetail[5].blockCheckFlg": "0",
        "torinBlockDetailInfo.torinBlockDetail[6].blockCheckFlg": "0",
        "torinBlockDetailInfo.torinBlockDetail[7].blockCheckFlg": "0",
        "torinBlockDetailInfo.torinBlockDetail[8].blockCheckFlg": "0",
        "torinBlockDetailInfo.torinBlockDetail[9].blockCheckFlg": "0",
        "torinBlockDetailInfo.torinBlockDetail[10].blockCheckFlg": "0",
        "torinBlockDetailInfo.torinBlockDetail[11].blockCheckFlg": "0",
        "torinBlockDetailInfo.torinBlockDetail[12].blockCheckFlg": "0",
    }

    # 地域選択ページのセッション作成
    with requests.Session() as s:

        r = s.get(base_url)

        soup = BeautifulSoup(r.content, "html.parser")

        # トークンを取得
        token = soup.find(
            "input", attrs={"name": "org.apache.struts.taglib.html.TOKEN"}
        ).get("value")

        # トークンをセット
        payload["org.apache.struts.taglib.html.TOKEN"] = token

        # URL生成
        url = urljoin(
            base_url, soup.find("form", attrs={"name": "wp0805Form"}).get("action")
        )

        # URL確認
        # print(url)

        # データ送信
        r = s.post(url, data=payload)

    scraping(r.content)
