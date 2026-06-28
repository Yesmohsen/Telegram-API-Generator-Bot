from bot import run_bot
from config import config_exists, first_run_setup, from_env


def main():
    if not from_env() and not config_exists():
        first_run_setup()
    run_bot()


if __name__ == "__main__":
    main()
