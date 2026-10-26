import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

@pytest.fixture(scope="session")
def base_url(live_server):
    return live_server.url

@pytest.fixture
def driver():
    options = Options()
    # Selenium Manager selects the locally available Chrome-compatible browser.
    # Set SELENIUM_BROWSER_BINARY when a particular browser binary is required.
    import os

    browser_binary = os.getenv("SELENIUM_BROWSER_BINARY")
    if browser_binary:
        options.binary_location = browser_binary
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,900")
    browser = webdriver.Chrome(options=options)

    yield browser
    browser.quit()
