# Bibliographic Watch Tool (AWS-based)

🚧 **Work in Progress** 🚧  
This repository contains the initial skeleton of a **bibliographic watch tool** I am developing as part of my learning journey in **AWS Data Engineering**.  
The goal is to build a cloud-native application to automatically process, store, and analyze scientific articles.

---

## 📌 Objectives
- Explore **AWS services** (S3, DynamoDB, Lambda, Textract, Glue, Athena, QuickSight, …).  
- Learn how to **design scalable data pipelines** for text-heavy datasets (PDFs, scientific papers).  
- Apply cloud and AI tools to a **real-world use case in scientific research**.  
- Showcase my progress as part of my **portfolio** in data engineering and cloud computing.  

---

## 🗂️ Current Status
- ✅ Project skeleton created  
- ✅ First Lambda implemented: **arxiv_to_s3** (ingest metadata from arXiv)  
- ⏳ Next steps:  
  - Store PDFs in S3  
  - Extract text (Textract + PyPDF2 fallback)  
  - Structure metadata in DynamoDB  
  - Query with Athena  
  - Build dashboards in QuickSight  

---

## 🛠️ Tech Stack
- **AWS**: S3, Lambda, DynamoDB, SQS, Textract, Glue, Athena  
- **Python**: data processing and orchestration  
- **GitHub**: version control, project tracking  

---

## 📅 Roadmap
- [x] Lambda to fetch and filter arXiv metadata  
- [ ] Store PDFs in S3  
- [ ] Text extraction (Textract + PyPDF2 fallback)  
- [ ] DynamoDB integration  
- [ ] Athena queries  
- [ ] QuickSight dashboards  
- [ ] Automated summaries with LLMs (ChatGPT / Bedrock)  

---

## 🖥️ Lambda Functions

### arxiv_to_s3
Fetches recent articles from the arXiv API, filters them by keywords, and ingests metadata into S3.  
Also sends PDF download instructions to SQS for downstream processing.

**Environment variables:**
- `S3_BUCKET`: Target bucket for raw metadata  
- `PDF_QUEUE_URL`: SQS queue for PDF processing  
- `ARXIV_QUERIES`: List of queries separated by `;` (optional)  
- `ARXIV_QUERY`: Fallback single query (if `ARXIV_QUERIES` not set)  
- `ARXIV_MAX_RESULTS`: Max number of results (default: 25)  
- `KEYWORDS_ANALYTICAL`: Keywords for analytical chemistry (e.g. `gc-ms;lc-ms;proteomics;metabolomics`)  
- `KEYWORDS_APPLICATIONS`: Keywords for application domains (e.g. `biomarkers;clinical chemistry;food analysis`)  
- `KEYWORDS_CLOUD`: Keywords for cloud & AI (e.g. `aws;azure;machine learning;neural networks`)  

**Sample event JSON:**
```json
{
  "query": "all:chromatography AND all:deep learning"
}
```
---

### fetch_pdf
Downloads article PDFs from arXiv (based on messages sent to SQS by `arxiv_to_s3`) and stores them in S3.  
Once stored, it sends a message to another SQS queue (`TEXT_QUEUE_URL`) for downstream text extraction.

**Workflow:**
1. Reads messages from `PDF_QUEUE_URL` containing `id`, `url_pdf`, and minimal metadata.  
2. Downloads the PDF file from arXiv.  
3. Stores it in S3 under `pdf/arxiv/<paper_id>.pdf`.  
4. Sends a new message to `TEXT_QUEUE_URL` with the S3 key for the PDF.  

**Environment variables:**
- `S3_BUCKET`: Target bucket where PDFs are stored  
- `TEXT_QUEUE_URL`: SQS queue used to send messages for text extraction  

**Sample SQS message input:**
```json
{
  "id": "2502.13183v1",
  "url_pdf": "https://arxiv.org/pdf/2502.13183v1.pdf",
  "metadataMin": {
    "title": "Generative autoencoders for GC-IMS data",
    "authors": ["Author One", "Author Two"],
    "published_at": "2025-02-13T00:00:00Z"
  }
}
```
