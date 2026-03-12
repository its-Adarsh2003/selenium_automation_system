import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import ChromiumOptions


BROWSERSTACK_USER = os.getenv("BROWSERSTACK_USERNAME")
BROWSERSTACK_KEY = os.getenv("BROWSERSTACK_ACCESS_KEY")

BS_HUB_URL = "https://hub-cloud.browserstack.com/wd/hub"


def get_local_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    return driver


def get_bs_driver(capabilities: dict):
    """
    Create a Remote WebDriver session on BrowserStack.
    Requires BROWSERSTACK_USERNAME and BROWSERSTACK_ACCESS_KEY in env.
    """
    if not BROWSERSTACK_USER or not BROWSERSTACK_KEY:
        raise RuntimeError("Set BROWSERSTACK_USERNAME and BROWSERSTACK_ACCESS_KEY env vars first")

    caps = {
        "browserstack.user": BROWSERSTACK_USER,
        "browserstack.key": BROWSERSTACK_KEY,
        "project": "El Pais Opinion Scraper",
        "build": "Round 2 Assignment",
        "name": capabilities.get("name", "ElPais Opinion Test"),
    }
    caps.update(capabilities)

    options = ChromiumOptions()
    for k, v in caps.items():
        options.set_capability(k, v)

    driver = webdriver.Remote(
        command_executor=BS_HUB_URL,
        options=options,
    )
    return driver
