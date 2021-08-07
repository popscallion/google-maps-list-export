import re
import time

from selenium.webdriver import Firefox
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options


def main():
    print("Starting driver")
    options = Options()
    options.headless = False

    driver = Firefox(options=options)
    driver.implicitly_wait(5)

    print("Going to Maps")
    driver.get("")

    driver.find_elements_by_tag_name("button")[1].click()
    time.sleep(1)

    print("Loading list items")
    previous_page = None
    scrollbox = driver.find_element_by_class_name("section-scrollbox")
    while previous_page is None or previous_page != driver.page_source:
        previous_page = driver.page_source
        scrollbox.send_keys(Keys.PAGE_DOWN * 5)
        time.sleep(1)

    print("Scraping entries")
    entries = []
    item_count = len(driver.find_elements_by_xpath("//div[contains(@class,'section-scrollbox')]/div")) // 2
    for i in range(item_count):
        driver.find_elements_by_xpath("//div[contains(@class,'section-scrollbox')]/div")[i * 2].click()

        time.sleep(1)
        url = driver.current_url

        coords = re.findall(r"(-?\d+\.\d+)!4d(-?\d+\.\d+)", url)[0]
        name = driver.find_element_by_tag_name("h1").text
        print(f"Found {name} at {', '.join(coords)}")

        driver.find_element_by_class_name("omnibox-pane-container").click()
        time.sleep(1)

        entries.append({"name": name, "coords": coords})

    driver.close()


if __name__ == '__main__':
    main()
