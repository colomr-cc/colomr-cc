#!/usr/bin/env python3
"""Update README with latest Dev.to posts.

Fetches recent published posts from Dev.to API and updates the README.md
with a list of the latest posts as clickable links.
"""

import os
import re
from pathlib import Path

import requests

DEVTO_API_KEY = os.getenv("DEVTO_API_KEY", "")
DEVTO_USERNAME = "colomr"
DEVTO_BASE_URL = "https://dev.to/api"
REPO_ROOT = Path(__file__).parent.parent


def fetch_user_posts(username: str, api_key: str = "") -> list[dict]:
    """Fetch published posts for a user from Dev.to API.

    Args:
        username: Dev.to username
        api_key: Optional API key for higher rate limits

    Returns:
        List of post dictionaries from Dev.to API
    """
    url = f"{DEVTO_BASE_URL}/articles"
    headers = {}
    if api_key:
        headers["api-key"] = api_key

    params = {
        "username": username,
        "per_page": 10,
        "state": "published",
        "top": 6,
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    return response.json()


def format_posts_markdown(posts: list[dict], count: int = 6) -> str:
    """Format posts as markdown list with clickable links.

    Args:
        posts: List of post dictionaries from Dev.to API
        count: Maximum number of posts to include

    Returns:
        Markdown formatted string with post links
    """
    limited_posts = posts[:count]

    if not limited_posts:
        return "No posts available yet."

    lines = []
    for post in limited_posts:
        title = post.get("title", "Untitled")
        url = post.get("url", "")
        lines.append(f"- [{title}]({url})")

    return "\n".join(lines)


def update_readme(readme_path: str, new_posts_content: str) -> bool:
    """Update README with new posts section.

    Replaces the content between markers:
    <!-- START_BLOG_POST_LIST --> and <!-- END_BLOG_POST_LIST -->

    Args:
        readme_path: Path to README.md file
        new_posts_content: New markdown content for posts section

    Returns:
        True if file was modified, False if no changes
    """
    path = Path(readme_path)

    if not path.exists():
        raise FileNotFoundError(f"README not found at {readme_path}")

    content = path.read_text(encoding="utf-8")

    pattern = r"(<!-- START_BLOG_POST_LIST -->)(.*?)(<!-- END_BLOG_POST_LIST -->)"
    replacement = f"\\1\n{new_posts_content}\n\\3"

    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    if new_content == content:
        return False

    path.write_text(new_content, encoding="utf-8")
    return True


def main():
    """Main routine to fetch posts and update README."""
    try:
        posts = fetch_user_posts(DEVTO_USERNAME, DEVTO_API_KEY)
        print(f"Fetched {len(posts)} posts from Dev.to")

        posts_markdown = format_posts_markdown(posts, count=6)
        readme_path = REPO_ROOT / "README.md"

        if update_readme(str(readme_path), posts_markdown):
            print("README updated with latest posts")
            return 0
        else:
            print("No changes needed in README")
            return 0

    except Exception as e:
        print(f"Error: {e}", file=__import__("sys").stderr)
        return 1


if __name__ == "__main__":
    exit(main())
