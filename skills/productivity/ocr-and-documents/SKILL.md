---
name: ocr-and-documents
description: "Extract text from PDFs/scans (pymupdf, marker-pdf)."
version: 2.4.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [PDF, Documents, Research, Arxiv, Text-Extraction, OCR]
    related_skills: [powerpoint]
    trigger_conditions:
      - "extract text from PDF"
      - "OCR document"
      - "read PDF"
      - "scan document"
      - "extract arxiv paper"
      - "PDF to text"
      - "PDF to markdown"
      - "extract tables from PDF"
      - "split PDF"
      - "merge PDF"
      - "search PDF"
      - "document extraction"
      - "scanned PDF OCR"
---

# PDF & Document Extraction

For DOCX: use `python-docx` (parses actual document structure, far better than OCR).
For PPTX: see the `powerpoint` skill (uses `python-pptx` with full slide/notes support).
This skill covers **PDFs and scanned documents**.

## When to Use

- Extracting text from PDF files (local or remote)
- Converting scanned documents to searchable text via OCR
- Pulling tables, equations, or code blocks from PDFs
- Extracting text from Arxiv papers (abstract or full PDF)
- Splitting, merging, or searching PDFs programmatically
- Converting PDFs to markdown for downstream processing
- Batch processing multiple PDFs for text extraction
- Extracting embedded images from PDFs

## Not For

- **Word documents (.docx)** → use `python-docx` instead; it parses actual document structure
- **PowerPoint files (.pptx)** → use `powerpoint` skill instead; it uses `python-pptx`
- **Excel spreadsheets** → use `pandas.read_excel()` or `openpyxl` instead
- **HTML pages** → use `web_extract` instead
- **Images (JPG, PNG) with text** → use `tesseract` OCR directly; this skill covers PDF-based OCR only
- **EPUB ebooks** → use `pymupdf` (which supports EPUB) or `ebooklib` instead
- **Real-time document scanning** → use `tesseract` with a camera/scanner API; this skill is for files

## Step 1: Remote URL Available?

If the document has a URL, **always try `web_extract` first**:

```
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])
web_extract(urls=["https://example.com/report.pdf"])
```

This handles PDF-to-markdown conversion via Firecrawl with no local dependencies.

Only use local extraction when: the file is local, web_extract fails, or you need batch processing.

## Step 2: Choose Local Extractor

| Feature | pymupdf (~25MB) | marker-pdf (~3-5GB) |
|---------|-----------------|---------------------|
| **Text-based PDF** | ✅ | ✅ |
| **Scanned PDF (OCR)** | ❌ | ✅ (90+ languages) |
| **Tables** | ✅ (basic) | ✅ (high accuracy) |
| **Equations / LaTeX** | ❌ | ✅ |
| **Code blocks** | ❌ | ✅ |
| **Forms** | ❌ | ✅ |
| **Headers/footers removal** | ❌ | ✅ |
| **Reading order detection** | ❌ | ✅ |
| **Images extraction** | ✅ (embedded) | ✅ (with context) |
| **Images → text (OCR)** | ❌ | ✅ |
| **EPUB** | ✅ | ✅ |
| **Markdown output** | ✅ (via pymupdf4llm) | ✅ (native, higher quality) |
| **Install size** | ~25MB | ~3-5GB (PyTorch + models) |
| **Speed** | Instant | ~1-14s/page (CPU), ~0.2s/page (GPU) |

**Decision**: Use pymupdf unless you need OCR, equations, forms, or complex layout analysis.

If the user needs marker capabilities but the system lacks ~5GB free disk:
> "This document needs OCR/advanced extraction (marker-pdf), which requires ~5GB for PyTorch and models. Your system has [X]GB free. Options: free up space, provide a URL so I can use web_extract, or I can try pymupdf which works for text-based PDFs but not scanned documents or equations."

---

## pymupdf (lightweight)

```bash
pip install pymupdf pymupdf4llm
```

**Via helper script**:
```bash
python scripts/extract_pymupdf.py document.pdf              # Plain text
python scripts/extract_pymupdf.py document.pdf --markdown    # Markdown
python scripts/extract_pymupdf.py document.pdf --tables      # Tables
python scripts/extract_pymupdf.py document.pdf --images out/ # Extract images
python scripts/extract_pymupdf.py document.pdf --metadata    # Title, author, pages
python scripts/extract_pymupdf.py document.pdf --pages 0-4   # Specific pages
```

**Inline**:
```bash
python3 -c "
import pymupdf
doc = pymupdf.open('document.pdf')
for page in doc:
    print(page.get_text())
"
```

---

## marker-pdf (high-quality OCR)

```bash
# Check disk space first
python scripts/extract_marker.py --check

pip install marker-pdf
```

**Via helper script**:
```bash
python scripts/extract_marker.py document.pdf                # Markdown
python scripts/extract_marker.py document.pdf --json         # JSON with metadata
python scripts/extract_marker.py document.pdf --output_dir out/  # Save images
python scripts/extract_marker.py scanned.pdf                 # Scanned PDF (OCR)
python scripts/extract_marker.py document.pdf --use_llm      # LLM-boosted accuracy
```

**CLI** (installed with marker-pdf):
```bash
marker_single document.pdf --output_dir ./output
marker /path/to/folder --workers 4    # Batch
```

---

## Arxiv Papers

```
# Abstract only (fast)
web_extract(urls=["https://arxiv.org/abs/2402.03300"])

# Full paper
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])

# Search
web_search(query="arxiv GRPO reinforcement learning 2026")
```

## Split, Merge & Search

pymupdf handles these natively — use `execute_code` or inline Python:

```python
# Split: extract pages 1-5 to a new PDF
import pymupdf
doc = pymupdf.open("report.pdf")
new = pymupdf.open()
for i in range(5):
    new.insert_pdf(doc, from_page=i, to_page=i)
new.save("pages_1-5.pdf")
```

```python
# Merge multiple PDFs
import pymupdf
result = pymupdf.open()
for path in ["a.pdf", "b.pdf", "c.pdf"]:
    result.insert_pdf(pymupdf.open(path))
result.save("merged.pdf")
```

```python
# Search for text across all pages
import pymupdf
doc = pymupdf.open("report.pdf")
for i, page in enumerate(doc):
    results = page.search_for("revenue")
    if results:
        print(f"Page {i+1}: {len(results)} match(es)")
        print(page.get_text("text"))
```

No extra dependencies needed — pymupdf covers split, merge, search, and text extraction in one package.

## Pitfalls

1. **`web_extract` fails on PDF URLs behind authentication** — Firecrawl can't access PDFs behind login walls or paywalls. If you get a 403 or empty result, download the file locally first: `curl -o paper.pdf "URL"` (with authentication headers if needed), then use pymupdf or marker-pdf.

2. **pymupdf4llm not installed after `pip install pymupdf`** — `pymupdf4llm` is a separate package that provides the markdown conversion. Install both: `pip install pymupdf pymupdf4llm`. Without `pymupdf4llm`, `page.get_text()` works but markdown conversion won't.

3. **marker-pdf downloads ~2.5GB of models on first run** — The first invocation of marker-pdf downloads PyTorch, detection models, and OCR models to `~/.cache/huggingface/`. This can take 10-30 minutes depending on bandwidth. Run `python scripts/extract_marker.py --check` to verify disk space before starting.

4. **Scanned PDFs return empty/garbled text with pymupdf** — pymupdf cannot OCR scanned images. If `page.get_text()` returns empty strings or garbled characters, the PDF is likely scanned. Switch to marker-pdf which includes Tesseract OCR support for 90+ languages.

5. **marker-pdf OOM on large PDFs (>100 pages)** — marker-pdf loads the entire PDF into memory for layout analysis. For large documents, process in chunks: split the PDF with pymupdf first (`new.insert_pdf(doc, from_page=i, to_page=i+9)` for 10-page chunks), then run marker-pdf on each chunk. Alternatively, use pymupdf for text-based pages and marker-pdf only for pages with images/equations.

6. **`marker_single` command not found after pip install** — The CLI entry point may not be on PATH. Use the full path: `python -m marker.single document.pdf --output_dir ./output` or the helper script: `python scripts/extract_marker.py document.pdf`.

7. **Table extraction from pymupdf returns misaligned cells** — pymupdf's table detection works best on PDFs with explicit table structures (borders, gridlines). For borderless tables or complex layouts, use marker-pdf which has better table detection. If you must use pymupdf, try `page.find_tables()` which returns a `TableFinder` object with row/column detection.

8. **Arxiv PDF extraction returns the wrong paper version** — Arxiv PDFs have version numbers (v1, v2, etc.). The `/pdf/` URL returns the latest version; `/pdf/2402.03300v1` returns a specific version. If the content doesn't match expectations, check the paper's version history on the abstract page.

9. **`pymupdf.open()` fails with "no such file" on paths with spaces** — pymupdf handles paths with spaces correctly, but shell quoting may strip them. Use Python's `pathlib`: `from pathlib import Path; doc = pymupdf.open(Path("my document.pdf"))`.

10. **Merge PDFs with different page sizes produces inconsistent output** — `insert_pdf` preserves each source PDF's page dimensions, so a merged document may have mixed page sizes. To normalize, set `new = pymupdf.open()` with a fixed page size: `new.new_page(width=612, height=792)` before inserting, though this may clip content.

11. **marker-pdf `--use_llm` flag requires an API key** — The LLM-boosted accuracy mode uses an external LLM (default: OpenAI). Set `OPENAI_API_KEY` in the environment. Without it, the flag is silently ignored and marker-pdf falls back to standard extraction. To use a local LLM, configure the marker-pdf settings file.

12. **`web_extract` on arXiv abstracts returns the HTML page, not just the abstract** — The `/abs/` URL returns the full page including references, citations, and sidebar. For clean abstract-only extraction, append `?format=text` or use the arXiv API: `http://export.arxiv.org/api/query?id_list=2402.03300`.

## Notes

- `web_extract` is always first choice for URLs
- pymupdf is the safe default — instant, no models, works everywhere
- marker-pdf is for OCR, scanned docs, equations, complex layouts — install only when needed
- Both helper scripts accept `--help` for full usage
- marker-pdf downloads ~2.5GB of models to `~/.cache/huggingface/` on first use
- For Word docs: `pip install python-docx` (better than OCR — parses actual structure)
- For PowerPoint: see the `powerpoint` skill (uses python-pptx)