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

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()

        await login(page, USERNAME, PASSWORD)
        
        await openHistory(page)
        
        await getBalance(page)
        
        await getTimeline(page)
        
        input("Press Enter to close browser...")
        await browser.close()
        


async def login(page, username, password):
    """Open the One Card Web and log in using the given username and password.

    Args:
        page (Page): the current page object.
        USERNAME (string): the given username.
        PASSWORD (string): the given password.
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
        print("Hint: verify credentials and remove spaces/newlines in .env values.")
        if username in error_text:
            print("Server received this username:", username)
        return
    else:
        print("No 'Login failed' message detected.")
    
    
async def openHistory(page):
    """Set the date range and open the history.

    Args:
        page (Page): the current page object.
    """
    
    # Go to spending history page
    await page.locator("a", has_text="ULTD SVC").click()          
    
    # Set the beginning date.
    await page.locator('select[name="FromMonth"]').select_option("01")
    await page.locator('select[name="FromDay"]').select_option("12")
    await page.locator('select[name="FromYear"]').select_option("2026")
    
    # Set the ending date.
    await page.locator('select[name="ToMonth"]').select_option("06")
    await page.locator('select[name="ToDay"]').select_option("1")
    await page.locator('select[name="ToYear"]').select_option("2026")
    
    # Open the history.
    await page.locator('input[value="View History"]').click()
    print("Opened the spending history page")
        
async def getBalance(page):
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
    
async def getTimeline(page):
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

if __name__ == "__main__":
    asyncio.run(main())