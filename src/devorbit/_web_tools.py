"""Web operation tools for the Devorbit SDK.

This module provides tools for web operations including fetching URLs,
searching the web, and converting HTML to markdown.
"""

import asyncio
import re
from collections.abc import Callable
from typing import Any
from urllib.parse import urlparse

import httpx
from typing_extensions import TypedDict


class WebFetchResult(TypedDict):
    """Result from web fetch operation."""

    url: str
    content: str
    content_type: str
    status_code: int
    redirect_url: str | None


class WebSearchResult(TypedDict):
    """Result from web search operation."""

    query: str
    results: list[dict[str, Any]]
    num_results: int


# HTML to Markdown conversion
def html_to_markdown(html: str) -> str:
    """Convert HTML to Markdown format.

    This is a basic implementation that handles common HTML elements.
    For production use, consider using a library like markdownify or html2text.

    Args:
        html: HTML content to convert

    Returns:
        Markdown formatted text
    """
    # Remove script and style tags (handle any content in closing tags)
    html = re.sub(r"<script\b[^>]*>.*?</script[^>]*>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style\b[^>]*>.*?</style[^>]*>", "", html, flags=re.DOTALL | re.IGNORECASE)

    # Convert headers
    def make_header_replacer(level: int) -> Callable[[re.Match[str]], str]:
        """Create a header replacement function for a specific level."""

        def replacer(match: re.Match[str]) -> str:
            return f"{'#' * level} {match.group(1)}\n\n"

        return replacer

    for i in range(6, 0, -1):
        html = re.sub(
            rf"<h{i}[^>]*>(.*?)</h{i}>",
            make_header_replacer(i),
            html,
            flags=re.DOTALL | re.IGNORECASE,
        )

    # Convert links
    html = re.sub(
        r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
        r"[\2](\1)",
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # Convert images
    html = re.sub(
        r'<img[^>]+src=["\']([^"\']+)["\'][^>]*alt=["\']([^"\']*)["\'][^>]*>',
        r"![\2](\1)",
        html,
        flags=re.IGNORECASE,
    )
    html = re.sub(
        r'<img[^>]+alt=["\']([^"\']*)["\'][^>]*src=["\']([^"\']+)["\'][^>]*>',
        r"![\1](\2)",
        html,
        flags=re.IGNORECASE,
    )
    html = re.sub(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>', r"![](\1)", html, flags=re.IGNORECASE)

    # Convert bold and italic
    html = re.sub(
        r"<(?:strong|b)(?:\s[^>]*)?>([^<]+)</(?:strong|b)>", r"**\1**", html, flags=re.IGNORECASE
    )
    html = re.sub(r"<(?:em|i)(?:\s[^>]*)?>([^<]+)</(?:em|i)>", r"*\1*", html, flags=re.IGNORECASE)

    # Convert code blocks
    html = re.sub(
        r"<pre[^>]*><code[^>]*>(.*?)</code></pre>",
        r"```\n\1\n```\n",
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )
    html = re.sub(r"<code[^>]*>(.*?)</code>", r"`\1`", html, flags=re.DOTALL | re.IGNORECASE)

    # Convert lists
    html = re.sub(r"<li[^>]*>(.*?)</li>", r"- \1\n", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"</?[uo]l[^>]*>", "\n", html, flags=re.IGNORECASE)

    # Convert paragraphs and breaks
    html = re.sub(r"<p[^>]*>(.*?)</p>", r"\1\n\n", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)

    # Remove all remaining HTML tags
    html = re.sub(r"<[^>]+>", "", html)

    # Decode common HTML entities
    html = html.replace("&nbsp;", " ")
    html = html.replace("&amp;", "&")
    html = html.replace("&lt;", "<")
    html = html.replace("&gt;", ">")
    html = html.replace("&quot;", '"')
    html = html.replace("&#39;", "'")
    html = html.replace("&mdash;", "—")
    html = html.replace("&ndash;", "-")

    # Clean up multiple newlines
    html = re.sub(r"\n{3,}", "\n\n", html)

    return html.strip()


# WebFetch tool
def create_web_fetch_tool() -> dict[str, Any]:
    """Create WebFetch tool definition.

    Returns:
        Tool definition for WebFetch
    """
    return {
        "name": "web_fetch",
        "description": """Fetch content from a URL and optionally process it.

This tool fetches web content and converts HTML to markdown for easier reading.
It handles redirects and provides the final URL if redirected.

Use this when you need to:
- Fetch documentation from a URL
- Read web pages and articles
- Download and process web content
- Check API responses""",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to fetch content from (must be a valid HTTP/HTTPS URL)",
                },
                "convert_to_markdown": {
                    "type": "boolean",
                    "description": "Whether to convert HTML content to markdown (default: true)",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Request timeout in seconds (default: 30)",
                },
                "follow_redirects": {
                    "type": "boolean",
                    "description": "Whether to follow HTTP redirects (default: true)",
                },
            },
            "required": ["url"],
        },
    }


async def web_fetch(
    url: str,
    convert_to_markdown: bool = True,
    timeout: int = 30,
    follow_redirects: bool = True,
) -> WebFetchResult:
    """Fetch content from a URL.

    Args:
        url: URL to fetch
        convert_to_markdown: Convert HTML to markdown
        timeout: Request timeout in seconds
        follow_redirects: Follow HTTP redirects

    Returns:
        WebFetchResult with fetched content

    Raises:
        ValueError: If URL is invalid
        httpx.HTTPError: If request fails
    """
    # Basic validation - check for obviously invalid URLs
    if not url or not isinstance(url, str):
        raise ValueError(f"Invalid URL: {url}")

    # Check for invalid characters that could cause issues
    invalid_chars = [" ", "!", "|", "{", "}", "[", "]"]
    if any(char in url for char in invalid_chars):
        raise ValueError(f"Invalid URL contains illegal characters: {url}")

    # Validate URL
    parsed = urlparse(url)
    if not parsed.scheme or parsed.scheme not in ("http", "https"):
        # Auto-upgrade to HTTPS
        if not parsed.scheme:
            url = f"https://{url}"
            parsed = urlparse(url)
        elif parsed.scheme == "http":
            url = url.replace("http://", "https://", 1)

    if not parsed.netloc:
        raise ValueError(f"Invalid URL: {url}")

    # Fetch content
    async with httpx.AsyncClient(follow_redirects=follow_redirects, timeout=timeout) as client:
        response = await client.get(url)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "").lower()
        redirect_url = str(response.url) if str(response.url) != url else None

        # Get content
        content = response.text

        # Convert HTML to markdown if requested
        if convert_to_markdown and "html" in content_type:
            content = html_to_markdown(content)

        return WebFetchResult(
            url=url,
            content=content,
            content_type=content_type,
            status_code=response.status_code,
            redirect_url=redirect_url,
        )


def web_fetch_sync(
    url: str,
    convert_to_markdown: bool = True,
    timeout: int = 30,
    follow_redirects: bool = True,
) -> WebFetchResult:
    """Synchronous version of web_fetch.

    Args:
        url: URL to fetch
        convert_to_markdown: Convert HTML to markdown
        timeout: Request timeout in seconds
        follow_redirects: Follow HTTP redirects

    Returns:
        WebFetchResult with fetched content
    """
    return asyncio.run(web_fetch(url, convert_to_markdown, timeout, follow_redirects))


# WebSearch tool
def create_web_search_tool() -> dict[str, Any]:
    """Create WebSearch tool definition.

    Returns:
        Tool definition for WebSearch
    """
    return {
        "name": "web_search",
        "description": """Search the web for information.

This tool performs web searches and returns relevant results.
Use this when you need current information, documentation, or answers
that may not be in your training data.

Note: This is a placeholder implementation. For production use,
integrate with a search API like Google Custom Search, Bing Search API,
or DuckDuckGo API.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query",
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return (default: 10)",
                },
                "safe_search": {
                    "type": "boolean",
                    "description": "Enable safe search filtering (default: true)",
                },
            },
            "required": ["query"],
        },
    }


async def web_search(
    query: str,
    num_results: int = 10,
    safe_search: bool = True,
) -> WebSearchResult:
    """Search the web for information.

    Note: This is a placeholder implementation that returns a mock response.
    For production use, integrate with a real search API.

    Args:
        query: Search query
        num_results: Number of results to return
        safe_search: Enable safe search

    Returns:
        WebSearchResult with search results
    """
    # This is a placeholder implementation
    # In production, integrate with Google Custom Search API, Bing Search API, etc.

    return WebSearchResult(
        query=query,
        results=[
            {
                "title": f"Search result for: {query}",
                "url": "https://example.com",
                "snippet": "This is a placeholder implementation. "
                "Please integrate with a real search API for production use.",
            }
        ],
        num_results=1,
    )


def web_search_sync(
    query: str,
    num_results: int = 10,
    safe_search: bool = True,
) -> WebSearchResult:
    """Synchronous version of web_search.

    Args:
        query: Search query
        num_results: Number of results to return
        safe_search: Enable safe search

    Returns:
        WebSearchResult with search results
    """
    return asyncio.run(web_search(query, num_results, safe_search))


# Helper function to get all web tools
def get_all_web_tools() -> list[dict[str, Any]]:
    """Get all web operation tools.

    Returns:
        List of web tool definitions
    """
    return [
        create_web_fetch_tool(),
        create_web_search_tool(),
    ]


__all__ = [
    "WebFetchResult",
    "WebSearchResult",
    "create_web_fetch_tool",
    "create_web_search_tool",
    "get_all_web_tools",
    "html_to_markdown",
    "web_fetch",
    "web_fetch_sync",
    "web_search",
    "web_search_sync",
]
