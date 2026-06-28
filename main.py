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
        return

    print("=" * 50)
    print("First Run Setup")
    print("=" * 50)
    print()
    print("No config found. To set up:")
    print("  1. Run interactively: docker compose up")
    print("  2. Or set env vars in your hosting dashboard:")
    print("     BOT_TOKEN = your bot token from @BotFather")
    print("     ADMIN_ID  = your Telegram user ID")
    print()
    print("Then restart the container.")
    print("=" * 50)
    sys.exit(1)


if __name__ == "__main__":
    main()
