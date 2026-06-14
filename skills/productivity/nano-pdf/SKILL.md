---
name: nano-pdf
description: "Edit PDF text/typos/titles via nano-pdf CLI (NL prompts)."
version: 1.1.0
author: community
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [PDF, Documents, Editing, NLP, Productivity]
    homepage: https://pypi.org/project/nano-pdf/
    trigger_conditions:
      - "edit this PDF"
      - "fix a typo in the PDF"
      - "change the title in the PDF"
      - "update text in a PDF"
      - "nano-pdf"
      - "PDF text edit"
      - "correct the PDF"
      - "revise the PDF"
      - "change a name in the PDF"
      - "update the date in the PDF"
      - "fix the subtitle"
---

# nano-pdf

Edit PDFs using natural-language instructions. Point it at a page and describe what to change.

## When to Use

- User wants to fix a typo or wrong name in an existing PDF
- User needs to update a title, date, or subtitle on a specific page
- User needs to change a client name, project name, or address in a contract/proposal
- User wants to revise text on one page without re-exporting from the source tool
- Quick corrections where regenerating the whole PDF from source is expensive
- User says "edit this PDF" or "change X in the PDF"

## Not For

- **Creating a PDF from scratch** → nano-pdf edits existing PDFs; use `powerpoint`, `weasyprint`, or `pdflatex` to generate new ones
- **Extracting text from PDFs (OCR)** → use `ocr-and-documents`, `marker-pdf`, or `pymupdf` for extraction
- **Merging, splitting, or reordering pages** → use `pdftk`, `pypdf`, or `qpdf` for structural PDF operations
- **Editing scanned/image-based PDFs** → nano-pdf works on text layers; scanned PDFs have no text layer. Use `ocr-and-documents` first to OCR, then edit
- **Complex layout changes (move images, change columns)** → nano-pdf handles text replacement, not layout reflow. For major changes, re-export from source
- **Batch editing hundreds of PDFs** → nano-pdf is interactive/single-file; wrap in a shell loop for batch, but consider if a template engine (Jinja2 + LaTeX) is the right approach
- **Digital signatures or form filling** → use `pypdf` for form fields, `openssl`/`gpg` for signatures; nano-pdf doesn't handle either

## Prerequisites

```bash
# Install with uv (recommended — already available in Hermes)
uv pip install nano-pdf

# Or with pip
pip install nano-pdf
```

## Usage

```bash
nano-pdf edit <file.pdf> <page_number> "<instruction>"
```

## Examples

```bash
# Change a title on page 1
nano-pdf edit deck.pdf 1 "Change the title to 'Q3 Results' and fix the typo in the subtitle"

# Update a date on a specific page
nano-pdf edit report.pdf 3 "Update the date from January to February 2026"

# Fix content
nano-pdf edit contract.pdf 2 "Change the client name from 'Acme Corp' to 'Acme Industries'"
```

## Pitfalls

1. **Page number off by one** — nano-pdf may use 0-based or 1-based page numbering depending on version. If the edit hits the wrong page, retry with `page_number ± 1`. Fix: always verify the output PDF after editing; if wrong, adjust and re-run.

2. **LLM-based editing is non-deterministic** — nano-pdf uses an LLM under the hood, so the same instruction may produce slightly different results on each run. Fix: if the first attempt doesn't look right, re-run with a more specific instruction. For critical edits, verify visually with `vision_analyze`.

3. **API key not configured** — nano-pdf requires an API key (OpenAI or compatible). If you get auth errors, check `nano-pdf --help` for the config file location and set the key. Fix: `nano-pdf config set api-key <key>` or set the env var it documents.

4. **Scanned PDFs have no text layer** — If the PDF is image-based (scanned document), nano-pdf will fail silently or produce garbage. Fix: run OCR first with `ocr-and-documents` or `marker-pdf` to create a text layer, then edit.

5. **Complex instructions produce unexpected layout changes** — "Change the title and make it bigger" may cause the LLM to reflow the entire page. Fix: keep instructions specific and minimal — "Change the title text to X" is safer than "make the title better."

6. **Output PDF is larger than expected** — The LLM may embed fonts or resources that inflate the file. Fix: if file size matters, re-compress with `ghostscript` or `qpdf` after editing.

7. **Multi-page edits require multiple invocations** — nano-pdf edits one page per invocation. If the user wants to change a name that appears on 10 pages, you need 10 runs. Fix: script it with a shell loop, or suggest re-exporting from source if the change is widespread.

8. **Tool not installed** — `command not found: nano-pdf`. Fix: `uv pip install nano-pdf` (recommended) or `pip install nano-pdf`.
