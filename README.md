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
- Project skeleton created.  
- Basic AWS integration tested (file upload, text extraction).  
- Next steps:  
  - Structure the data in DynamoDB.  
  - Implement metadata extraction.  
  - Create dashboards for bibliographic insights.  

---

## 🛠️ Tech Stack
- **AWS**: S3, Lambda, DynamoDB, Textract (with fallback to PyPDF2), Glue, Athena  
- **Python**: data processing and orchestration  
- **GitHub**: version control, project tracking  

---

## 📅 Roadmap
- [ ] Upload and store scientific articles (PDF → S3)  
- [ ] Text extraction with Textract (fallback PyPDF2)  
- [ ] Store structured data in DynamoDB  
- [ ] Query with Athena + Glue Catalog  
- [ ] Visualization with QuickSight  
- [ ] Automated summaries with LLMs (ChatGPT / Bedrock)  

---

## 🙋 About Me
I am an **Application Engineer in Analytical Chemistry** (GC/GC-MS) exploring **cloud computing and AI** to build practical tools for data analysis and automation.  
This project is part of my path toward the **AWS Data Engineer – Associate certification** and my broader portfolio of applied AI/cloud solutions.

---

## ⚠️ Disclaimer
This is an **educational project**. Code is experimental and subject to change.  
Please do not use in production without proper review and testing.
