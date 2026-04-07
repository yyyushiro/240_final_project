import asyncio
import getpass
import json
import os
from playwright.async_api import Page, async_playwright, expect

# True = visible browser, you log in by hand, then press Enter in the terminal (no prompts).
loginManually = False


async def prompt_credentials() -> tuple[str, str]:
    """Ask for NetID and password in the terminal (password is hidden)."""
    user = (await asyncio.to_thread(input, "NetID / username: ")).strip()
    pw = (await asyncio.to_thread(getpass.getpass, "Password: ")).strip()
    return user, pw


async def main():
    username = ""
    password = ""
    if not loginManually:
        username, password = await prompt_credentials()
        if not username or not password:
            print("Username and password cannot be empty.")
            return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        if loginManually:
            await page.goto("https://onecardweb.richmond.edu/login/ldap.php")
            print("Log in manually in the browser, then press Enter here to continue...")
            await asyncio.to_thread(input)
        elif not await login(page, username, password):
            print("Login did not succeed; stopping.")
            await browser.close()
            return

        await openHistory(page)
        
        balances = await getBalance(page)
        
        timeline = await getTimeline(page)
        
        await browser.close()
        
    path = os.path.join(os.path.dirname(__file__), "rawHistory.json")
        
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "balances" : balances,
                "timelineHeader" : timeline.header,
                "timelineData": timeline.data
            },
            f,
            indent=2
        )

async def login(page: Page, username: str, password: str) -> bool:
    """Open the One Card Web and log in using the given username and password.

    Args:
        page (Page): the current page object.
        USERNAME (string): the given username.
        PASSWORD (string): the given password.

    Returns:
        True if the page does not show a login failure message.
    """
    # Go to the login page.
    await page.goto("https://onecardweb.richmond.edu/login/ldap.php")

    # Enter username and password
    print("Enter username and password...")
    await page.fill('input[name="user"]', username)
    await page.fill('input[name="pass"]', password)

    # Click the login button.
    print("Click the login button...")
    await page.click('input[type="submit"]')
    await page.wait_for_load_state("networkidle")
    print("Login flow finished.")
    
    # print meta information.
    print("Current URL:", page.url)
    print("Page title:", await page.title())

    # Login failure message appears on the same page when auth fails.
    login_failed = await page.locator("text=Login failed").count() > 0
    if login_failed:
        error_text = await page.locator("body").inner_text()
        print("Detected login failure on page.")
        print("Hint: verify credentials (no stray spaces).")
        if username in error_text:
            print("Server received this username:", username)
        return False
    print("No 'Login failed' message detected.")
    return True
     
async def openHistory(page: Page):
    """Set the date range and open the history.

    Args:
        page (Page): the current page object.
    """

    await page.locator("a", has_text="ULTD SVC").click()

    # Wait until Spending History form is actually ready (avoids racing the first open).
    await page.wait_for_selector(
        'select[name="FromMonth"]', state="visible", timeout=60_000
    )

    await page.locator('select[name="FromMonth"]').select_option("01")
    await page.locator('select[name="FromDay"]').select_option("12")
    await page.locator('select[name="FromYear"]').select_option("2026")
    await page.locator('select[name="ToMonth"]').select_option("06")
    await page.locator('select[name="ToDay"]').select_option("1")
    await page.locator('select[name="ToYear"]').select_option("2026")

    # Some sites update other controls after the last select change; brief settle time.
    await asyncio.sleep(0.5)

    btn = page.locator('input[value="View History"]')
    await btn.scroll_into_view_if_needed()
    await expect(btn).to_be_visible(timeout=30_000)
    await expect(btn).to_be_enabled(timeout=60_000)

    await btn.click()

    # Do not continue until the same table getBalance() waits on appears.
    await page.wait_for_selector(
        'table.fieldlist tbody tr', state="attached", timeout=60_000
    )
    print("Opened the spending history page")
        
async def getBalance(page) -> list[list[str]]:
    """Get the balance and return the beginning balance and the ending balance. 

    Args:
        page (Page): the current page object.
    """
    # Get the beginning balance and ending balance.
    balanceRows = page.locator('table[class="fieldlist"] tbody tr')
    await balanceRows.nth(0).wait_for(state='attached')
    balanceTable = []
    
    # Extract the texts from each row.
    for i in range(await balanceRows.count()):
        cells = balanceRows.nth(i).locator('td')
        
        numCells = await cells.count()
        if numCells == 0:
            continue
        texts = []
        # Extract the text from each cell.
        for j in range(numCells):
            texts.append((await cells.nth(j).inner_text()).strip())
        balanceTable.append(texts)
        
    print(balanceTable)
    return balanceTable
    
async def getTimeline(page) -> Timeline:
    """get the actual timeline of dining dollar usage.

    Args:
        page (Page): the current page object.
    """
    
    # Get the basic information about the timeline table.
    historyRows = page.locator('table[aria-live="polite"] tbody tr')
    await historyRows.nth(0).wait_for(state='attached')
    numRows = await historyRows.count()
    numCols = await historyRows.nth(0).locator('th').count()
    
    historyHeader = [] # the header of the history.
    historyData = [] # the raw data except for the header.
    
    # get the header.
    for i in range(numCols):
        historyHeader.append((await historyRows.nth(0).locator('th').nth(i).inner_text()).strip())

    # get the raw data line by line.
    for r in range(1, numRows):
        curRowTexts = []
        for c in range(numCols):
            curRowTexts.append((await historyRows.nth(r).locator('td').nth(c).inner_text()).strip())
        historyData.append(curRowTexts)
        
    print(historyHeader)
    print(historyData)
    
    return Timeline(historyHeader, historyData)

class Timeline:
    """
    The class for containing header and actual data of the timeline.
    """
    header: list[str]
    data: list[list[str]]
    
    def __init__(self, header, data) -> None:
        self.header = header
        self.data = data

if __name__ == "__main__":
    asyncio.run(main())
    
    
