import hashlib
import json
import os
import pathlib
from urllib.parse import urljoin, urlparse
import fitz

import requests
import tweepy
from atproto import Client


def download_file(url, save_path):
    response = requests.get(url)
    response.raise_for_status()

    with open(save_path, "wb") as fpw:
        fpw.write(response.content)


def calculate_file_hash(file_path):
    try:
        with open(file_path, "rb") as fpr:
            digest = hashlib.file_digest(fpr, "sha256")
            return digest.hexdigest()
    except FileNotFoundError:
        print("ファイルが見つかりません")
        return None


def load_previous_hash(hash_file):
    try:
        with open(hash_file, "r") as fhr:
            data = json.load(fhr)
            return data.get("hash")
    except FileNotFoundError:
        print("前回のハッシュファイルが見つかりませんでした")
        return None
    except (json.JSONDecodeError, KeyError):
        print("JSON ファイルに有効なハッシュが含まれていません")
        return None


def save_hash_to_file(hash_value, hash_file):
    with open(hash_file, "w") as fhw:
        json.dump({"hash": hash_value}, fhw)


def main():
    base_url = "https://www.city.imabari.ehime.jp/kouhou/koho/"
    response = requests.get(base_url)
    response.raise_for_status()

    url = urljoin(response.url, "kyukyu.pdf")

    yyyymm = urlparse(response.url).path.strip("/").split("/")[-1]
    year = int(yyyymm[:4])
    month = int(yyyymm[4:])

    save_path = pathlib.Path(pathlib.PurePath(url).name)
    save_path.parent.mkdir(parents=True, exist_ok=True)

    download_file(url, save_path)
    current_hash = calculate_file_hash(save_path)

    hash_file = pathlib.Path("hash.json")
    previous_hash = load_previous_hash(hash_file)

    if previous_hash == current_hash:
        save_hash_to_file(current_hash, hash_file)

        consumer_key = os.environ["CONSUMER_KEY"]
        consumer_secret = os.environ["CONSUMER_SECRET"]
        access_token = os.environ["ACCESS_TOKEN"]
        access_token_secret = os.environ["ACCESS_TOKEN_SECRET"]

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)

        xapi = tweepy.API(auth)
        client = tweepy.Client(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
        )

        at_user = os.environ["AT_USER"]
        at_pass = os.environ["AT_PASS"]

        api = Client()
        api.login(at_user, at_pass)
        
        # PDFを画像に変換
        doc = fitz.open(save_path)
        
        for i, page in enumerate(doc, 1):
            pix = page.get_pixmap(dpi=200)
            pix.save(f"kyukyu{i}.png")

        # X

        image_path = "kyukyu1.png"
        message = f"{month}月の救急病院などの当直表 #imabari\n{url}\n\n【子供の急な病気に困ったら】\n・小児救急電話相談（#8000）へ電話\n\n【救急車を呼んだ方がいいか？迷ったら】\n・えひめ救急電話相談（#7119）"

        media = xapi.media_upload(filename=image_path)
        client.create_tweet(text=message, media_ids=[media.media_id])

        with open(image_path, "rb") as f:
            img_data = f.read()
            api.send_image(text=text, image=img_data, image_alt=f"{year}年{month}月 救急病院")

if __name__ == "__main__":
    main()
