"""Smoke coverage for jobseeker pages after a real browser login."""

import pytest
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from helpers import registered_and_logged_in


@pytest.mark.parametrize(
    "path",
    [
        "/jobseeker/profile/",
        "/jobseeker/skillgap/",
        "/jobseeker/roadmap/",
        "/jobseeker/ats-resume/",
        "/jobseeker/verify-skills/",
        "/jobseeker/skill-badge/",
        "/jobseeker/cover/",
        "/jobseeker/jobs/",
        "/jobseeker/jobs/applications/",
        "/jobseeker/jobs/invitations",
        "/jobseeker/interview/",
    ],
)
def test_jobseeker_pages_load_for_authenticated_user(driver, base_url, path):
    registered_and_logged_in(driver, base_url, "jobseeker", "/jobseeker/")
    driver.get(f"{base_url}{path}")

    WebDriverWait(driver, 5).until(EC.url_contains(path))
    assert "Skill Nova AI" in driver.title
