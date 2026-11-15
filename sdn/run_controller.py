import logging

from os_ken.base.app_manager import AppManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)

if __name__ == "__main__":
    AppManager.run_apps(["sdn.controller"])
