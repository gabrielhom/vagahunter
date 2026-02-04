import requests
from bs4 import BeautifulSoup
from typing import List
from ..schemas import JobCreate

class JobScraper:
    def search_jobs(self, query: str) -> List[JobCreate]:
        found_jobs = []
        
        # 1. Search on Programathor
        # URL format: https://programathor.com.br/jobs-python
        clean_query = query.lower().strip()
        url = f"https://programathor.com.br/jobs-{clean_query}"
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Programathor uses 'cell-list' for job rows
                cards = soup.select('.cell-list')
                
                for card in cards[:10]:
                    # Title is usually in h3 with text-24 class
                    title_elem = card.select_one('.cell-list-content h3')
                    
                    # Company info might be tricky, sometimes just text or another span
                    # Programathor structure varies, let's try generic extraction
                    
                    link_elem = card.get('href') # The card itself is often an anchor or has one
                    if not link_elem:
                        a_tag = card.find('a')
                        if a_tag: link_elem = a_tag['href']

                    if title_elem and link_elem:
                        title = title_elem.get_text(strip=True)
                        company = "Programathor Job" # Default if not found easily
                        
                        # Try to find company name (often separate span)
                        info_spans = card.select('.cell-list-content-icon span')
                        if info_spans:
                            company = info_spans[0].get_text(strip=True)

                        link = f"https://programathor.com.br{link_elem}"
                        
                        # Check if remote (Programathor usually tags it)
                        is_remote = "remoto" in card.get_text().lower()
                        
                        found_jobs.append(JobCreate(
                            title=title,
                            company=company,
                            url=link,
                            source="Programathor",
                            is_remote=is_remote
                        ))
                        
        except Exception as e:
            print(f"Error scraping Programathor: {e}")
            
        return found_jobs
