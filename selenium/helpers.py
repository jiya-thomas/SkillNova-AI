"""Reusable browser actions for end-to-end tests."""

from uuid import uuid4

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait


WAIT_SECONDS = 5


def register_user(driver, base_url, role):
    """Create a unique application user through the public registration form."""
    email = f"selenium-{role}-{uuid4().hex[:10]}@example.test"
    password = "SeleniumPass123!"

    driver.get(f"{base_url}/register/")
    driver.find_element(By.NAME, "name").send_keys(f"Selenium {role.title()}")
    driver.find_element(By.NAME, "email").send_keys(email)
    driver.find_element(By.NAME, "phone").send_keys("9876543210")
    Select(driver.find_element(By.NAME, "role")).select_by_value(role)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.NAME, "confirm_password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "form button").click()
    WebDriverWait(driver, WAIT_SECONDS).until(EC.url_contains("/login/"))
    return email, password


def login_user(driver, base_url, email, password, role, expected_path):
    """Log in through the UI and wait for the requested role landing page."""
    driver.get(f"{base_url}/login/")
    driver.find_element(By.NAME, "email").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(password)
    Select(driver.find_element(By.NAME, "role")).select_by_value(role)
    driver.find_element(By.CSS_SELECTOR, "form button").click()
    WebDriverWait(driver, WAIT_SECONDS).until(EC.url_contains(expected_path))


def registered_and_logged_in(driver, base_url, role, expected_path):
    email, password = register_user(driver, base_url, role)
    login_user(driver, base_url, email, password, role, expected_path)
    return email
