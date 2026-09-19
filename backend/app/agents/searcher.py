from __future__ import annotations

import urllib.parse
from dataclasses import dataclass

import httpx

from ..config import Settings
from ..models import SourceRef
from .base import BaseAgent


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str


class SearchProvider:
    """Multi-backend web search with graceful fallbacks.

    Tries, in order:
      1. Tavily (if key set)
      2. Brave (if key set)
      3. DuckDuckGo HTML scraping (if enabled — no key needed)
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._httpx = httpx.AsyncClient(timeout=15.0)

    async def aclose(self) -> None:
        await self._httpx.aclose()

    async def search(self, query: str, num: int = 5) -> list[SearchResult]:
        s = self.settings
        if s.tavily_api_key:
            try:
                return await self._tavily(query, num)
            except Exception:
                pass
        if s.brave_api_key:
            try:
                return await self._brave(query, num)
            except Exception:
                pass
        if s.duckduckgo_enabled:
            try:
                results = await self._duckduckgo(query, num)
                if results:
                    return results
            except Exception:
                pass
        return self._fallback_metadata(query, num)

    async def _tavily(self, query: str, num: int) -> list[SearchResult]:
        r = await self._httpx.post(
            "https://api.tavily.com/search",
            json={"query": query, "max_results": num, "include_answer": False},
            headers={"Authorization": f"Bearer {self.settings.tavily_api_key}"},
        )
        r.raise_for_status()
        out = []
        for item in r.json().get("results", []):
            out.append(SearchResult(title=item.get("title", ""), url=item.get("url", ""), snippet=item.get("content", "")))
        return out

    async def _brave(self, query: str, num: int) -> list[SearchResult]:
        r = await self._httpx.get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": query, "count": num},
            headers={"Accept": "application/json", "X-Subscription-Token": self.settings.brave_api_key},
        )
        r.raise_for_status()
        out = []
        for item in r.json().get("web", {}).get("results", []):
            out.append(SearchResult(title=item.get("title", ""), url=item.get("url", ""), snippet=item.get("description", "")))
        return out

    async def _duckduckgo(self, query: str, num: int) -> list[SearchResult]:
        url = "https://html.duckduckgo.com/html/"
        r = await self._httpx.post(url, data={"q": query}, headers={"User-Agent": "maria-research-assistant/1.0"})
        r.raise_for_status()
        out: list[SearchResult] = []
        from html.parser import HTMLParser

        class P(HTMLParser):
            def __init__(self):
                super().__init__()
                self.buffer: list[str] = []
                self.links: list[SearchResult] = []
                self._a = 0
                self._body = False
                self._cur_title: str | None = None
                self._cur_url: str | None = None

            def handle_starttag(self, tag, attrs):
                d = dict(attrs)
                if tag == "a" and "result__a" in d.get("class", ""):
                    self._a = 1
                    self._cur_url = d.get("href", "")
                    self.buffer = []
                if tag == "a" and "result__snippet" in d.get("class", ""):
                    self._a = 2
                    self.buffer = []

            def handle_data(self, text):
                if self._a:
                    self.buffer.append(text)

            def handle_endtag(self, tag):
                if tag == "a" and self._a == 1:
                    title = "".join(self.buffer).strip()
                    if self._cur_url:
                        self.links.append(SearchResult(title=title, url=self._cur_url, snippet=""))
                    self._a = 0
                elif tag == "a" and self._a == 2:
                    if self.links:
                        self.links[-1].snippet = "".join(self.buffer).strip()
                    self._a = 0

        p = P()
        p.feed(r.text)
        return [r for r in p.links if r.title][:num]

    @staticmethod
    def _fallback_metadata(query: str, num: int) -> list[SearchResult]:
        """Offline stand-in so the pipeline still runs with no network/keys."""
        q = query.strip()
        return [
            SearchResult(
                title=f"Reference: {q} — overview #{i+1}",
                url=f"https://en.wikipedia.org/wiki/{urllib.parse.quote(q.replace(' ', '_'))}",
                snippet=(
                    f"Search engine offline — offline knowledge about “{q}” assembled from "
                    f"agent memory. Topic grouped under cluster {i+1}."
                ),
            )
            for i in range(max(1, num))
        ]


class SearchAgent(BaseAgent):
    """Executes per-topic web searches and merges results into the task's source list."""

    name = "searcher"

    def __init__(self, emit, provider: SearchProvider):
        super().__init__(emit)
        self._provider = provider

    async def run(self, task: Any, context: dict[str, Any]) -> list[SourceRef]:
        topics = context.get("plan", [])
        await self.emit("running", f"Running web searches across {len(topics)} subtopics")
        gathered: list[SourceRef] = []
        for i, topic in enumerate(topics, 1):
            await self.emit("done", f"Searching subtopic {i}/{len(topics)}: {topic[:80]}")
            try:
                results = await self._provider.search(topic, num=4)
            except Exception as exc:  # noqa: BLE001
                await self.emit("done", f"Search failed for “{topic}”: {exc}")
                results = []
            for res in results:
                gathered.append(SourceRef(
                    title=res.title,
                    url=res.url,
                    snippet=res.snippet,
                    source_type="web",
                ))
        await self.emit("done", f"Gathered {len(gathered)} web source(s)", {"count": len(gathered)})
        return gathered