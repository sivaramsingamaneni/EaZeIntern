from typing import Dict, Any
import httpx
import asyncio

GITHUB_API_URL = "https://api.github.com"

async def analyze_github(github_url: str) -> Dict[str, Any]:
    """
    Analyzes a GitHub profile via the public API.
    """
    username = github_url.rstrip("/").split("/")[-1]
    
    # Simple unauthenticated request (rate limits apply)
    # In prod, we should use a token
    headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "InternshipParser/1.0"}

    async with httpx.AsyncClient() as client:
        try:
            # 1. Get User Details
            user_resp = await client.get(f"{GITHUB_API_URL}/users/{username}", headers=headers)
            if user_resp.status_code != 200:
                print(f"Failed to fetch user {username}: {user_resp.status_code}")
                return {"error": "User not found or API limit exceeded"}
            
            user_data = user_resp.json()
            
            # 2. Get Repositories
            repos_resp = await client.get(f"{GITHUB_API_URL}/users/{username}/repos?per_page=100", headers=headers)
            repos = repos_resp.json() if repos_resp.status_code == 200 else []

            # 3. Aggregate Data
            total_stars = 0
            languages = {}
            last_activity = "N/A"
            
            sorted_repos = sorted(repos, key=lambda x: x.get("pushed_at", ""), reverse=True)
            if sorted_repos:
                last_activity = sorted_repos[0].get("pushed_at", "N/A").split("T")[0]

            for repo in repos:
                total_stars += repo.get("stargazers_count", 0)
                lang = repo.get("language")
                if lang:
                    languages[lang] = languages.get(lang, 0) + 1
            
            # Sort languages by usage
            sorted_languages = dict(sorted(languages.items(), key=lambda item: item[1], reverse=True))

            return {
                "username": username,
                "avatar_url": user_data.get("avatar_url"),
                "bio": user_data.get("bio"),
                "public_repos": user_data.get("public_repos"),
                "followers": user_data.get("followers"),
                "total_stars": total_stars,
                "top_languages": sorted_languages,
                "last_activity": last_activity
            }

        except Exception as e:
            print(f"Error accessing GitHub API: {e}")
            return {"error": str(e)}
