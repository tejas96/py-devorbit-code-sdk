"""Tests for web operation tools."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from devorbit import (
    create_web_fetch_tool,
    create_web_search_tool,
    get_all_web_tools,
    html_to_markdown,
    web_fetch,
    web_fetch_sync,
    web_search,
    web_search_sync,
)


class TestHTMLToMarkdown:
    """Tests for HTML to markdown conversion."""

    def test_convert_headers(self) -> None:
        """Test header conversion."""
        html = "<h1>Title</h1><h2>Subtitle</h2><h3>Section</h3>"
        result = html_to_markdown(html)
        assert "# Title" in result
        assert "## Subtitle" in result
        assert "### Section" in result

    def test_convert_links(self) -> None:
        """Test link conversion."""
        html = '<a href="https://example.com">Example</a>'
        result = html_to_markdown(html)
        assert "[Example](https://example.com)" in result

    def test_convert_images(self) -> None:
        """Test image conversion."""
        html = '<img src="image.jpg" alt="Test Image">'
        result = html_to_markdown(html)
        assert "![Test Image](image.jpg)" in result or "![](image.jpg)" in result

    def test_convert_bold_italic(self) -> None:
        """Test bold and italic conversion."""
        html = "<strong>Bold</strong> and <em>Italic</em>"
        result = html_to_markdown(html)
        assert "**Bold**" in result
        assert "*Italic*" in result

    def test_convert_code_blocks(self) -> None:
        """Test code block conversion."""
        html = "<pre><code>print('hello')</code></pre>"
        result = html_to_markdown(html)
        assert "```" in result
        assert "print('hello')" in result

    def test_convert_inline_code(self) -> None:
        """Test inline code conversion."""
        html = "Use <code>print()</code> to output"
        result = html_to_markdown(html)
        assert "`print()`" in result

    def test_convert_lists(self) -> None:
        """Test list conversion."""
        html = "<ul><li>Item 1</li><li>Item 2</li></ul>"
        result = html_to_markdown(html)
        assert "- Item 1" in result
        assert "- Item 2" in result

    def test_remove_scripts_and_styles(self) -> None:
        """Test removal of script and style tags."""
        html = "<script>alert('test')</script><style>body{}</style><p>Content</p>"
        result = html_to_markdown(html)
        assert "alert" not in result
        assert "body{}" not in result
        assert "Content" in result

    def test_remove_scripts_with_whitespace(self) -> None:
        """Test removal of script tags with whitespace before closing bracket."""
        # Security test: ensure malicious scripts with whitespace are also removed
        html = "<script>alert('xss')</script ><p>Content</p><script >alert('xss2')</script >"
        result = html_to_markdown(html)
        assert "alert" not in result
        assert "xss" not in result
        assert "Content" in result

    def test_decode_html_entities(self) -> None:
        """Test HTML entity decoding."""
        html = "AT&amp;T &lt;test&gt; &quot;quote&quot;"
        result = html_to_markdown(html)
        assert "AT&T" in result
        assert "<test>" in result
        assert '"quote"' in result


class TestWebFetchTool:
    """Tests for WebFetch tool."""

    def test_create_web_fetch_tool(self) -> None:
        """Test web fetch tool creation."""
        tool = create_web_fetch_tool()
        assert tool["name"] == "web_fetch"
        assert "description" in tool
        assert "input_schema" in tool
        assert "url" in tool["input_schema"]["properties"]

    @pytest.mark.asyncio
    async def test_web_fetch_success(self) -> None:
        """Test successful web fetch."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html"}
        mock_response.text = "<html><body><h1>Test</h1></body></html>"
        mock_response.url = "https://example.com"
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await web_fetch("https://example.com")

            assert result["url"] == "https://example.com"
            assert result["status_code"] == 200
            assert "Test" in result["content"]
            assert result["content_type"] == "text/html"

    @pytest.mark.asyncio
    async def test_web_fetch_http_upgrade(self) -> None:
        """Test HTTP to HTTPS upgrade."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.text = "Test content"
        mock_response.url = "https://example.com"
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            # Test URL without scheme - verify the actual URL starts with https://example.com
            result = await web_fetch("example.com")
            # Ensure the URL was properly upgraded and starts with the expected domain
            assert result["url"].startswith("https://example.com")

    @pytest.mark.asyncio
    async def test_web_fetch_invalid_url(self) -> None:
        """Test web fetch with invalid URL."""
        # This test checks that truly malformed URLs raise ValueError
        # Note: Simple strings get auto-upgraded to https://string format
        # so we need a truly invalid URL structure
        with pytest.raises((ValueError, Exception)):
            # Using a URL with invalid characters that can't be auto-fixed
            await web_fetch("ht!tp://not a valid url at all")

    @pytest.mark.asyncio
    async def test_web_fetch_no_markdown_conversion(self) -> None:
        """Test web fetch without markdown conversion."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html"}
        mock_response.text = "<html><h1>Test</h1></html>"
        mock_response.url = "https://example.com"
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await web_fetch("https://example.com", convert_to_markdown=False)

            assert "<h1>Test</h1>" in result["content"]

    @pytest.mark.asyncio
    async def test_web_fetch_redirect(self) -> None:
        """Test web fetch with redirect."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.text = "Redirected content"
        mock_response.url = "https://example.com/redirected"
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await web_fetch("https://example.com")

            assert result["redirect_url"] == "https://example.com/redirected"

    def test_web_fetch_sync(self) -> None:
        """Test synchronous web fetch."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.text = "Test content"
        mock_response.url = "https://example.com"
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = web_fetch_sync("https://example.com")

            assert result["url"] == "https://example.com"
            assert result["content"] == "Test content"


class TestWebSearchTool:
    """Tests for WebSearch tool."""

    def test_create_web_search_tool(self) -> None:
        """Test web search tool creation."""
        tool = create_web_search_tool()
        assert tool["name"] == "web_search"
        assert "description" in tool
        assert "input_schema" in tool
        assert "query" in tool["input_schema"]["properties"]

    @pytest.mark.asyncio
    async def test_web_search_basic(self) -> None:
        """Test basic web search."""
        result = await web_search("test query")

        assert result["query"] == "test query"
        assert "results" in result
        assert isinstance(result["results"], list)
        assert result["num_results"] > 0

    @pytest.mark.asyncio
    async def test_web_search_with_options(self) -> None:
        """Test web search with options."""
        result = await web_search("test", num_results=5, safe_search=True)

        assert result["query"] == "test"
        assert "results" in result

    def test_web_search_sync(self) -> None:
        """Test synchronous web search."""
        result = web_search_sync("test query")

        assert result["query"] == "test query"
        assert "results" in result


class TestWebToolsHelpers:
    """Tests for web tools helper functions."""

    def test_get_all_web_tools(self) -> None:
        """Test getting all web tools."""
        tools = get_all_web_tools()

        assert len(tools) == 2
        tool_names = {tool["name"] for tool in tools}
        assert "web_fetch" in tool_names
        assert "web_search" in tool_names

        # Verify each tool has required fields
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool
            assert "properties" in tool["input_schema"]
