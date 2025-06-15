import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin
import time
import re

# Configuration
BASE_URL = "https://algomap.io"
OUTPUT_FILE = "algomap_roadmap_problems.xlsx"

def extract_roadmap_problems():
    """Extract problems listed in the roadmap in their original order"""
    print("Fetching roadmap page...")
    response = requests.get(BASE_URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Updated selector based on your HTML structure
    problem_elements = soup.select('.roadmap-section')
    
    problems = []
    for elem in problem_elements:
        # Extract problem title from the text
        problem_title = elem.get_text(strip=True)
        # Try to extract a problem identifier from the onclick attribute
        onclick = elem.get('onclick', '')
        match = re.search(r"openSectionModal\('([^']+)'\)", onclick)
        if match:
            problem_id = match.group(1)
            # You may need to construct the problem URL if possible
            # This is a placeholder; update if you know the URL pattern
            problem_url = f"{BASE_URL}/problems/{problem_id.replace(' ', '-').lower()}"
        else:
            problem_url = ''
        problems.append({
            'Problem': problem_title,
            'Problem Link': problem_url,
            'Solution Link': ''  # Will be filled later
        })
    
    print(f"Found {len(problems)} problems in roadmap")
    return problems

def add_solution_links(problems):
    """Add solution links by visiting each problem page"""
    print("Fetching solution links...")
    for i, problem in enumerate(problems):
        try:
            # Skip if no problem link
            if not problem['Problem Link']:
                continue
            # Add delay to avoid rate limiting
            if i > 0 and i % 10 == 0:
                time.sleep(2)
                
            response = requests.get(problem['Problem Link'])
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # UPDATE THIS SELECTOR based on solution link structure
            solution_elem = soup.select_one('a.solution-link')
            if solution_elem:
                problem['Solution Link'] = urljoin(BASE_URL, solution_elem['href'])
                
            print(f"Processed {i+1}/{len(problems)}: {problem['Problem']}")
        except Exception as e:
            print(f"Error processing {problem['Problem']}: {str(e)}")
    
    return problems

def main():
    # Get problems from roadmap
    problems = extract_roadmap_problems()
    
    # Add solution links
    problems_with_solutions = add_solution_links(problems)
    
    # Save to Excel
    df = pd.DataFrame(problems_with_solutions)
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"\nSaved {len(df)} roadmap problems to {OUTPUT_FILE}")

if __name__ == '__main__':
    main()