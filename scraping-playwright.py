import asyncio
import pandas as pd
from urllib.parse import urljoin
from playwright.async_api import async_playwright

BASE_URL = "https://algomap.io"
OUTPUT_FILE = "algomap_problems.xlsx"

async def force_table_visible(page, level):
    """Multiple strategies to reveal the problem table"""
    # Try clicking the section again
    section = await level.query_selector('.roadmap-section')
    await section.click()
    await page.wait_for_timeout(1500)
    
    # Forcefully make tables visible via JavaScript
    await page.evaluate("""(level) => {
        // Remove any overlays
        const overlays = level.closest('.roadmap').querySelectorAll('.modal, .popup, .overlay');
        overlays.forEach(el => el.remove());
        
        // Make all tables visible
        const tables = level.getElementsByTagName('table');
        for (let table of tables) {
            table.style.display = 'table';
            table.style.visibility = 'visible';
            table.style.opacity = '1';
        }
        
        // Expand container
        level.style.height = 'auto';
        level.style.overflow = 'visible';
    }""", level)

async def extract_problems():
    problems = []
    async with async_playwright() as p:
        # Configure browser to look more human-like
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--start-maximized'
            ]
        )
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            locale='en-US'
        )
        page = await context.new_page()
        page.set_default_timeout(60000)

        # Block unnecessary resources
        await page.route('**/*.{png,jpg,jpeg,svg,gif,woff2,css}', lambda route: route.abort())
        
        print("Navigating to Algomap...")
        await page.goto(BASE_URL, wait_until="networkidle")
        
        # Remove any popups/overlays
        await page.evaluate("""() => {
            document.querySelectorAll('.modal, .popup, .overlay, #close-ad-btn, #ad-modal, #ad-popup').forEach(el => el.remove());
            let closeBtn = document.getElementById('close-ad-btn');
            if (closeBtn) closeBtn.click();
        }""")

        # Wait for roadmap to fully load
        print("Waiting for roadmap to load...")
        await page.wait_for_selector('.roadmap-level', state='visible', timeout=15000)
        
        # Process each category
        levels = await page.query_selector_all('.roadmap-level')
        print(f"\nFound {len(levels)} categories to process")
        
        for i, level in enumerate(levels, 1):
            try:
                # Get category name
                section = await level.query_selector('.roadmap-section')
                if not section:
                    print(f"Skipping level {i} - no section found")
                    continue
                
                category = (await section.inner_text()).strip()
                print(f"\n[{i}/{len(levels)}] Processing: {category}")
                
                # Open category - with multiple attempts if needed
                for attempt in range(3):
                    await section.click()
                    await page.wait_for_timeout(2000)  # Crucial wait for animation
                    
                    # Force the table to appear
                    await force_table_visible(page, level)
                    
                    # Check if table exists
                    table = await level.query_selector('table')
                    if not table:
                        # Try to find the last table on the page (likely the modal)
                        tables = await page.query_selector_all('table')
                        if tables:
                            table = tables[-1]
                    if table:
                        break
                    print(f"Attempt {attempt + 1}: Table not found, retrying...")
                
                if not table:
                    print(f"⚠️ Could not load table for {category}")
                    continue
                
                # Extract problems
                rows = await table.query_selector_all('tbody tr')
                print(f"Found {len(rows)} problems")
                
                for row in rows:
                    try:
                        cols = await row.query_selector_all('td')
                        if len(cols) >= 4:
                            problem = (await cols[0].inner_text()).strip()
                            solution_elem = await cols[0].query_selector('a')
                            problem_elem = await cols[2].query_selector('a.problem-name')
                            
                            if solution_elem and problem_elem:
                                problems.append({
                                    'Category': category,
                                    'Problem': problem,
                                    'Problem Link': await problem_elem.get_attribute('href'),
                                    'Solution Link': urljoin(BASE_URL, await solution_elem.get_attribute('href'))
                                })
                    except Exception as e:
                        print(f"Error parsing row: {str(e)}")
                        continue
                
                # Close category
                await section.click()
                await page.wait_for_timeout(1000)
                
            except Exception as e:
                print(f"⛔ Error processing {category}: {str(e)}")
                continue

        await browser.close()
    
    return problems

def main():
    print("Starting Algomap scraper...")
    problems = asyncio.run(extract_problems())
    
    if problems:
        df = pd.DataFrame(problems)
        df.to_excel(OUTPUT_FILE, index=False)
        print(f"\n✅ Success! Saved {len(df)} problems to {OUTPUT_FILE}")
        print("Sample problems:")
        print(df.head())
    else:
        print("\n❌ No problems were scraped.")

if __name__ == '__main__':
    print("Check browser and press Enter to continue...")
    input()
    main()