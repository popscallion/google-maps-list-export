import argparse
import json
import re
import time

import simplekml
from selenium.common.exceptions import ElementNotInteractableException
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

    try:
        previous_page = None
        scrollbox = driver.find_element_by_class_name("section-scrollbox")
        while previous_page is None or previous_page != driver.page_source:
            previous_page = driver.page_source
            scrollbox.send_keys(Keys.PAGE_DOWN * 5)
            time.sleep(1)
    except ElementNotInteractableException:
        pass

    return list_name


def scrape_items(driver):
    print("Scraping entries")

    item_count = len(driver.find_elements_by_xpath("//div[contains(@class,'section-scrollbox')]/div")) // 2
    print(f"Found {item_count} items")

    entries = []
    for i in range(item_count):
        driver.find_elements_by_xpath("//div[contains(@class,'section-scrollbox')]/div")[i * 2].click()

        time.sleep(3)
        url = driver.current_url

        lat, lon = re.findall(r"(-?\d+\.\d+)!4d(-?\d+\.\d+)", url)[0]
        name = driver.find_element_by_tag_name("h1").text
        print(f"({i + 1}/{item_count}) Location '{name}' at {lat},{lon}")

        driver.find_element_by_class_name("omnibox-pane-container").click()
        time.sleep(1)

        entries.append({"name": name, "lat": lat, "lon": lon})

    return entries


def slugify(word):
    return "".join(c for c in word.lower().replace(" ", "-") if c.isalnum() or c == "-")


def save(entries, list_name, format):
    filename = f"{slugify(list_name)}.{format}"

    if format == "json":
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False)

    elif format == "kml":
        kml = simplekml.Kml()
        for entry in entries:
            kml.newpoint(name=entry["name"], coords=[(entry["lon"], entry["lat"])])
        kml.save(filename)

    else:
        raise ValueError(f"Format {format} not supported.")

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
    parser.add_argument("-f", "--format", choices=["json", "kml"], nargs="?", default="json",
                        help="Specify the export format. Default: json")
    parser.add_argument("--show-browser", action="store_true", help="Don't start the browser in headless mode.")

    args = parser.parse_args()

    main(args.list_url, not args.show_browser, args.format)
