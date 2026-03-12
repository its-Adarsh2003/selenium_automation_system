import os
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils.driver_setup import get_bs_driver
from pages.home_page import HomePage
from pages.opinion_page import OpinionPage

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s %(message)s",
)
logger = logging.getLogger(__name__)


CAPABILITIES = [
    {
        "browserName": "Chrome",
        "browserVersion": "latest",
        "os": "Windows",
        "osVersion": "11",
        "name": "Chrome Windows 11",
    },
    {
        "browserName": "Edge",
        "browserVersion": "latest",
        "os": "Windows",
        "osVersion": "10",
        "name": "Edge Windows 10",
    },
    {
        "browserName": "Safari",
        "browserVersion": "latest",
        "os": "OS X",
        "osVersion": "Sonoma",
        "name": "Safari macOS Sonoma",
    },
    {
        "browserName": "Chrome",
        "device": "Samsung Galaxy S23",
        "realMobile": "true",
        "osVersion": "13.0",
        "name": "Chrome Android S23",
    },
    {
        "browserName": "Safari",
        "device": "iPhone 15",
        "realMobile": "true",
        "osVersion": "17",
        "name": "Safari iPhone 15",
    },
]


def run_smoke_on_bs(cap: dict) -> str:
    driver = None
    try:
        logger.info("Starting session: %s", cap.get("name"))
        driver = get_bs_driver(cap)

        home = HomePage(driver)
        opinion = OpinionPage(driver)

        home.open()
        home.accept_cookies()
        home.go_to_opinion()

        time.sleep(3)

        logger.info("Completed session: %s", cap.get("name"))
        return f"OK: {cap.get('name')}"
    except Exception as e:
        logger.error("Failed session %s: %s", cap.get("name"), e)
        return f"FAIL: {cap.get('name')} -> {e}"
    finally:
        if driver:
            driver.quit()


def run_parallel_on_browserstack():
    start = time.time()
    results = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(run_smoke_on_bs, cap) for cap in CAPABILITIES]
        for fut in as_completed(futures):
            results.append(fut.result())

    elapsed = time.time() - start
    logger.info("All BrowserStack sessions done in %.2f seconds", elapsed)
    for r in results:
        logger.info("Result: %s", r)


if __name__ == "__main__":
    if not os.getenv("BROWSERSTACK_USERNAME") or not os.getenv("BROWSERSTACK_ACCESS_KEY"):
        raise RuntimeError("Set BROWSERSTACK_USERNAME and BROWSERSTACK_ACCESS_KEY before running.")

    run_parallel_on_browserstack()
