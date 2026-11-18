import os
from json import JSONDecodeError
from typing import Any, Literal

import requests
from crewai_tools import SerperDevTool
from dotenv import load_dotenv
from pydantic import PrivateAttr


class ResilientSerperDevTool(SerperDevTool):
    """Keep search unlimited while preventing retries of a failed query."""

    _failed_queries: set[tuple[str, str]] = PrivateAttr(default_factory=set)

    def _run(self, **kwargs: Any) -> dict[str, Any]:
        query = kwargs.get("search_query") or kwargs.get("query") or ""
        search_type = kwargs.get("search_type", self.search_type)
        failed_query = (search_type, query.strip().casefold())
        if failed_query in self._failed_queries:
            return {
                "error": (
                    "This exact Serper query already failed; it was not retried. "
                    "Continue without it or use a different query."
                )
            }

        try:
            return super()._run(**kwargs)
        except (requests.RequestException, JSONDecodeError, ValueError) as error:
            self._failed_queries.add(failed_query)
            status_code = getattr(getattr(error, "response", None), "status_code", None)
            status = f"HTTP {status_code}" if status_code else type(error).__name__
            return {
                "error": (
                    f"Serper search failed ({status}); this exact query will not "
                    "be retried. Continue with other evidence and report the limitation."
                )
            }


def create_web_search_tool(
    search_type: Literal["search", "news"] = "search",
) -> ResilientSerperDevTool:
    """Create a Serper tool that allows unlimited calls and skips failed-query retries."""
    load_dotenv()
    if not os.getenv("SERPER_API_KEY"):
        raise RuntimeError(
            "Internet research requires SERPER_API_KEY. Add your Serper API key "
            "to the project .env file or environment before running the flow."
        )

    return ResilientSerperDevTool(search_type=search_type, n_results=5)
