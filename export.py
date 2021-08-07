import argparse
import json
import re
import time

from selenium.webdriver import Firefox
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options


def initialize(headless):
    print("Starting driver")
    options = Options()
    options.headless = headless

    driver = Firefox(options=options)
    driver.implicitly_wait(5)

    return driver


def load_list(driver, list_url):
    print("Going to Maps")
    driver.get(list_url)

    driver.find_elements_by_tag_name("button")[1].click()
    time.sleep(1)

    list_name = driver.find_element_by_tag_name("h1").text

    print(f"Loading items of list '{list_name}'")
    previous_page = None
    scrollbox = driver.find_element_by_class_name("section-scrollbox")
    while previous_page is None or previous_page != driver.page_source:
        previous_page = driver.page_source
        scrollbox.send_keys(Keys.PAGE_DOWN * 5)
        time.sleep(1)

    return list_name


def scrape_items(driver):
    print("Scraping entries")

    item_count = len(driver.find_elements_by_xpath("//div[contains(@class,'section-scrollbox')]/div")) // 2

    entries = []
    for i in range(item_count):
        driver.find_elements_by_xpath("//div[contains(@class,'section-scrollbox')]/div")[i * 2].click()

        time.sleep(1)
        url = driver.current_url

        coords = re.findall(r"(-?\d+\.\d+)!4d(-?\d+\.\d+)", url)[0]
        name = driver.find_element_by_tag_name("h1").text
        print(f"Item '{name}' at {','.join(coords)}")

        driver.find_element_by_class_name("omnibox-pane-container").click()
        time.sleep(1)

        entries.append({"name": name, "coords": coords})

    return entries


def slugify(word):
    return "".join(c for c in word.lower().replace(" ", "-") if c.isalnum())


def save(entries, list_name, format):
    if format == "json":
        filename = f"{slugify(list_name)}.json"
        with open(filename, "w") as f:
            json.dump(entries, f)

        print(f"Exported as '{filename}'")


def main(list_url, headless, format):
    driver = initialize(headless)

    list_name = load_list(driver, list_url)

    entries = scrape_items(driver)

    save(entries, list_name, format)

    driver.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Export a Google Maps list (because Google doesn't let you).")

    parser.add_argument("list_url", help="The share URL of the list.")
    parser.add_argument("-f", "--format", choices=["json"], nargs="?", default="json",
                        help="Specify the export format. Default: json")
    parser.add_argument("--show-browser", action="store_true", help="Don't start the browser in headless mode.")

    args = parser.parse_args()

    main(args.list_url, not args.show_browser, args.format)
