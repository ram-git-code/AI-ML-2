import re
import httpx
from typing import Optional, List, Dict, Any
from app.core.logging import logger

class WebSearchService:
    """
    Clean provider abstraction for external web search and real-time grounding.
    Used for time-sensitive, current affairs, weather, office-holders, and external general knowledge queries.
    """

    DUCKDUCKGO_API_URL = "https://api.duckduckgo.com/"
    WIKIPEDIA_API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"

    @classmethod
    async def search(cls, query: str, max_results: int = 3) -> Optional[str]:
        """
        Executes external web query and returns summarized context text.
        """
        if not query or not query.strip():
            return None

        clean_query = query.strip()

        # 1. Try DuckDuckGo Instant Answer API
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                params = {
                    "q": clean_query,
                    "format": "json",
                    "no_html": "1",
                    "skip_disambig": "1"
                }
                res = await client.get(cls.DUCKDUCKGO_API_URL, params=params)
                if res.status_code == 200:
                    data = res.json()
                    abstract = data.get("AbstractText", "").strip()
                    if abstract:
                        logger.info(f"WebSearch: Retrieved DuckDuckGo instant summary for '{clean_query}'")
                        return abstract

                    # Check related topics
                    related = data.get("RelatedTopics", [])
                    snippets = []
                    for topic in related[:max_results]:
                        if isinstance(topic, dict) and "Text" in topic:
                            snippets.append(topic["Text"])
                    if snippets:
                        return "\n".join(snippets)
        except Exception as ddg_err:
            logger.debug(f"WebSearch DuckDuckGo error: {ddg_err}")

        # 2. Try Wikipedia Summary for prominent entities / roles
        try:
            wiki_topic = clean_query.replace(" ", "_")
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(cls.WIKIPEDIA_API_URL.format(title=wiki_topic), headers={"User-Agent": "AIQuestionBank/1.0"})
                if res.status_code == 200:
                    data = res.json()
                    extract = data.get("extract", "").strip()
                    if extract:
                        logger.info(f"WebSearch: Retrieved Wikipedia summary for '{clean_query}'")
                        return extract
        except Exception as wiki_err:
            logger.debug(f"WebSearch Wikipedia error: {wiki_err}")

        return None
