import os, json, urllib.request, urllib.parse, xml.etree.ElementTree as ET
from datetime import datetime, timezone
import boto3

S3_BUCKET      = os.environ["S3_BUCKET"]
PDF_QUEUE_URL  = os.environ["PDF_QUEUE_URL"]

# Supporte soit ARXIV_QUERIES (liste séparée par ";"), soit ARXIV_QUERY (fallback)
QUERIES = [q.strip() for q in os.environ.get("ARXIV_QUERIES","").split(";") if q.strip()]
if not QUERIES:
    QUERIES = [os.environ.get("ARXIV_QUERY","all:gc-ms OR all:gcms OR all:chromatography")]

MAX_RESULTS    = int(os.environ.get("ARXIV_MAX_RESULTS","25"))

s3 = boto3.client("s3")
sqs = boto3.client("sqs")

# -------------------------
# Filtre simple par mots-clés (via env var)
# -------------------------
KEYWORDS = [k.strip().lower() for k in os.environ.get("KEYWORDS","").split(";") if k.strip()]
if not KEYWORDS:
    # fallback si pas défini
    KEYWORDS = ["gc-ms", "gcms", "gas chromatography"]

def is_relevant(item):
    text = (item["title"] + " " + item["abstract"]).lower()
    return any(k in text for k in KEYWORDS)

# -------------------------
# Téléchargement depuis arXiv
# -------------------------
def fetch_arxiv(query, max_results=25):
    base = "http://export.arxiv.org/api/query"
    params = {
        "search_query": query,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": str(max_results),
    }
    url = base + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=20) as r:
        return r.read()

def parse_atom(atom_bytes):
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(atom_bytes)
    for entry in root.findall("a:entry", ns):
        eid = entry.findtext("a:id", default="", namespaces=ns) or ""
        doc_id = eid.split("/abs/")[-1] if "/abs/" in eid else eid.rsplit("/",1)[-1]
        title = (entry.findtext("a:title", default="", namespaces=ns) or "").strip()
        summary = (entry.findtext("a:summary", default="", namespaces=ns) or "").strip()
        published = entry.findtext("a:published", default="", namespaces=ns) or ""
        authors = [a.findtext("a:name", default="", namespaces=ns) for a in entry.findall("a:author", ns)]
        pdf_url = None
        for link in entry.findall("a:link", ns):
            if link.attrib.get("type") == "application/pdf":
                pdf_url = link.attrib.get("href")
                break
        yield {
            "source":"arxiv",
            "id": doc_id,
            "title": title,
            "abstract": summary,
            "authors": authors,
            "published_at": published,
            "url_pdf": pdf_url,
            "doi": None,
            "topics": []
        }

def put_raw_to_s3(item):
    now = datetime.now(timezone.utc)
    key = f"raw/arxiv/{now:%Y/%m/%d}/{item['id']}.json"
    s3.put_object(Bucket=S3_BUCKET, Key=key, Body=json.dumps(item, ensure_ascii=False).encode("utf-8"))
    return key

def send_pdf_message(item):
    if not item.get("url_pdf"):
        return
    msg = {
        "source":"arxiv",
        "id": item["id"],
        "url_pdf": item["url_pdf"],
        "metadataMin": {
            "title": item["title"],
            "published_at": item["published_at"],
            "authors": item["authors"]
        }
    }
    sqs.send_message(QueueUrl=PDF_QUEUE_URL, MessageBody=json.dumps(msg))

def lambda_handler(event, context):
    override_q = event.get("query") if isinstance(event, dict) else None
    queries = [override_q] if override_q else QUERIES

    seen_ids = set()
    count_total = 0
    count_kept = 0

    for q in queries:
        try:
            atom = fetch_arxiv(q, MAX_RESULTS)
        except Exception as e:
            print(f"[ERROR] fetch_arxiv failed for {q}: {e}")
            continue

        for item in parse_atom(atom):
            count_total += 1
            if not is_relevant(item):
                print(f"[SKIP] {item['id']} not GC-MS related")
                continue

            if item["id"] in seen_ids:
                continue
            seen_ids.add(item["id"])

            put_raw_to_s3(item)
            send_pdf_message(item)
            count_kept += 1

    return {
        "ok": True,
        "count_total": count_total,
        "count_kept": count_kept,
        "queries": queries,
        "keywords": KEYWORDS
    }
