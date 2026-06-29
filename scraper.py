import logging
import time

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

REQUEST_TIMEOUT = 30


def make_session(proxy=None):
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    if proxy:
        session.proxies.update({"http": proxy, "https": proxy})
    return session


def request_tg_code_get_random_hash(phone, session=None):
    if session is None:
        session = make_session()
    url = "https://my.telegram.org/auth/send_password"
    data = {"phone": phone}
    resp = session.post(url, data=data, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()["random_hash"]


def login_step_get_stel_cookie(phone, random_hash, code, session=None):
    if session is None:
        session = make_session()
    url = "https://my.telegram.org/auth/login"
    data = {
        "phone": phone,
        "random_hash": random_hash,
        "password": code,
    }
    resp = session.post(url, data=data, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()

    if resp.text == "true":
        return True, session
    return False, resp.text


def scarp_tg_existing_app(session):
    url = "https://my.telegram.org/apps"
    resp = session.get(url, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()

    logger.debug("Scrape response status=%s url=%s (len=%s)",
                  resp.status_code, resp.url, len(resp.text))

    soup = BeautifulSoup(resp.text, features="html.parser")
    title_tag = soup.title
    title = title_tag.string if title_tag else ""

    if "configuration" in title:
        inputs = soup.find_all("span", {"class": "input-xlarge"})
        if len(inputs) >= 2:
            app_id = inputs[0].string.strip()
            api_hash = inputs[1].string.strip()
            return True, {"app_id": app_id, "api_hash": api_hash}
        logger.warning("Found configuration page but couldn't extract app_id/api_hash")
        return False, {"error": "Could not extract credentials from page"}

    form = soup.find("form")
    if form:
        inputs = form.find_all("input")
        logger.debug("Form action=%s, inputs: %s",
                     form.get("action"),
                     [(i.get("name"), i.get("value", "")) for i in inputs])

    tg_hash_input = soup.find("input", {"name": "hash"})
    if tg_hash_input:
        tg_hash = tg_hash_input.get("value")
        logger.debug("Found tg_hash=%s", tg_hash)
        return False, {"tg_app_hash": tg_hash}

    logger.error("Unexpected page (url=%s, title=%s). First 500 chars: %s",
                  resp.url, title, resp.text[:500])
    return False, {"error": f"Unexpected page: {title}"}


def _parse_error_from_html(html):
    soup = BeautifulSoup(html, features="html.parser")
    for tag in soup.find_all(["div", "span", "p", "li"]):
        cls = " ".join(tag.get("class", []))
        text = tag.get_text(strip=True)
        if text and ("error" in cls.lower() or "alert" in cls.lower() or "danger" in cls.lower()):
            return text[:300]
    for tag in soup.find_all(["div", "span", "p"]):
        text = tag.get_text(strip=True)
        if text and any(w in text.lower() for w in ["error", "invalid", "already", "taken"]):
            if len(text) < 300:
                return text
    return "(no error text found)"


def create_new_tg_app(session, tg_hash):
    ts = int(time.time())
    rand_suffix = ts % 1000000

    shortname = f"app{rand_suffix}"
    data = {
        "hash": tg_hash,
        "app_title": f"App {ts}",
        "app_shortname": shortname,
        "app_url": "",
        "app_platform": "desktop",
    }
    resp = session.post(
        "https://my.telegram.org/apps",
        data=data,
        headers={"Referer": "https://my.telegram.org/apps"},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()

    logger.debug("Create response status=%s url=%s len=%s",
                  resp.status_code, resp.url, len(resp.text))

    if resp.text.strip() == "true":
        time.sleep(1)
        return True

    soup = BeautifulSoup(resp.text, features="html.parser")
    title_tag = soup.title
    page_title = title_tag.string if title_tag else ""

    if "configuration" in page_title:
        time.sleep(1)
        return True

    err = _parse_error_from_html(resp.text)
    logger.warning("Form inputs after POST: %s",
                    [(i.get("name"), i.get("value", ""))
                     for i in soup.find_all("input")])
    logger.error("App creation failed. Page title=%s error=%s",
                  page_title, err)

    return False
