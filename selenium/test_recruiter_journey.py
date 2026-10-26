"""Smoke coverage for recruiter pages after a real browser login."""

import pytest
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from helpers import registered_and_logged_in


@pytest.mark.parametrize(
    "path",
    [
        "/recruiter/candidate/",
        "/recruiter/post-job/",
        "/recruiter/job-list/",
        "/recruiter/screening/",
        "/recruiter/applications/",
        "/recruiter/interviews/",
        "/recruiter/interviews/schedule/",
    ],
)
def test_recruiter_pages_load_for_authenticated_user(driver, base_url, path):
    registered_and_logged_in(driver, base_url, "recruiter", "/recruiter/")
    driver.get(f"{base_url}{path}")

    print("Requested URL:", f"{base_url}{path}")
    print("Current URL:", driver.current_url)
    print("Page title:", driver.title)

    WebDriverWait(driver, 5).until(EC.url_contains(path))
    assert "Skill Nova AI" in driver.title
