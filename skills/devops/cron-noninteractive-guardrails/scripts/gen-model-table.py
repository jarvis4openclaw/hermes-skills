#!/usr/bin/env python3
"""Generate OpenRouter free models table image with tool calling + latency."""

import os
import sys
from datetime import datetime

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    os.system(f"{sys.executable} -m pip install Pillow -q")
    from PIL import Image, ImageDraw, ImageFont

# Data: (model, context, reasoning, tool_calling, latency_seconds)
# Update this table from the tracker JSON or fresh API data
models = [
    ("openrouter/owl-alpha",                              1048756, True,  True,  2.0),
    ("deepseek/deepseek-v4-flash:free",                   1048576, False, True,  2.4),
    ("inclusionai/ring-2.6-1t:free",                       262144, True,  True,  1.1),
    ("google/gemma-4-26b-a4b-it:free",                    262144, True,  True,  1.4),
    ("google/gemma-4-31b-it:free",                        262144, True,  True,  None),
    ("arcee-ai/trinity-large-thinking:free",               262144, True,  True,  0.8),
    ("nvidia/nemotron-3-super-120b-a12b:free",             262144, False, True,  2.5),
    ("qwen/qwen3-next-80b-a3b-instruct:free",              262144, True,  True,  None),
    ("qwen/qwen3-coder:free",                              262000, True,  True,  None),
    ("nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free", 256000, True,  True,  11.5),
    ("nvidia/nemotron-3-nano-30b-a3b:free",                256000, False, True,  0.9),
]

# Style
BG          = (15, 15, 25)
HEADER_BG   = (30, 30, 50)
ROW_BG_1    = (22, 22, 38)
ROW_BG_2    = (28, 28, 45)
ACCENT      = (100, 180, 255)
GREEN       = (80, 220, 120)
RED         = (255, 100, 100)
YELLOW      = (255, 200, 80)
WHITE       = (230, 230, 240)
DIM         = (140, 140, 160)
WARN_BG     = (45, 30, 10)

HEADERS     = ["Model", "Context", "Reasoning", "Tools", "Latency"]
COL_WIDTHS  = [330, 100, 90, 70, 90]
ROW_HEIGHT  = 44
HEADER_H    = 50
TITLE_H     = 64
PAD         = 20
FOOTER_H    = 52

total_w = sum(COL_WIDTHS) + PAD * 2
total_h = TITLE_H + HEADER_H + ROW_HEIGHT * len(models) + FOOTER_H + PAD * 2

img = Image.new("RGB", (total_w, total_h), BG)
draw = ImageDraw.Draw(img)

# Fonts
font_paths = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]
bold_paths = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]

font = font_bold = font_sm = None
for p in font_paths:
    if os.path.exists(p):
        font = ImageFont.truetype(p, 14)
        font_sm = ImageFont.truetype(p, 11)
        break
for p in bold_paths:
    if os.path.exists(p):
        font_bold = ImageFont.truetype(p, 15)
        break

if not font:
    font = font_bold = font_sm = ImageFont.load_default()
if not font_bold:
    font_bold = font

# Title bar
draw.rectangle([0, 0, total_w, TITLE_H], fill=(20, 20, 35))
draw.text((PAD, 14), "OpenRouter — Top-Tier Free Models", fill=ACCENT, font=font_bold)
draw.text((PAD, 36), f"{len(models)} models  •  >=200k context  •  frontier labs  •  all support tool calling", fill=DIM, font=font_sm)

# Header row
y = TITLE_H + PAD
draw.rectangle([PAD, y, total_w - PAD, y + HEADER_H], fill=HEADER_BG)
x = PAD + 10
for hdr, w in zip(HEADERS, COL_WIDTHS):
    draw.text((x, y + 16), hdr, fill=ACCENT, font=font_bold)
    x += w

# Data rows
y = TITLE_H + PAD + HEADER_H
for idx, (model, ctx, reasoning, tools, latency) in enumerate(models):
    row_bg = ROW_BG_1 if idx % 2 == 0 else ROW_BG_2
    if latency is None:
        row_bg = WARN_BG

    draw.rectangle([PAD, y, total_w - PAD, y + ROW_HEIGHT], fill=row_bg)
    draw.line([PAD, y + ROW_HEIGHT - 1, total_w - PAD, y + ROW_HEIGHT - 1], fill=(40, 40, 60))

    x = PAD + 10

    # Model name - truncate with ellipsis if too long
    display = model
    bbox = draw.textbbox((0, 0), display, font=font)
    text_w = bbox[2] - bbox[0]
    max_w = COL_WIDTHS[0] - 20
    while text_w > max_w and len(display) > 10:
        display = display[:-4] + "..."
        bbox = draw.textbbox((0, 0), display, font=font)
        text_w = bbox[2] - bbox[0]
    draw.text((x, y + 14), display, fill=WHITE, font=font)
    x += COL_WIDTHS[0]

    # Context
    if ctx >= 1000000:
        ctx_str = f"{ctx/1000000:.1f}M"
    else:
        ctx_str = f"{ctx//1000}k"
    draw.text((x, y + 14), ctx_str, fill=WHITE, font=font)
    x += COL_WIDTHS[1]

    # Reasoning
    if reasoning:
        draw.text((x, y + 14), "Yes", fill=GREEN, font=font)
    else:
        draw.text((x, y + 14), "No", fill=DIM, font=font)
    x += COL_WIDTHS[2]

    # Tools
    if tools:
        draw.text((x, y + 14), "Yes", fill=GREEN, font=font)
    else:
        draw.text((x, y + 14), "No", fill=DIM, font=font)
    x += COL_WIDTHS[3]

    # Latency
    if latency is not None:
        if latency < 1.0:
            lat_color = GREEN
        elif latency < 2.0:
            lat_color = YELLOW
        else:
            lat_color = RED
        draw.text((x, y + 14), f"{latency:.1f}s", fill=lat_color, font=font)
    else:
        draw.text((x, y + 14), "N/A", fill=DIM, font=font)

    y += ROW_HEIGHT

# Footer
y = TITLE_H + PAD + HEADER_H + ROW_HEIGHT * len(models) + 10
draw.text((PAD, y), "Latency = ping response time (lower=better)  <1s green  1-2s yellow  >2s red  N/A=provider error/rate-limited", fill=DIM, font=font_sm)
draw.text((PAD, y + 16), "All models verified to support OpenAI-style tool/function calling via OpenRouter", fill=DIM, font=font_sm)
draw.text((PAD, y + 32), f"Generated by Hermes Agent  *  Data from OpenRouter API  *  {datetime.now().strftime('%B %Y')}", fill=DIM, font=font_sm)

# Border
draw.rectangle([0, 0, total_w - 1, total_h - 1], outline=ACCENT, width=2)

out_path = os.path.expanduser("~/.hermes/openrouter-free-models.png")
img.save(out_path)
print(f"Saved: {out_path}  ({total_w}x{total_h})")
