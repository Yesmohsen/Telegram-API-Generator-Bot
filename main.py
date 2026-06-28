import sys

from bot import run_bot
from config import config_exists, first_run_setup, from_env


def main():
    env_config = from_env()
    if env_config:
        run_bot()
        return

    if config_exists():
        run_bot()
        return

    if sys.stdin.isatty():
        first_run_setup()
        run_bot()
    else:
        print("ERROR: BOT_TOKEN and ADMIN_ID environment variables not set.")
        print("Create a .env file:")
        print("  BOT_TOKEN=your_token")
        print("  ADMIN_ID=your_user_id")
        sys.exit(1)


if __name__ == "__main__":
    main()
