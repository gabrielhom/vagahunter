import asyncio
import httpx
from bs4 import BeautifulSoup
from typing import List
from tenacity import retry, stop_after_attempt, wait_fixed
from ..schemas import JobCreate
from ..config import settings
import logging
from urllib.parse import urlparse, urlunparse

logger = logging.getLogger(__name__)

class JobScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; VagaHunter/1.0; +https://github.com/)",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.8,pt-BR;q=0.7",
        }
        self._detail_semaphore = asyncio.Semaphore(4)

    def _normalize_url(self, url: str, base: str | None = None) -> str:
        """Normalize URLs to avoid duplicates and ensure scheme."""
        if not isinstance(url, str):
            return ""
        cleaned = url.strip()
        if base and cleaned.startswith("/"):
            cleaned = f"{base.rstrip('/')}{cleaned}"
        parsed = urlparse(cleaned)
        if not parsed.scheme:
            parsed = parsed._replace(scheme="https")
        normalized = urlunparse(parsed._replace(fragment=""))
        return normalized

    def _remote_title(self, title: str, company: str | None = None) -> str:
        """Ensure the title carries a remote marker; fall back to company when missing."""
        base = (title or "").strip()
        if not base:
            base = f"Remote role at {company}" if company else "Remote role"
        if not base.startswith("🌐"):
            base = f"🌐 {base}"
        return base

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1), reraise=True)
    async def _get(self, client: httpx.AsyncClient, url: str, timeout: int):
        return await client.get(url, headers=self.headers, timeout=timeout, follow_redirects=True)

    async def _fetch_description(self, client: httpx.AsyncClient, link: str, selectors: list[str]) -> str:
        async with self._detail_semaphore:
            await asyncio.sleep(settings.scraper_sleep_seconds)
            try:
                job_resp = await self._get(client, link, settings.scraper_detail_timeout)
                if job_resp.status_code == 200 and "text/html" in job_resp.headers.get("Content-Type", ""):
                    job_soup = BeautifulSoup(job_resp.content, "html.parser")
                    for selector in selectors:
                        desc_div = job_soup.select_one(selector)
                        if desc_div:
                            text = desc_div.get_text(" ", strip=True)
                            if text:
                                return text[:5000]
                    fallback_text = job_soup.get_text(" ", strip=True)
                    if fallback_text:
                        return fallback_text[:5000]
            except Exception as e:
                logger.warning("Failed to fetch details for %s: %s", link, e)
            return "Could not fetch description."

    async def _scrape_programathor(self, client: httpx.AsyncClient, clean_query: str) -> List[JobCreate]:
        results: List[JobCreate] = []
        url = f"https://programathor.com.br/jobs-{clean_query}"
        try:
            response = await self._get(client, url, settings.scraper_timeout)
            if response.status_code != 200 or "text/html" not in response.headers.get("Content-Type", ""):
                return results

            soup = BeautifulSoup(response.content, "html.parser")
            cards = soup.select(".cell-list")
            detail_tasks = []
            meta = []
            for card in cards[: settings.scraper_max_results]:
                title_elem = card.select_one(".cell-list-content h3")
                anchor = card.find("a", href=True)
                raw_href = card.get("href") or (anchor.get("href") if anchor else None)
                link_elem = raw_href if isinstance(raw_href, str) else None
                if not title_elem or not link_elem:
                    continue

                title = title_elem.get_text(strip=True)
                link = self._normalize_url(f"https://programathor.com.br{link_elem}")
                company = "Programathor Job"
                info_spans = card.select(".cell-list-content-icon span")
                if info_spans:
                    company = info_spans[0].get_text(strip=True)
                is_remote = "remoto" in card.get_text().lower()

                if not link:
                    continue
                meta.append((title, company, link, is_remote))
                detail_tasks.append(asyncio.create_task(self._fetch_description(client, link, [".line-height-2-4", "article", "body"])))

            descriptions = await asyncio.gather(*detail_tasks, return_exceptions=True)
            for (title, company, link, is_remote), desc in zip(meta, descriptions):
                description = desc if isinstance(desc, str) else "Could not fetch description."
                results.append(JobCreate(
                    title=title,
                    company=company,
                    url=link,
                    source="Programathor",
                    is_remote=is_remote,
                    description=description[:5000],
                ))
        except Exception as e:
            logger.error("Error scraping Programathor: %s", e)
        return results

    async def _scrape_weworkremotely(self, client: httpx.AsyncClient, clean_query: str) -> List[JobCreate]:
        results: List[JobCreate] = []
        url = f"https://weworkremotely.com/remote-jobs/search?term={clean_query}"
        try:
            response = await self._get(client, url, settings.scraper_timeout)
            if response.status_code != 200 or "text/html" not in response.headers.get("Content-Type", ""):
                return results

            soup = BeautifulSoup(response.content, "html.parser")
            cards = soup.select("section.jobs li.feature, section.jobs li.job")
            detail_tasks = []
            meta = []
            for card in cards[: settings.scraper_max_results]:
                anchor = card.find("a", href=True)
                href = anchor.get("href") if anchor else None
                if not isinstance(href, str):
                    continue
                link = self._normalize_url(href, base="https://weworkremotely.com")
                if not link:
                    continue

                title_elem = card.select_one("span.title") or card.select_one("span.company")
                company_elem = card.select_one("span.company") or card.select_one("span.company-name")
                company = (company_elem.get_text(strip=True) if company_elem else "WeWorkRemotely").strip()
                raw_title = title_elem.get_text(strip=True) if title_elem else ""
                title = self._remote_title(raw_title, company)

                meta.append((title, company, link))
                detail_tasks.append(asyncio.create_task(self._fetch_description(
                    client,
                    link,
                    ["div.listing-container", "div#job-listing", "article", "main"]
                )))

            descriptions = await asyncio.gather(*detail_tasks, return_exceptions=True)
            for (title, company, link), desc in zip(meta, descriptions):
                description = desc if isinstance(desc, str) else "Could not fetch description."
                results.append(JobCreate(
                    title=title,
                    company=company,
                    url=link,
                    source="WeWorkRemotely",
                    is_remote=True,
                    description=description[:5000],
                ))
        except Exception as e:
            logger.error("Error scraping WeWorkRemotely: %s", e)
        return results

    async def _scrape_remoteok(self, client: httpx.AsyncClient, clean_query: str) -> List[JobCreate]:
        results: List[JobCreate] = []
        url = f"https://remoteok.com/remote-{clean_query}-jobs"
        try:
            response = await self._get(client, url, settings.scraper_timeout)
            if response.status_code != 200 or "text/html" not in response.headers.get("Content-Type", ""):
                return results

            soup = BeautifulSoup(response.content, "html.parser")
            rows = soup.select("tr.job") or soup.select("div.job")
            detail_tasks = []
            meta = []
            for row in rows[: settings.scraper_max_results]:
                raw_link = row.get("data-href") or row.get("data-url")
                if not isinstance(raw_link, str):
                    anchor = row.find("a", href=True)
                    raw_link = anchor.get("href") if anchor else None
                if not isinstance(raw_link, str):
                    continue
                link = self._normalize_url(raw_link, base="https://remoteok.com")
                if not link:
                    continue

                title_elem = row.select_one("h2") or row.select_one("a.preventLink")
                company_elem = row.select_one("h3") or row.select_one("span.companyLink")
                company = (company_elem.get_text(strip=True) if company_elem else "RemoteOK").strip()
                raw_title = title_elem.get_text(strip=True) if title_elem else ""
                title = self._remote_title(raw_title, company)

                meta.append((title, company, link))
                detail_tasks.append(asyncio.create_task(self._fetch_description(
                    client,
                    link,
                    ["div.description", "section.description", "article", "main"]
                )))

            descriptions = await asyncio.gather(*detail_tasks, return_exceptions=True)
            for (title, company, link), desc in zip(meta, descriptions):
                description = desc if isinstance(desc, str) else "Could not fetch description."
                results.append(JobCreate(
                    title=title,
                    company=company,
                    url=link,
                    source="RemoteOK",
                    is_remote=True,
                    description=description[:5000],
                ))
        except Exception as e:
            logger.error("Error scraping RemoteOK: %s", e)
        return results

    async def search_jobs(self, query: str) -> List[JobCreate]:
        clean_query = (query or "").lower().strip().replace(" ", "-")
        if not clean_query:
            return []

        async with httpx.AsyncClient() as client:
            tasks = [
                self._scrape_programathor(client, clean_query),
                self._scrape_weworkremotely(client, clean_query),
                self._scrape_remoteok(client, clean_query),
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        aggregated: List[JobCreate] = []
        seen_urls = set()
        for res in results:
            if isinstance(res, Exception):
                logger.error("Scraper task failed: %s", res)
                continue
            if not isinstance(res, list):
                continue
            for job in res:
                if job.url in seen_urls:
                    continue
                seen_urls.add(job.url)
                aggregated.append(job)

        return aggregated
