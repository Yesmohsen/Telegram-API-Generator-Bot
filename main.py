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

    first_run_setup()
    run_bot()


if __name__ == "__main__":
    main()
