"""Unit tests for update_posts module."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.update_posts import (
    fetch_user_posts,
    format_posts_markdown,
    update_readme,
)


@pytest.fixture
def mock_posts():
    """Fixture with sample Dev.to posts."""
    return [
        {
            "id": 1,
            "title": "Getting Started with Python",
            "url": "https://dev.to/colomr/getting-started-with-python",
            "published_at": "2024-08-01T10:00:00Z",
        },
        {
            "id": 2,
            "title": "Advanced Django Patterns",
            "url": "https://dev.to/colomr/advanced-django-patterns",
            "published_at": "2024-07-28T14:30:00Z",
        },
        {
            "id": 3,
            "title": "Testing Best Practices",
            "url": "https://dev.to/colomr/testing-best-practices",
            "published_at": "2024-07-15T09:15:00Z",
        },
    ]


class TestFetchUserPosts:
    """Tests for fetch_user_posts function."""

    @patch("scripts.update_posts.requests.get")
    def test_fetch_user_posts_success(self, mock_get, mock_posts):
        """Test successful fetch of user posts."""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_posts
        mock_get.return_value = mock_response

        posts = fetch_user_posts("colomr")

        assert len(posts) == 3
        assert posts[0]["title"] == "Getting Started with Python"
        mock_get.assert_called_once()

    @patch("scripts.update_posts.requests.get")
    def test_fetch_user_posts_with_api_key(self, mock_get, mock_posts):
        """Test fetch with API key includes header."""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_posts
        mock_get.return_value = mock_response

        fetch_user_posts("colomr", api_key="test-key-123")

        call_kwargs = mock_get.call_args[1]
        assert call_kwargs["headers"]["api-key"] == "test-key-123"

    @patch("scripts.update_posts.requests.get")
    def test_fetch_user_posts_empty_result(self, mock_get):
        """Test fetch when no posts are returned."""
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        posts = fetch_user_posts("colomr")

        assert len(posts) == 0

    @patch("scripts.update_posts.requests.get")
    def test_fetch_user_posts_api_error(self, mock_get):
        """Test fetch handles API errors."""
        mock_get.side_effect = Exception("API Error")

        with pytest.raises(Exception):
            fetch_user_posts("colomr")


class TestFormatPostsMarkdown:
    """Tests for format_posts_markdown function."""

    def test_format_posts_basic(self, mock_posts):
        """Test basic markdown formatting."""
        result = format_posts_markdown(mock_posts[:2])

        assert "[Getting Started with Python]" in result
        assert "https://dev.to/colomr/getting-started-with-python" in result
        assert "[Advanced Django Patterns]" in result
        assert "https://dev.to/colomr/advanced-django-patterns" in result

    def test_format_posts_default_count(self, mock_posts):
        """Test format limits to default count of 6."""
        result = format_posts_markdown(mock_posts)

        lines = result.strip().split("\n")
        assert len(lines) <= 6

    def test_format_posts_custom_count(self, mock_posts):
        """Test format with custom count limit."""
        result = format_posts_markdown(mock_posts, count=2)

        lines = result.strip().split("\n")
        assert len(lines) == 2

    def test_format_posts_empty_list(self):
        """Test format handles empty post list."""
        result = format_posts_markdown([])

        assert result == "No posts available yet."

    def test_format_posts_missing_fields(self):
        """Test format handles posts with missing fields."""
        posts = [
            {"title": "Title Only"},
            {"url": "https://example.com"},
        ]

        result = format_posts_markdown(posts)

        assert "[Title Only]()" in result
        assert "[Untitled](https://example.com)" in result

    def test_format_posts_markdown_syntax(self, mock_posts):
        """Test output uses proper markdown list syntax."""
        result = format_posts_markdown(mock_posts[:1])

        assert result.startswith("- [")
        assert "](" in result
        assert ")" in result


class TestUpdateReadme:
    """Tests for update_readme function."""

    def test_update_readme_replaces_content(self):
        """Test that readme content is updated between markers."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(
                "# Title\n\n<!-- START_BLOG_POST_LIST -->\nOld content\n<!-- END_BLOG_POST_LIST -->\n\nFooter"
            )
            f.flush()

            try:
                result = update_readme(f.name, "- [New Post](https://example.com)")

                assert result is True

                updated = Path(f.name).read_text()
                assert "- [New Post](https://example.com)" in updated
                assert "Old content" not in updated
                assert "# Title" in updated
                assert "Footer" in updated

            finally:
                Path(f.name).unlink()

    def test_update_readme_no_changes_needed(self):
        """Test update returns False when content is identical."""
        content = "# Title\n\n<!-- START_BLOG_POST_LIST -->\nContent\n<!-- END_BLOG_POST_LIST -->\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()

            try:
                result = update_readme(f.name, "Content")

                assert result is False

            finally:
                Path(f.name).unlink()

    def test_update_readme_file_not_found(self):
        """Test update raises error when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            update_readme("/nonexistent/path/README.md", "content")

    def test_update_readme_creates_markers_if_missing(self):
        """Test handling of README without markers."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Title\n\nNo markers here\n")
            f.flush()

            try:
                result = update_readme(f.name, "- [Post](url)")

                assert result is False

            finally:
                Path(f.name).unlink()
