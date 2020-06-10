import datetime
from urllib.parse import urljoin
import pathlib

import pandas as pd
import requests
from bs4 import BeautifulSoup

JST = datetime.timezone(datetime.timedelta(hours=+9), "JST")
dt_now = datetime.datetime.now(JST)
dt_str = dt_now.date().isoformat()


def scraping(html):

    soup = BeautifulSoup(r.content, "html.parser")

    tables = soup.find_all(
        "table", class_="comTblGyoumuCommon", summary="検索結果一覧を表示しています。"
    )

    result = []
    before = ["今治市医師会市民病院", "今治市別宮町７−１−４０", "TEL（昼）", "0898-22-7611", "TEL（夜）", None]

    for table in tables:

        # 日付取得
        date, week = table.td.get_text(strip=True).split()

        for trs in table.find_all("tr", id=[1, 2, 3]):

            id = trs.get("id")

            data = list(trs.stripped_strings)

            if id == "3":
                temp = [id, date, week] + data
            elif id == "2":
                temp = [id, date, week] + before + data
            else:
                temp = [id, date, week] + data[1:]

            # TEL（昼）追加
            if temp[5] != "TEL（昼）":
                temp = temp[:5] + ["TEL（昼）", None] + temp[5:]

            # TEL（夜）追加
            if temp[7] != "TEL（夜）":
                temp = temp[:7] + ["TEL（夜）", None] + temp[7:]

            # 夜間へ移動
            if not temp[10].startswith("0"):
                temp = temp[:10] + [None] + temp[10:]

            result.append(temp)
            before = temp[3:9]

    df = pd.DataFrame(
        result,
        columns=[
            "ID",
            "日付",
            "曜日",
            "病院名",
            "住所",
            "昼",
            "TEL（昼）",
            "夜",
            "TEL（夜）",
            "科目",
            "日中",
            "夜間",
        ],
    )

    df.drop(columns=["昼", "夜"], inplace=True)

    p = pathlib.Path("data", f"{dt_str}.csv")
    p.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(p, index=False, encoding="utf_8_sig")


if __name__ == "__main__":

    base_url = "http://www.qq.pref.ehime.jp/qq38/WP0805/RP080501BL.do"

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

    with requests.Session() as s:

        r = s.get(base_url)

        soup = BeautifulSoup(r.content, "html.parser")
        token = soup.find(
            "input", attrs={"name": "org.apache.struts.taglib.html.TOKEN"}
        ).get("value")

        payload["org.apache.struts.taglib.html.TOKEN"] = token

        url = urljoin(
            base_url, soup.find("form", attrs={"name": "wp0805Form"}).get("action")
        )
        r = s.post(url, data=payload)

    scraping(r.content)
