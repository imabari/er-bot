import hashlib
import json
import os
import pathlib
from urllib.parse import urljoin

import requests
import tweepy


def download_file(url, save_path):
    response = requests.get(url)
    response.raise_for_status()

    with open(save_path, "wb") as fw:
        fw.write(response.content)


def calculate_file_hash(file_path):
    try:
        with open(file_path, "rb") as fr:
            digest = hashlib.file_digest(fr, "sha256")
            return digest.hexdigest()
    except FileNotFoundError:
        print("ファイルが見つかりません")
        return None


def load_previous_hash(hash_file):
    try:
        with open(hash_file, "r") as fp:
            data = json.load(fp)
            return data.get("hash")
    except FileNotFoundError:
        print("前回のハッシュファイルが見つかりませんでした")
        return None
    except (json.JSONDecodeError, KeyError):
        print("JSON ファイルに有効なハッシュが含まれていません")
        return None


def save_hash_to_file(hash_value, hash_file):
    with open(hash_file, "w") as fh:
        json.dump({"hash": hash_value}, fh)


def main():
    base_url = "https://www.city.imabari.ehime.jp/kouhou/koho/"
    response = requests.get(base_url)
    response.raise_for_status()

    url = urljoin(response.url, "kyukyu.pdf")

    save_path = pathlib.Path(pathlib.PurePath(url).name)
    save_path.parent.mkdir(parents=True, exist_ok=True)

    download_file(url, save_path)
    current_hash = calculate_file_hash(save_path)

    hash_file = pathlib.Path("hash.json")
    previous_hash = load_previous_hash(hash_file)

    if previous_hash != current_hash:
        save_hash_to_file(current_hash, hash_file)

        # Twitterへのツイート

        bearer_token = os.environ["BEARER_TOKEN"]
        consumer_key = os.environ["CONSUMER_KEY"]
        consumer_secret = os.environ["CONSUMER_SECRET"]
        access_token = os.environ["ACCESS_TOKEN"]
        access_token_secret = os.environ["ACCESS_TOKEN_SECRET"]

        client = tweepy.Client(
            bearer_token,
            consumer_key,
            consumer_secret,
            access_token,
            access_token_secret,
        )
        client.create_tweet(text="広報いまばりの救急病院が更新されています")


if __name__ == "__main__":
    main()
