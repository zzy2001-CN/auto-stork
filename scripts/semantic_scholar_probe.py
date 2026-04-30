from __future__ import annotations

import json
import sys

import requests


API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"


def main() -> int:
    params = {
        "query": "ACL injury",
        "limit": "5",
        "fields": "title,year,venue,url,externalIds",
    }

    try:
        response = requests.get(API_URL, params=params, timeout=30)
    except requests.RequestException as exc:
        print("Request failed.")
        print(f"Error: {exc}")
        return 1

    print(f"Request URL: {response.url}")
    print(f"Status code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    print()

    if response.status_code != 200:
        print("Response body:")
        print(response.text)
        return 1

    payload = response.json()
    print(f"Total returned: {len(payload.get('data', []))}")
    print()

    for index, paper in enumerate(payload.get("data", []), start=1):
        print(f"{index}. {paper.get('title', '<no title>')}")
        print(f"   Year: {paper.get('year')}")
        print(f"   Venue: {paper.get('venue')}")
        print(f"   URL: {paper.get('url')}")
        doi = (paper.get("externalIds") or {}).get("DOI")
        if doi:
            print(f"   DOI: {doi}")
        print()

    print("Raw JSON preview:")
    print(json.dumps(payload, ensure_ascii=False, indent=2)[:2000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
