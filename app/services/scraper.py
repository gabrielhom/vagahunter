import asyncio
import httpx
from bs4 import BeautifulSoup
from typing import List
from tenacity import retry, stop_after_attempt, wait_fixed
from ..schemas import JobCreate
from ..config import settings
import logging

logger = logging.getLogger(__name__)

class JobScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; VagaHunter/1.0; +https://github.com/)",
            "Accept": "text/html,application/xhtml+xml",
        }
        self._detail_semaphore = asyncio.Semaphore(4)

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1), reraise=True)
    async def _get(self, client: httpx.AsyncClient, url: str, timeout: int):
        return await client.get(url, headers=self.headers, timeout=timeout, follow_redirects=True)

    async def _fetch_description(self, client: httpx.AsyncClient, link: str) -> str:
        async with self._detail_semaphore:
            await asyncio.sleep(settings.scraper_sleep_seconds)
            try:
                job_resp = await self._get(client, link, settings.scraper_detail_timeout)
                if job_resp.status_code == 200:
                    job_soup = BeautifulSoup(job_resp.content, "html.parser")
                    desc_div = job_soup.select_one(".line-height-2-4")
                    if desc_div:
                        return desc_div.get_text(strip=True)
            except Exception as e:
                logger.warning("Failed to fetch details for %s: %s", link, e)
            return "Could not fetch description."

    async def search_jobs(self, query: str) -> List[JobCreate]:
        found_jobs: List[JobCreate] = []
        clean_query = (query or "").lower().strip().replace(" ", "-")
        if not clean_query:
            return found_jobs

        url = f"https://programathor.com.br/jobs-{clean_query}"
        async with httpx.AsyncClient() as client:
            try:
                response = await self._get(client, url, settings.scraper_timeout)
                if response.status_code != 200 or "text/html" not in response.headers.get("Content-Type", ""):
                    return found_jobs

                soup = BeautifulSoup(response.content, "html.parser")
                cards = soup.select(".cell-list")
                detail_tasks = []
                meta = []
                for card in cards[: settings.scraper_max_results]:
                    title_elem = card.select_one(".cell-list-content h3")
                    anchor = card.find("a", href=True)
                    link_elem = card.get("href") or (anchor["href"] if anchor else None)
                    if not title_elem or not link_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    link = f"https://programathor.com.br{link_elem}"
                    company = "Programathor Job"
                    info_spans = card.select(".cell-list-content-icon span")
                    if info_spans:
                        company = info_spans[0].get_text(strip=True)
                    is_remote = "remoto" in card.get_text().lower()

                    meta.append((title, company, link, is_remote))
                    detail_tasks.append(asyncio.create_task(self._fetch_description(client, link)))

                descriptions = await asyncio.gather(*detail_tasks, return_exceptions=True)
                for (title, company, link, is_remote), desc in zip(meta, descriptions):
                    description = desc if isinstance(desc, str) else "Could not fetch description."
                    found_jobs.append(JobCreate(
                        title=title,
                        company=company,
                        url=link,
                        source="Programathor",
                        is_remote=is_remote,
                        description=description[:5000],
                    ))
            except Exception as e:
                logger.error("Error scraping Programathor: %s", e)
        return found_jobs
