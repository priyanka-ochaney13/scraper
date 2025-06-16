import time
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import re

BASE_URL = "https://algomap.io"
OUTPUT_FILE = "algomap_roadmap_problems.xlsx"

def extract_problems():
    print("Launching browser and fetching roadmap page...")
    
    # Force specific ChromeDriver version that matches your Chrome
    driver = webdriver.Chrome(service=Service(
        ChromeDriverManager(version="114.0.5735.90").install()
    ))
    
    driver.get(BASE_URL)
    time.sleep(5)

    problems = []

    category_buttons = driver.find_elements(By.CSS_SELECTOR, '.roadmap-section')
    for idx, button in enumerate(category_buttons):
        onclick = button.get_attribute('onclick')
        match = re.search(r"openSectionModal\('([^']+)'\)", onclick)
        category_name = match.group(1) if match else f"Category {idx + 1}"
        print(f"Processing category: {category_name}")

        driver.execute_script("arguments[0].click();", button)
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        tables = soup.select('table')
        if not tables:
            print(f"No tables found for category: {category_name}")
            continue
        table = tables[-1]
        for row in table.select('tbody tr'):
            tds = row.find_all('td')
            if len(tds) >= 4:
                solution_elem = tds[0].find('a')
                leetcode_elem = tds[2].find('a', class_='problem-name')
                if solution_elem and leetcode_elem:
                    problem_name = solution_elem.get_text(strip=True)
                    solution_link = urljoin(BASE_URL, solution_elem['href'])
                    problem_link = leetcode_elem['href']
                    problems.append({
                        'Problem': problem_name,
                        'Problem Link': problem_link,
                        'Solution Link': solution_link,
                        'Category': category_name
                    })
    driver.quit()
    print(f"Found {len(problems)} problems in roadmap")
    return problems

def main():
    problems = extract_problems()
    if problems:
        df = pd.DataFrame(problems)
        df.to_excel(OUTPUT_FILE, index=False)
        print(f"\nSaved {len(df)} roadmap problems to {OUTPUT_FILE}")
    else:
        print("No problems found. Please check the page structure or selectors.")

if __name__ == '__main__':
    main()