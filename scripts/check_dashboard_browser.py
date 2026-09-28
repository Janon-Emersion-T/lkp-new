"""Authenticated, read-only dashboard checks against the running development server."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lkprofessionals.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.test import Client
from playwright.sync_api import sync_playwright

client = Client()
client.force_login(get_user_model().objects.filter(is_superuser=True, is_active=True).first())
session = client.cookies['sessionid'].value
output = ROOT / 'artifacts' / 'dashboard'
output.mkdir(parents=True, exist_ok=True)
try:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for width, height in [(1440, 1000), (390, 844)]:
            context = browser.new_context(viewport={'width': width, 'height': height})
            context.add_cookies([{'name': 'sessionid', 'value': session, 'domain': '127.0.0.1', 'path': '/'}])
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            for name, path in [('command-center', '/dashboard/'), ('leads', '/dashboard/leads/'), ('board', '/dashboard/project-tasks/board/'), ('reports', '/dashboard/reports/'), ('quotation-form', '/dashboard/quotations/new/'), ('roles', '/dashboard/access-roles/new/')]:
                response = page.goto('http://127.0.0.1:8118' + path, wait_until='networkidle')
                assert response.status == 200, (path, response.status)
                assert page.locator('h2.page-title').is_visible()
                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1'), f'Overflow: {path} at {width}'
                assert page.locator('.navbar-brand img').evaluate('(img) => img.complete && img.naturalWidth > 0')
                page.screenshot(path=str(output / f'{name}-{width}.png'), full_page=True)
            page.goto('http://127.0.0.1:8118/dashboard/', wait_until='networkidle')
            if width < 992:
                page.locator('.navbar-toggler').click()
            page.locator('summary').filter(has_text='CRM & Sales').click()
            page.locator('.dashboard-subnav a').filter(has_text='Leads').first.click()
            page.wait_for_url('**/dashboard/leads/')
            assert not errors, errors
            print(f'{width}px: six screens, logo, overflow and sidebar navigation passed')
            context.close()
        browser.close()
finally:
    Session.objects.filter(session_key=session).delete()
