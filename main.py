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

    if not sys.stdin.isatty():
        print("=" * 50)
        print("First Run Setup")
        print("=" * 50)
        print()
        print("No config found. To set up interactively, run:")
        print("  docker compose run --rm bot")
        print()
        print("Or create a .env file with:")
        print("  BOT_TOKEN=your_token")
        print("  ADMIN_ID=your_user_id")
        print("=" * 50)
        sys.exit(1)

    first_run_setup()
    run_bot()


if __name__ == "__main__":
    main()
