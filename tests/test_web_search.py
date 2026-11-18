import os
import unittest
from unittest.mock import Mock, patch

import requests
from crewai_tools import SerperDevTool

from stockthestock.tools import web_search


class WebSearchToolTests(unittest.TestCase):
    def test_creates_search_and_news_tools(self) -> None:
        with patch.dict(os.environ, {"SERPER_API_KEY": "test-key"}):
            search_tool = web_search.create_web_search_tool()
            news_tool = web_search.create_web_search_tool("news")

        self.assertIsInstance(search_tool, SerperDevTool)
        self.assertEqual(search_tool.search_type, "search")
        self.assertEqual(search_tool.n_results, 5)
        self.assertIsNone(search_tool.max_usage_count)
        self.assertEqual(news_tool.search_type, "news")
        self.assertEqual(news_tool.n_results, 5)
        self.assertIsNone(news_tool.max_usage_count)

    def test_missing_api_key_has_actionable_error(self) -> None:
        with (
            patch.dict(os.environ, {}, clear=True),
            patch.object(web_search, "load_dotenv", return_value=False),
        ):
            with self.assertRaisesRegex(RuntimeError, "SERPER_API_KEY"):
                web_search.create_web_search_tool()

    def test_failed_query_is_not_retried_but_other_queries_are_allowed(self) -> None:
        tool = web_search.ResilientSerperDevTool(
            search_type="search",
            n_results=5,
        )
        error = requests.HTTPError("403 Forbidden")
        error.response = Mock(status_code=403)
        with patch.object(
            tool,
            "_make_api_request",
            side_effect=[error, {"organic": []}],
        ) as request:
            first_result = tool._run(search_query="same query")
            retry_result = tool._run(search_query="same query")
            other_query_result = tool._run(search_query="different query")

        self.assertIn("HTTP 403", first_result["error"])
        self.assertIn("not retried", retry_result["error"])
        self.assertNotIn("error", other_query_result)
        self.assertEqual(request.call_count, 2)

    def test_successful_searches_have_no_usage_limit(self) -> None:
        with patch.dict(os.environ, {"SERPER_API_KEY": "test-key"}):
            tool = web_search.create_web_search_tool()
            with patch.object(
                tool,
                "_make_api_request",
                return_value={"organic": [], "credits": 1},
            ) as request:
                tool._run(search_query="first query")
                tool._run(search_query="second query")

        self.assertEqual(request.call_count, 2)


if __name__ == "__main__":
    unittest.main()
