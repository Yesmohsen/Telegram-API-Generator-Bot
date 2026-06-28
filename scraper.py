import random

import requests
from bs4 import BeautifulSoup


def request_tg_code_get_random_hash(phone):
    url = "https://my.telegram.org/auth/send_password"
    data = {"phone": phone}
    resp = requests.post(url, data=data)
    resp.raise_for_status()
    return resp.json()["random_hash"]


def login_step_get_stel_cookie(phone, random_hash, code):
    url = "https://my.telegram.org/auth/login"
    data = {
        "phone": phone,
        "random_hash": random_hash,
        "password": code,
    }
    resp = requests.post(url, data=data)
    resp.raise_for_status()

    if resp.text == "true":
        return True, resp.headers.get("Set-Cookie")
    return False, resp.text


def scarp_tg_existing_app(cookie):
    url = "https://my.telegram.org/apps"
    headers = {"Cookie": cookie}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, features="html.parser")
    title = soup.title.string

    if "configuration" in title:
        inputs = soup.find_all("span", {"class": "input-xlarge"})
        app_id = inputs[0].string
        api_hash = inputs[1].string
        return True, {"app_id": app_id, "api_hash": api_hash}

    tg_hash = soup.find("input", {"name": "hash"}).get("value")
    return False, {"tg_app_hash": tg_hash}


def create_new_tg_app(cookie, tg_hash):
    url = "https://my.telegram.org/apps/create"
    headers = {"Cookie": cookie}
    data = {
        "hash": tg_hash,
        "app_title": "TestApp1",
        "app_shortname": f"testapp{random.randint(3, 99999)}",
        "app_url": "",
        "app_platform": "desktop",
        "app_desc": "",
    }
    resp = requests.post(url, data=data, headers=headers)
    resp.raise_for_status()
    return resp
