import json
import os

CONFIG_FILE = "config.json"

ENV_BOT_TOKEN = "BOT_TOKEN"
ENV_ADMIN_ID = "ADMIN_ID"


def config_exists():
    return os.path.exists(CONFIG_FILE)


def from_env():
    token = os.environ.get(ENV_BOT_TOKEN)
    admin = os.environ.get(ENV_ADMIN_ID)
    if token and admin:
        return {"bot_token": token, "admin_id": int(admin)}
    return None


def load_config():
    env_config = from_env()
    if env_config:
        return env_config
    with open(CONFIG_FILE) as f:
        return json.load(f)


def save_config(bot_token, admin_id):
    with open(CONFIG_FILE, "w") as f:
        json.dump(
            {"bot_token": bot_token, "admin_id": int(admin_id)},
            f,
            indent=2,
        )


def first_run_setup():
    print("=" * 50)
    print("First Run Setup")
    print("=" * 50)
    bot_token = input("Enter your Telegram Bot Token (from @BotFather): ").strip()
    admin_id = input("Enter your Telegram User ID (admin): ").strip()
    save_config(bot_token, admin_id)
    print("Config saved to config.json")
    print("=" * 50)
