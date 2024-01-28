from urllib.parse import urljoin

import pathlib

import pandas as pd
import requests
from bs4 import BeautifulSoup

base_url = "https://www.qq.pref.ehime.jp/qq38/WP0805/RP080501BL"

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

df0 = (
    pd.DataFrame(result)
    .ffill()
    .set_axis(["医療機関情報", "診療科目", "外来受付時間", "日付", "曜日"], axis=1)
)

# 日付変換
df0["date"] = pd.to_datetime(
    df0["日付"]
    .str.extract("(?P<year>\d{4})年(?P<month>\d{1,2})月(?P<day>\d{1,2})日")
    .astype(int)
)

# 日付と曜日を結合
df0["date_week"] = df0["日付"].str.cat(df0["曜日"], sep=" ")

# 医療機関情報
df0[["name", "address", "tel", "night_tel"]] = (
    df0["医療機関情報"].apply(pd.Series).drop([2, 4], axis=1)
)

# 医療科目
df0["medical"] = df0["診療科目"].str[0]
df0["type"] = df0["診療科目"].str[0]


# 受付時間
def transform_time(times):
    if len(times) == 1:
        return times[0]
    else:
        start_1st, end_1st = times[0].split("～")
        start_2nd, end_2nd = times[1].split("～")

        if end_1st == start_2nd:
            return "～".join([start_1st, end_2nd])
        else:
            return "\n".join(times)


df0["time"] = df0["外来受付時間"].apply(transform_time)

# ソート用

# 診療科目
df0["診療科目ID"] = df0["type"].map({"指定なし": 0, "内科": 2, "小児科": 7})

# 外科系
df0["診療科目ID"].mask(df0["type"].str.contains("外科", na=False), 1, inplace=True)

# 内科系
df0["診療科目ID"].mask(df0["type"].str.contains("内科", na=False), 2, inplace=True)

# 島しょ部
simanami_flag = df0["address"].str.contains("吉海町|宮窪町|伯方町|上浦町|大三島町|関前", na=False)

df0["type"].mask(simanami_flag, "島しょ部", inplace=True)
df0["診療科目ID"].mask(simanami_flag, 9, inplace=True)

# その他
df0["診療科目ID"] = df0["診療科目ID"].fillna(8).astype(int)

# 救急
df0["type"] = df0["type"].replace({"指定なし": "救急"})

df1 = (
    df0.sort_values(by=["date", "診療科目ID", "time"])
    .reset_index(drop=True)
    .reindex(columns=["date", "date_week", "type", "medical", "name", "address", "tel", "time"])
    .copy()
)
df1

p_csv = pathlib.Path("dist", "latest.csv")
p_csv.parent.mkdir(parents=True, exist_ok=True)

df1.to_csv(p_csv, encoding="utf_8_sig")

# json作成

# 位置情報付与
df2 = pd.read_csv("hosp_list.csv")

# 医療機関と位置情報を結合する
df3 = pd.merge(df1, df2, on="name", how="left")

df3["date"] = df3["date"].dt.strftime("%Y-%m-%d")
df3["time"] = df3["time"].str.replace("\n", " / ")

grp = (
    df3.groupby(["date", "date_week"])
    .apply(lambda x: x.drop(columns=["date", "date_week"]).to_dict(orient="records"))
    .reset_index()
)
grp.columns = ["date", "date_week", "hospital"]

grp_json = grp.to_json(orient="records", force_ascii=False, indent=4)

p_json = pathlib.Path("dist", "data.json")

with open(p_json, "w") as f:
    f.write(grp_json)
