import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin

BASE_URL = "https://algomap.io"
OUTPUT_FILE = "algomap_roadmap_problems.xlsx"

def extract_roadmap_problems():
    print("Fetching roadmap page...")
    response = requests.get(BASE_URL)
    soup = BeautifulSoup(response.text, 'html.parser')

    problems = []
    roadmap_table = soup.select_one('table')
    if roadmap_table:
        for row in roadmap_table.select('tbody tr'):
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
                        'Solution Link': solution_link
                    })
    print(f"Found {len(problems)} problems in roadmap")
    return problems

def main():
    problems = extract_roadmap_problems()
    df = pd.DataFrame(problems)
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"\nSaved {len(df)} roadmap problems to {OUTPUT_FILE}")

if __name__ == '__main__':
    main()