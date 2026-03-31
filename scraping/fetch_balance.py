import asyncio
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import os

load_dotenv()

USERNAME = os.environ.get("USERNAME", "").strip()
PASSWORD = os.environ.get("PASSWORD", "").strip()

async def main():
    if not USERNAME or not PASSWORD:
        print("USERNAME/PASSWORD is empty. Check scraping/.env")
        return

    print(f"Using USERNAME from .env: '{USERNAME}'")
    print(f"PASSWORD length from .env: {len(PASSWORD)}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Go to the login page.
        await page.goto("https://onecardweb.richmond.edu/login/ldap.php")

        # Enter username and password
        print("Enter username and password...")
        await page.fill('input[name="user"]', USERNAME)
        await page.fill('input[name="pass"]', PASSWORD)

        # Click the login button.
        print("Click the login button...")
        await page.click('input[type="submit"]')

        await page.wait_for_load_state("networkidle")
        print("Login flow finished.")
        print("Current URL:", page.url)
        print("Page title:", await page.title())

        # Login failure message appears on the same page when auth fails.
        login_failed = await page.locator("text=Login failed").count() > 0
        if login_failed:
            error_text = await page.locator("body").inner_text()
            print("Detected login failure on page.")
            print("Hint: verify credentials and remove spaces/newlines in .env values.")
            if USERNAME in error_text:
                print("Server received this username:", USERNAME)
        else:
            print("No 'Login failed' message detected.")
            
        # Go to spending history page
        await page.locator("a", has_text="ULTD SVC").click()          
        
        # Set the date range.
        await page.locator('select[name="FromMonth"]').select_option("01")
        await page.locator('select[name="FromDay"]').select_option("12")
        await page.locator('select[name="FromYear"]').select_option("2026")

        await page.locator('select[name="ToMonth"]').select_option("06")
        await page.locator('select[name="ToDay"]').select_option("1")
        await page.locator('select[name="ToYear"]').select_option("2026")
        
        # Get the history
        await page.locator('input[value="View History"]').click()
        
        input("Press Enter to close browser...")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())