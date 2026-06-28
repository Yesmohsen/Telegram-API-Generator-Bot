import sys
import time

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

    from web_setup import run_setup_server
    import threading

    t = threading.Thread(target=run_setup_server, daemon=True)
    t.start()

    while not config_exists():
        time.sleep(1)

    print("Config saved. Starting bot...")
    time.sleep(0.5)
    run_bot()


if __name__ == "__main__":
    main()
