---
name: youtube-content
description: >
  Fetch YouTube video transcripts and transform them into structured content
  (chapters, summaries, threads, blog posts). Use when the user shares a YouTube
  URL or video link, asks to summarize a video, requests a transcript, or wants
  to extract and reformat content from any YouTube video.
metadata:
  hermes:
    trigger_conditions:
      - user shares a YouTube URL or video link
      - user asks to summarize a video
      - user requests a transcript from a YouTube video
      - user wants to extract chapters, quotes, or key points from a video
      - user asks to convert a video into a blog post, thread, or article
      - user mentions a YouTube video ID or youtu.be short link
      - phrases: "summarize this video", "get transcript", "what does this video say", "youtube summary"
---

# YouTube Content Tool

Extract transcripts from YouTube videos and convert them into useful formats.

## When to Use

- User shares a YouTube URL, short link, or embeds a video
- User asks to summarize what a video says without watching it
- User requests structured content from a video: chapters, quotes, blog posts, Twitter/X threads
- User wants timestamps + key points from educational, technical, or conference talks
- User needs a transcript for quoting, translation, or downstream processing
- User provides a video ID directly (11-char string)
- User asks "what's in this video" or "what does this person say about X"

## Not For

- **Downloading YouTube video/audio files** → use `yt-dlp` or `ffmpeg` instead
- **Real-time livestream commentary or chat** → this only handles transcripts after the stream ends
- **Non-YouTube video platforms (Vimeo, Dailymotion, Bilibili)** → `youtube-transcript-api` is YouTube-only; use platform-specific APIs or general-purpose transcription tools
- **Speaker diarization or multi-speaker identification** → the transcript is single-speaker text; use `whisper` with diarization for speaker attribution
- **Full-text search across multiple videos** → this fetches one video at a time; use a video search API or your database for cross-video search
- **Audio-only extraction or waveform analysis** → use `ffmpeg` for audio extraction, `songsee` for spectrograms
- **Monetization, view count, or channel analytics** → use the YouTube Data API v3; this tool only handles transcripts

## Setup

```bash
pip install youtube-transcript-api
```

## Helper Script

`SKILL_DIR` is the directory containing this SKILL.md file. The script accepts any standard YouTube URL format, short links (youtu.be), shorts, embeds, live links, or a raw 11-character video ID.

```bash
# JSON output with metadata
python3 SKILL_DIR/scripts/fetch_transcript.py "https://youtube.com/watch?v=VIDEO_ID"

# Plain text (good for piping into further processing)
python3 SKILL_DIR/scripts/fetch_transcript.py "URL" --text-only

# With timestamps
python3 SKILL_DIR/scripts/fetch_transcript.py "URL" --timestamps

# Specific language with fallback chain
python3 SKILL_DIR/scripts/fetch_transcript.py "URL" --language tr,en
```

## Output Formats

After fetching the transcript, format it based on what the user asks for:

- **Chapters**: Group by topic shifts, output timestamped chapter list
- **Summary**: Concise 5-10 sentence overview of the entire video
- **Chapter summaries**: Chapters with a short paragraph summary for each
- **Thread**: Twitter/X thread format — numbered posts, each under 280 chars
- **Blog post**: Full article with title, sections, and key takeaways
- **Quotes**: Notable quotes with timestamps

### Example — Chapters Output

```
00:00 Introduction — host opens with the problem statement
03:45 Background — prior work and why existing solutions fall short
12:20 Core method — walkthrough of the proposed approach
24:10 Results — benchmark comparisons and key takeaways
31:55 Q&A — audience questions on scalability and next steps
```

## Workflow

1. **Fetch** the transcript using the helper script with `--text-only --timestamps`.
2. **Validate**: confirm the output is non-empty and in the expected language. If empty, retry without `--language` to get any available transcript. If still empty, tell the user the video likely has transcripts disabled.
3. **Chunk if needed**: if the transcript exceeds ~50K characters, split into overlapping chunks (~40K with 2K overlap) and summarize each chunk before merging.
4. **Transform** into the requested output format. If the user did not specify a format, default to a summary.
5. **Verify**: re-read the transformed output to check for coherence, correct timestamps, and completeness before presenting.

## Pitfalls

1. **Auto-captions mangle technical content** — YouTube auto-generated transcripts frequently corrupt proper nouns, acronyms, and domain-specific terms. Fix: flag uncertainty and note that captions are auto-generated; cross-check critical terminology against the video title or description.

2. **Transcript covers only part of the video** — Some videos have music segments, sponsor breaks, or silent sections where no transcript is generated, causing multi-minute gaps. Fix: check for time gaps >60s in timestamps and flag them explicitly rather than presenting output as complete.

3. **Very long videos (>2 hours) exceed context limits** — The full transcript may be too large to process in one pass. Fix: chunk at ~40K characters with 2K overlap, summarize each chunk independently, then merge. Never silently truncate.

4. **youtu.be short-link resolution failure** — In restricted network environments the script may fail to resolve youtu.be short-links. Fix: convert to canonical form `https://www.youtube.com/watch?v=VIDEO_ID` before retrying.

5. **Livestream in progress** — youtube-transcript-api raises an error for active livestreams. Fix: inform the user the stream is currently live and suggest retrying after it ends.

6. **Auto-generated track returned instead of manual captions** — Use `--language en` (not `en-US`) to prefer manually uploaded English transcripts; `en-US` typically refers to auto-generated versions.

7. **Age-restricted or sign-in-required videos** — The API cannot fetch transcripts from videos requiring a YouTube account login. Fix: inform the user the video is restricted; cookie-based auth is not supported.

## Error Handling

- **Transcript disabled**: tell the user; suggest they check if subtitles are available on the video page.
- **Private/unavailable video**: relay the error and ask the user to verify the URL.
- **No matching language**: retry without `--language` to fetch any available transcript, then note the actual language to the user.
- **Dependency missing**: run `pip install youtube-transcript-api` and retry.
