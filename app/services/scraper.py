import requests
from bs4 import BeautifulSoup
from typing import List
from ..schemas import JobCreate
import time
from ..config import settings

class JobScraper:
    def search_jobs(self, query: str) -> List[JobCreate]:
        found_jobs = []
        
        # 1. Search on Programathor
        clean_query = query.lower().strip().replace(" ", "-")
        url = f"https://programathor.com.br/jobs-{clean_query}"
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=settings.scraper_timeout)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                cards = soup.select('.cell-list')
                
                # Limit to 5 to avoid slow response time (fetching details takes time)
                for card in cards[: settings.scraper_max_results]:
                    title_elem = card.select_one('.cell-list-content h3')
                    link_elem = card.get('href')
                    if not link_elem:
                        a_tag = card.find('a', href=True)
                        if a_tag:
                            link_elem = a_tag['href']

                    if title_elem and link_elem:
                        title = title_elem.get_text(strip=True)
                        link = f"https://programathor.com.br{link_elem}"
                        
                        # Find company
                        company = "Programathor Job"
                        info_spans = card.select('.cell-list-content-icon span')
                        if info_spans: company = info_spans[0].get_text(strip=True)
                        
                        is_remote = "remoto" in card.get_text().lower()
                        
                        # --- DEEP SCRAPING (New!) ---
                        description = "Could not fetch description."
                        try:
                            time.sleep(settings.scraper_sleep_seconds)
                            job_resp = requests.get(link, headers=headers, timeout=settings.scraper_detail_timeout)
                            if job_resp.status_code == 200:
                                job_soup = BeautifulSoup(job_resp.content, 'html.parser')
                                # Programathor description selector
                                desc_div = job_soup.select_one('.line-height-2-4')
                                if desc_div:
                                    description = desc_div.get_text(strip=True)
                        except Exception as e:
                            print(f"Failed to fetch details for {link}: {e}")
                        # ----------------------------

                        found_jobs.append(JobCreate(
                            title=title,
                            company=company,
                            url=link,
                            source="Programathor",
                            is_remote=is_remote,
                            description=description # Saving the full text
                        ))
                        
        except Exception as e:
            print(f"Error scraping Programathor: {e}")
            
        return found_jobs
