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
    print("BOT_TOKEN and ADMIN_ID not set.")
    print()
    print("Set these environment variables in Dockage dashboard,")
    print("then restart the container:")
    print()
    print("  BOT_TOKEN = your bot token from @BotFather")
    print("  ADMIN_ID  = your Telegram user ID")
    print("=" * 50)
    sys.exit(0)


if __name__ == "__main__":
    main()
