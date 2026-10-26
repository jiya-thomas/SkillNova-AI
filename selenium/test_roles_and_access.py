"""Login routing, logout, and unauthenticated access coverage."""

import pytest
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from helpers import registered_and_logged_in


@pytest.mark.parametrize(
    "role, dashboard_path",
    [("jobseeker", "/jobseeker/"), ("recruiter", "/recruiter/"), ("admin", "/skillnova/")],
)
def test_role_login_routes_to_its_dashboard(driver, base_url, role, dashboard_path):
    registered_and_logged_in(driver, base_url, role, dashboard_path)

    assert dashboard_path in driver.current_url


@pytest.mark.parametrize(
    "path",
    ["/jobseeker/", "/recruiter/", "/recruiter/post-job/", "/skillnova/"],
)
def test_private_routes_redirect_anonymous_users_to_login(driver, base_url, path):
    driver.get(f"{base_url}{path}")

    WebDriverWait(driver, 5).until(EC.url_contains("/login/"))
    assert "Please login first." in driver.page_source


def test_logout_ends_the_browser_session(driver, base_url):
    registered_and_logged_in(driver, base_url, "jobseeker", "/jobseeker/")
    driver.get(f"{base_url}/logout/")

    WebDriverWait(driver, 5).until(EC.url_contains("/login/"))
    driver.get(f"{base_url}/jobseeker/")
    WebDriverWait(driver, 5).until(EC.url_contains("/login/"))
