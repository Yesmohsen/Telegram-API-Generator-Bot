import logging
import random
import time

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


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
        if len(inputs) >= 2:
            app_id = inputs[0].string.strip()
            api_hash = inputs[1].string.strip()
            return True, {"app_id": app_id, "api_hash": api_hash}
        logger.warning("Found configuration page but couldn't extract app_id/api_hash")
        return False, {"error": "Could not extract credentials from page"}

    tg_hash_input = soup.find("input", {"name": "hash"})
    if tg_hash_input:
        tg_hash = tg_hash_input.get("value")
        return False, {"tg_app_hash": tg_hash}

    logger.error("Unexpected page structure. Title: %s", title)
    return False, {"error": f"Unexpected page: {title}"}


def create_new_tg_app(cookie, tg_hash):
    ts = int(time.time())
    shortname = f"app{ts}"
    data = {
        "hash": tg_hash,
        "app_title": f"App{ts}",
        "app_shortname": shortname,
        "app_url": "",
        "app_platform": "desktop",
        "app_desc": "",
    }
    resp = requests.post(
        "https://my.telegram.org/apps/create",
        data=data,
        headers={"Cookie": cookie},
    )
    resp.raise_for_status()

    if resp.text == "true":
        time.sleep(1)
        return True

    logger.error("App creation failed: %s", resp.text[:200])
    return False
