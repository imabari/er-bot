import os
import pathlib

import pandas as pd

url = os.environ["URL"]

df0 = pd.read_csv(url)
df1 = pd.read_csv("hosp_list.csv")

# 医療機関と位置情報を結合する
df_hosp = pd.merge(df0, df1, on="name", how="left")

df_hosp.to_csv("latest.csv", index=False)

grp_hosp = (
    df_hosp.groupby(["date", "date_week"])
    .apply(lambda x: x.drop(columns=["date", "date_week"]).to_dict(orient="records"))
    .reset_index()
)

grp_hosp

grp_hosp.columns = ["date", "date_week", "hospital"]

grp_hosp_json = grp_hosp.to_json(orient="records", force_ascii=False, indent=4)

p = pathlib.Path("dist", "data.json")
p.parent.mkdir(parents=True, exist_ok=True)

with open(p, "w") as f:
    f.write(grp_hosp_json)
