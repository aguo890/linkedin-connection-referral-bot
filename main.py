# main.py

import os
import asyncio
from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page, expect

# --- CONFIGURATION ---
# Load environment variables (your email and password) from the .env file
load_dotenv()
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")
COMPANY_TO_SEARCH = "Amazon"


# < Login Functions
async def is_logged_in(page: Page) -> bool:
    """
    Checks if the user is logged into LinkedIn using the current page state.

    Args:
        page (Page): The Playwright page object to check.

    Returns:
        bool: True if logged in, False otherwise.
    """
    # Most reliable check: If we are on the feed page, we are logged in.
    if "/feed" in page.url:
        print("INFO: Currently on the feed page. User is logged in.")
        return True

    # Check for elements that ONLY appear when you are LOGGED OUT.
    # We use a short timeout because we don't want to wait long if they don't exist.
    try:
        # Check for a prominent "Sign in" button or link
        sign_in_button = page.get_by_role("button", name="Sign in", exact=True)
        # Check for the "Join now" link
        join_now_link = page.get_by_role("link", name="Join now")

        # If either is visible, we are definitely logged out.
        if await sign_in_button.is_visible(
            timeout=2000
        ) or await join_now_link.is_visible(timeout=2000):
            print("INFO: Found 'Sign in' or 'Join now' elements. User is logged out.")
            return False
    except Exception:
        # An exception here (like a timeout) means the elements weren't found,
        # which is a strong indicator that the user IS logged in.
        pass

    # Fallback: If we can't find logout indicators, assume the user is logged in.
    print("INFO: Did not find explicit login prompts, assuming user is logged in.")
    return True


async def login(page: Page, email: str, password: str) -> bool:
    """
    Logs into LinkedIn using the provided credentials. This version uses highly stable ID locators.
    """
    print("INFO: Navigating to LinkedIn login page...")
    await page.goto("https://www.linkedin.com/login")

    try:
        # --- THE FIX ---
        # Instead of using the label, we now target the input field directly by its ID.
        # The '#' symbol means "ID". So '#username' means "find the element with id='username'".
        print("INFO: Locating the email field using its ID...")
        email_field = page.locator("#username")

        # We still wait for it to be ready, just in case.
        await email_field.wait_for(timeout=10000)

        print(f"INFO: Filling out email: {email}")
        await email_field.fill(email)

        # For the password field, we can use its `aria-label` which is stable.
        print("INFO: Locating and filling password field...")
        password_field = page.get_by_label("Password")
        await password_field.fill(password)

        # --- END OF FIX ---

        print("INFO: Clicking 'Sign in'...")
        await page.get_by_role("button", name="Sign in", exact=True).click()

        # Wait for the main feed to load to confirm success
        print("INFO: Waiting for login confirmation...")
        messaging_link = page.get_by_role("link", name="Messaging")
        await expect(messaging_link).to_be_visible(timeout=60000)

        print("SUCCESS: Login successful!")
        return True


    except Exception as e:
        print(f"ERROR: Login attempt failed.")
        print("Check the screenshot and error message below to debug.")
        print(f"DEBUG: The specific error was: {e}")

        screenshot_path = "login_error.png"
        await page.screenshot(path=screenshot_path)
        print(f"A screenshot has been saved to '{screenshot_path}'")

        await page.pause()
        return False


#------SEARCHING FOR THE COMPANY-------
async def company_search(page: Page, COMPANY_TO_SEARCH: str):

    print("Searching for People to connect ")
    await page.get_by_role("combobox", name="Search", exact=True).click()
    
    print(f"INFO: Filling out company: {COMPANY_TO_SEARCH}")
    await page.get_by_role("combobox", name="Search").fill(COMPANY_TO_SEARCH)
    await page.keyboard.press("Enter")
    
    print("Found Company...")
    await page.wait_for_timeout(3000) 

async def people_message(page: Page, person):
    name1= "Message "+person
    await page.get_by_role("button", name=name1, exact = True).click()





async def people_search(page: Page):

    print("Searching for people.....")

    print("Demonstration finished. Keeping browser open...")

    all_filters_button = page.get_by_role("button", name="All filters")
    await expect(all_filters_button).to_be_visible(timeout=3000)

    await all_filters_button.click()
    await page.get_by_role("button", name="1st", exact=True).click()

    await page.get_by_role("button", name="Apply current filters to show results", exact=True).click()

    print ("applying People Filters.....")
    await page.wait_for_timeout(3000) 

    results = []
    # The presence indicator is inside the profile card div. Let's get all such cards:
    profile_cards = await page.locator('div.presence-entity--size-3').all()

    for card in profile_cards:
        try:
            # Get the name from the alt text of the profile image
            img = card.locator('img.presence-entity__image')
            name = await img.get_attribute('alt')
            
            # Optionally, you can check for status span text if you want to filter further
            span = card.locator('span.visually-hidden')
            if await span.inner_text() and "Status" in await span.inner_text():
                results.append(name)
        except Exception:
            continue

    print("Profiles with Status found....")
    print(results)

    return results  # List of (name, link) tuples

    

async def message_person(people_with_status, page: Page):
    for name, link in people_with_status:
        print(f"Ready to process: {name}")
        # (Do something with link)
    #await page.get_by_role("button", name="Message Jay Zhu").click()


# --- DEMONSTRATION OF HOW TO USE THE FUNCTIONS ---
async def main_demonstration():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        page = await browser.new_page()

        # Go to a LinkedIn page to see our status
        await page.goto("https://www.linkedin.com/feed/")

        if not await is_logged_in(page):
            print("User is not logged in. Attempting login...")
            await login(page, LINKEDIN_EMAIL, LINKEDIN_PASSWORD)
        else:
            print("User is already logged in. No action needed.")
        await company_search(page, COMPANY_TO_SEARCH)
        print ("Company search completed")

        person_found = await people_search(page)   
        
        for person in person_found:
            await people_message(page, person)
            print("Demonstration finished. Keeping browser open...")
            await page.pause()
            await browser.close()

        print("Demonstration finished. Keeping browser open...")
        await page.pause()
        await browser.close()   

        print("Demonstration finished. Keeping browser open...")
        await page.pause()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main_demonstration())
