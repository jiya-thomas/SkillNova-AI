"""Selenium tests for login error handling."""

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait


def test_invalid_login_displays_feedback(driver, base_url):
    driver.get(f"{base_url}/login/")

    driver.find_element(By.NAME, "email").send_keys("missing@example.test")
    driver.find_element(By.NAME, "password").send_keys("not-the-password")
    Select(driver.find_element(By.NAME, "role")).select_by_value("jobseeker")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit'], button").click()

    feedback = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".toast-body"))
    )
    assert feedback.text == "Invalid User Credentials."
