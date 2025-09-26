import os
import json
from datetime import datetime, timezone
from typing import Dict, List, Any

import boto3
from botocore.exceptions import ClientError

try:
    from openai import OpenAI
except ImportError as exc:  # pragma: no cover - guard for packaging issues
    raise RuntimeError("openai package must be installed for the review lambda") from exc

# --- Environment configuration
S3_BUCKET = os.environ["S3_BUCKET"]
DDB_TABLE = os.environ["DDB_TABLE"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
MAX_ARTICLES = int(os.environ.get("MAX_REVIEW_ARTICLES", "5"))
REVIEW_PREFIX = os.environ.get("REVIEW_PREFIX", "reviews")
TEMPERATURE = float(os.environ.get("OPENAI_TEMPERATURE", "0.3"))

s3 = boto3.client("s3")
ddb = boto3.resource("dynamodb")
table = ddb.Table(DDB_TABLE)
client = OpenAI(api_key=OPENAI_API_KEY)


# --- Data access helpers

def _fetch_articles(paper_ids: List[str], limit: int) -> List[Dict[str, Any]]:
    """Retrieve article metadata and text pointers from DynamoDB."""
    if paper_ids:
        keys = [{"id": pid} for pid in paper_ids]
        response = ddb.batch_get_item(RequestItems={DDB_TABLE: {"Keys": keys}})
        items = response.get("Responses", {}).get(DDB_TABLE, [])
    else:
        response = table.scan()
        items = response.get("Items", [])
        # Handle pagination if needed
        while "LastEvaluatedKey" in response and len(items) < limit:
            response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            items.extend(response.get("Items", []))
    # Sort by publication date when available (descending)
    def _sort_key(item: Dict[str, Any]):
        published = item.get("published_at")
        return published or ""

    items.sort(key=_sort_key, reverse=True)
    return items[:limit]


def _load_text(item: Dict[str, Any]) -> str:
    """Retrieve full text of an article from S3, with DynamoDB fallback."""
    s3_key = item.get("s3_text_key")
    if not s3_key:
        return item.get("extracted_text", "")

    try:
        obj = s3.get_object(Bucket=S3_BUCKET, Key=s3_key)
    except ClientError as exc:
        print(f"[WARN] Unable to fetch text from S3 for {item.get('id')}: {exc}")
        return item.get("extracted_text", "")

    body = obj["Body"].read()
    try:
        return body.decode("utf-8")
    except UnicodeDecodeError:
        return body.decode("utf-8", errors="replace")


def _build_prompt(articles: List[Dict[str, Any]]) -> str:
    blocks = []
    for art in articles:
        text = _load_text(art)
        snippet = text[:4000]
        authors = ", ".join(art.get("authors", [])) or "Unknown authors"
        published = art.get("published_at") or "Unknown date"
        title = art.get("title") or art.get("id")
        blocks.append(
            f"Title: {title}\n"
            f"Authors: {authors}\n"
            f"Published: {published}\n"
            f"Content snippet:\n{snippet}\n"
        )
    return (
        "You are a scientific assistant helping to summarise recent research articles. "
        "Write a concise literature review in French (≤ 600 mots) that: \n"
        "- Synthétise les contributions majeures de chaque article.\n"
        "- Compare les approches et met en évidence les points communs ou divergents.\n"
        "- Liste les pistes d'application potentielles et les limites identifiées.\n"
        "- Termine par des recommandations pour approfondir la veille scientifique.\n\n"
        "Voici les articles à analyser:\n\n"
        + "\n\n".join(blocks)
    )


def _call_openai(prompt: str) -> str:
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=TEMPERATURE,
        messages=[
            {
                "role": "system",
                "content": "Tu es un assistant scientifique qui rédige des synthèses de veille bibliographique.",
            },
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content.strip()


def _store_review(review_text: str, metadata: Dict[str, Any]) -> str:
    now = datetime.now(timezone.utc)
    key = f"{REVIEW_PREFIX}/{now:%Y/%m/%d}/review_{now:%H%M%S}.md"
    payload = {
        "generated_at": now.isoformat(),
        "model": OPENAI_MODEL,
        "metadata": metadata,
        "review": review_text,
    }
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"),
        ContentType="application/json",
    )
    return key


def lambda_handler(event, context):
    event = event or {}
    requested_ids = event.get("paper_ids") or []
    limit = int(event.get("limit") or MAX_ARTICLES)

    articles = _fetch_articles(requested_ids, limit)
    if not articles:
        return {"ok": False, "message": "No articles available for review"}

    prompt = _build_prompt(articles)
    review_text = _call_openai(prompt)

    output_key = _store_review(
        review_text,
        metadata={
            "paper_ids": [art.get("id") for art in articles],
            "requested_ids": requested_ids,
            "limit": limit,
        },
    )

    return {
        "ok": True,
        "paper_count": len(articles),
        "s3_review_key": output_key,
        "review": review_text,
    }
