import datetime
import pathlib
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup


base_url = "http://www.qq.pref.ehime.jp/qq38/WP0805/RP080501BL"

payload = {
    "_blockCd": "",
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

    # トークンを取得
    token = soup.find("input", attrs={"name": "_csrf"}).get("value")

    # トークンをセット
    payload["_csrf"] = token

    # URL生成
    url = urljoin(
        base_url, soup.find("form", attrs={"id": "_wp0805Form"}).get("action")
    )

    # データ送信
    r = s.post(url, data=payload)

# スクレイピング

soup = BeautifulSoup(r.content, "html.parser")

tables = soup.find_all("table", class_="comTblGyoumuCommon", summary="検索結果一覧を表示しています。")

result = []

for table in tables:

    # 日付取得
    date, week = table.td.get_text(strip=True).split()

    for trs in table.find_all("tr", id=[1, 2, 3]):
        data = (
            [None]
            + [list(td.stripped_strings) for td in trs.find_all("td", recursive=False)]
            + [date, week]
        )
        result.append(data[-5:])

# データラングリング

df0 = (
    pd.DataFrame(result)
    .fillna(method="ffill")
    .set_axis(["医療機関情報", "診療科目", "外来受付時間", "日付", "曜日"], axis=1)
)

# 日付変換
df0["date"] = pd.to_datetime(
    df0["日付"]
    .str.extract("(?P<year>\d{4})年(?P<month>\d{1,2})月(?P<day>\d{1,2})日")
    .astype(int)
).dt.date

# 医療機関情報
df1 = (
    df0["医療機関情報"]
    .apply(pd.Series)
    .drop([2, 4], axis=1)
    .rename(columns={0: "病院名", 1: "住所", 3: "TEL（昼）", 5: "TEL（夜）"})
)

# 医療科目
df2 = df0["診療科目"].apply(pd.Series).rename(columns={0: "診療科目"})

# 外来受付時間
df3 = df0["外来受付時間"].apply(pd.Series).rename(columns={0: "日中", 1: "夜間"})

# 結合
df4 = pd.concat([df0[["日付", "曜日", "date"]], df1, df2, df3], axis=1)

# 診療科目
df4["診療科目ID"] = df4["診療科目"].map({"指定なし": 0, "内科": 2, "小児科": 7})

# 外科系
df4["診療科目ID"].mask(df4["診療科目"].str.contains("外科", na=False), 1, inplace=True)

# 内科系
df4["診療科目ID"].mask(df4["診療科目"].str.contains("内科", na=False), 2, inplace=True)

# 島嶼部
df4["診療科目ID"].mask(
    df4["住所"].str.contains("吉海町|宮窪町|伯方町|上浦町|大三島町|関前", na=False), 9, inplace=True
)

# その他
df4["診療科目ID"] = df4["診療科目ID"].fillna(8).astype(int)

# 開始時間
df4["開始時間"] = pd.to_timedelta(df4["日中"].str.split("～").str[0] + ":00")

df4.sort_values(by=["date", "診療科目ID", "開始時間"]).reset_index(drop=True, inplace=True)


df = df4.reindex(
    columns=["日付", "曜日", "病院名", "住所", "TEL（昼）", "TEL（夜）", "診療科目", "日中", "夜間"]
)

# 日付作成
JST = datetime.timezone(datetime.timedelta(hours=+9))
dt_str = datetime.datetime.now(JST).date().isoformat()

p = pathlib.Path("data", f"{dt_str}.csv")
p.parent.mkdir(parents=True, exist_ok=True)

df.to_csv(p, index=False, encoding="utf_8_sig")
