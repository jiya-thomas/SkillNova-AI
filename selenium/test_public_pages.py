"""Browser-level smoke tests for publicly accessible Skill Nova pages."""

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def test_home_page_displays_primary_actions(driver, base_url):
    driver.get(base_url)

    assert driver.title == "Skill Nova AI"
    assert driver.find_element(By.LINK_TEXT, "Getting Started").is_displayed()
    assert driver.find_element(By.LINK_TEXT, "Login").is_displayed()


def test_getting_started_opens_registration_page(driver, base_url):
    driver.get(base_url)
    driver.find_element(By.LINK_TEXT, "Getting Started").click()

    WebDriverWait(driver, 5).until(EC.title_is("Skill Nova AI | Register"))
    assert driver.find_element(By.NAME, "name").is_displayed()
    assert driver.find_element(By.NAME, "email").is_displayed()
    assert driver.find_element(By.NAME, "role").is_displayed()


def test_login_page_shows_required_fields(driver, base_url):
    driver.get(f"{base_url}/login/")

    assert driver.title == "Skill Nova AI | Login"
    assert driver.find_element(By.NAME, "email").is_displayed()
    assert driver.find_element(By.NAME, "password").is_displayed()
    assert driver.find_element(By.NAME, "role").is_displayed()


def test_jobseeker_page_requires_authentication(driver, base_url):
    driver.get(f"{base_url}/jobseeker/")

    WebDriverWait(driver, 5).until(EC.url_contains("/login/"))
    assert "Please login first." in driver.page_source
