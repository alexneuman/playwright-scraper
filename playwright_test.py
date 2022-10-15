

from playwright.sync_api import Playwright, sync_playwright, expect
def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    # Open new page
    page = context.new_page()
    page.goto('https://www.drudgereport.com/', wait_until='load')
    bob = page.query_selector_all('//b')
    for b in bob:
        n = b.query_selector('//a')
        print(n)

    context.close()
    browser.close()
with sync_playwright() as playwright:
    run(playwright)
