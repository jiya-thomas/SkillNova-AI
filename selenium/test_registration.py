"""Registration validation and success-path browser coverage."""

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from helpers import register_user


def test_jobseeker_can_register(driver, base_url):
    email, _ = register_user(driver, base_url, "jobseeker")

    assert "Account Created Successfully." in driver.page_source
    assert email not in driver.page_source  # Registration redirects back to login.


def test_registration_rejects_mismatched_passwords(driver, base_url):
    driver.get(f"{base_url}/register/")

    driver.find_element(By.NAME, "name").send_keys("Mismatch User")
    driver.find_element(By.NAME, "email").send_keys("mismatch@example.test")
    driver.find_element(By.NAME, "phone").send_keys("9876543210")
    driver.find_element(By.NAME, "role").send_keys("Jobseeker")
    driver.find_element(By.NAME, "password").send_keys("one-password")

    confirm_password = driver.find_element(
        By.NAME, "confirm_password"
    )
    confirm_password.send_keys("another-password")

    # Verify client-side password validation
    is_invalid = driver.execute_script(
        "return arguments[0].validity.customError;",
        confirm_password
    )

    validation_message = driver.execute_script(
        "return arguments[0].validationMessage;",
        confirm_password
    )

    assert is_invalid is True
    assert "Passwords do not match" in validation_message