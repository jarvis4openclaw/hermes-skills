#!/usr/bin/env python3
"""
NostrX - Nostr to Twitter/X Sync Tool
Syncs posts from Nostr to Twitter, handling media and remembering state.
Threading: posts > 280 chars are posted as a thread, ending with the Nostr link.
"""

import asyncio
import json
import os
import re
import time
import requests
import tempfile
from datetime import datetime, timedelta
from dotenv import load_dotenv

import tweepy
from nostr_sdk import (
    Client, Filter, Kind, Timestamp, PublicKey, 
    RelayUrl
)

# Load environment variables from .env file
load_dotenv()

# ==========================================
# CONFIGURATION
# ==========================================

# Nostr Settings
# Get npubs from environment variable (comma-separated)
npubs_env = os.getenv("NOSTR_NPUBS", "")
MONITORED_NPUBS = [n.strip() for n in npubs_env.split(",") if n.strip()]

# Get relays from environment variable (comma-separated), or use defaults
relays_env = os.getenv("NOSTR_RELAYS", "")
if relays_env:
    NOSTR_RELAYS = [r.strip() for r in relays_env.split(",") if r.strip()]
else:
    NOSTR_RELAYS = [
        "wss://relay.damus.io",
        "wss://nos.lol",
        "wss://relay.nostr.band",
        "wss://relay.primal.net"
    ]

# Twitter Settings
TWITTER_API_KEY=os.getenv("TWITTER_API_KEY","")
TWITTER_API_SECRET=os.getenv("TWITTER_API_SECRET","")
TWITTER_ACCESS_TOKEN=os.getenv("TWITTER_ACCESS_TOKEN","")
TWITTER_ACCESS_SECRET=os.getenv("TWITTER_ACCESS_SECRET","")

# State File
STATE_FILE = "sync_state.json"

# Media Extensions to detect in Nostr posts
MEDIA_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mov']

# ==========================================
# STATE MANAGEMENT
# ==========================================

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    # Default state: Sync from 24 hours ago if running for the first time
    return {
        "last_synced_timestamp": int(time.time()) - 86400,
        "synced_event_ids": [] # Keep track of IDs to avoid duplicates
    }

def save_state(state):
    # Keep history manageable (last 1000 IDs)
    state["synced_event_ids"] = state["synced_event_ids"][-1000:]
    
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

# ==========================================
# MEDIA HANDLING
# ==========================================

def extract_media_urls(content):
    """Find media URLs in text content"""
    urls = []
    clean_content = content
    
    # Regex for URLs
    url_pattern = r'https?://\S+'
    found_urls = re.findall(url_pattern, content)
    
    for url in found_urls:
        lower_url = url.lower()
        # Check if it looks like an image/video file
        if any(lower_url.endswith(ext) for ext in MEDIA_EXTENSIONS):
            urls.append(url)
            # Remove the URL from the text so it doesn't appear as a link in the tweet
            # (Twitter displays uploaded media natively)
            clean_content = clean_content.replace(url, "").strip()
            
    return clean_content, urls

def download_media(url):
    """Download media to a temp file"""
    try:
        # Fake user agent to avoid blocking
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, stream=True, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # Get extension
            ext = os.path.splitext(url)[1]
            if not ext:
                ext = ".jpg" # Default
                
            # Create temp file
            tf = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
            for chunk in response.iter_content(chunk_size=8192):
                tf.write(chunk)
            tf.close()
            return tf.name
    except Exception as e:
        print(f"     ❌ Failed to download media {url}: {e}")
    return None

# ==========================================
# THREAD HELPERS
# ==========================================

def build_nostr_link(event_id):
    """Build a Nostr link for the given event ID."""
    return f"https://njump.me/{event_id}"

def split_text_for_thread(text, max_len=275):
    """
    Split text into chunks safe for a Twitter thread.
    Each chunk is at most max_len chars. Returns a list of strings.
    """
    if len(text) <= max_len:
        return [text]
    chunks = []
    while len(text) > max_len:
        chunks.append(text[:max_len])
        text = text[max_len:]
    chunks.append(text)
    return chunks

# ==========================================
# SYNC LOGIC
# ==========================================

class SyncTool:
    def __init__(self):
        self.state = load_state()
        self.client = None
        self.twitter_client = None
        self.twitter_v2 = None
        
    def setup_twitter(self):
        if all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET]):
            # V1.1 API for media upload
            auth = tweepy.OAuth1UserHandler(
                TWITTER_API_KEY, TWITTER_API_SECRET,
                TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET
            )
            self.twitter_client = tweepy.API(auth)
            
            # V2 API for posting tweets
            self.twitter_v2 = tweepy.Client(
                consumer_key=TWITTER_API_KEY,
                consumer_secret=TWITTER_API_SECRET,
                access_token=TWITTER_ACCESS_TOKEN,
                access_token_secret=TWITTER_ACCESS_SECRET
            )
            print("✓ Twitter API connected")
        else:
            print("⚠️  Twitter credentials missing. Running in DRY RUN mode.")

    async def setup_nostr(self):
        self.client = Client()
        for relay in NOSTR_RELAYS:
            await self.client.add_relay(RelayUrl.parse(relay))
        
        await self.client.connect()
        print(f"✓ Connected to {len(NOSTR_RELAYS)} Nostr relays")

    def post_thread(self, text, media_ids, event_id):
        """
        Post a Twitter thread, handling the 280-char limit.
        Long posts are split into a thread; final tweet includes the Nostr link.
        """
        nostr_link = build_nostr_link(event_id)
        link_len = len(nostr_link) + 1  # +1 for space before link

        # Max chars available for text in any tweet (leaves room for " (n/n)" if needed)
        MAX_CHARS = 275

        # Check if we need threading
        total_len = len(text) + link_len

        if total_len <= 280:
            # Fits in one tweet
            final_text = f"{text} {nostr_link}"
            resp = self.twitter_v2.create_tweet(text=final_text, media_ids=media_ids if media_ids else None)
            tweet_id = resp.data.get('id') if resp.data else None
            print(f"   ✅ Posted single tweet: {tweet_id}")
            return tweet_id

        # Needs a thread: split the text, post each chunk as a reply
        # Strategy: put link on the final tweet
        chunks = split_text_for_thread(text, MAX_CHARS)
        total_tweets = len(chunks)
        in_reply_to = None

        for i, chunk in enumerate(chunks):
            is_last = (i == total_tweets - 1)
            thread_marker = f" ({i+1}/{total_tweets})"

            if total_tweets == 1:
                # Shouldn't happen since total_len > 280, but safety guard
                tweet_text = f"{text} {nostr_link}"
            elif is_last:
                # Final tweet: append Nostr link
                tweet_text = f"{chunk} {nostr_link}"
            else:
                # Middle tweet: add thread marker
                tweet_text = f"{chunk}{thread_marker}"

            # Media only on the first tweet
            media = media_ids if i == 0 else None

            resp = self.twitter_v2.create_tweet(
                text=tweet_text,
                in_reply_to_tweet_id=in_reply_to,
                media_ids=media
            )
            tweet_id = resp.data.get('id') if resp.data else None
            print(f"   ✅ Tweet {i+1}/{total_tweets}: {tweet_id}")

            if in_reply_to is None:
                # First tweet ID becomes the thread parent
                pass
            in_reply_to = tweet_id

            if i < total_tweets - 1:
                time.sleep(1)

        return tweet_id

    async def run(self):
        print(f"[{datetime.now()}] Starting NostrX Sync...")
        print(r"""
                  _      __  __
  _ __   ___  ___| |_ _ _\ \/ /
 | '_ \ / _ \/ __| __| '__\  / 
 | | | | (_) \__ \ |_| |  /  \ 
 |_| |_|\___/|___/\__|_| /_/\_\                      
        """)
        
        self.setup_twitter()
        
        if not MONITORED_NPUBS:
            print("❌ No npubs configured in MONITORED_NPUBS")
            return

        await self.setup_nostr()

        # 1. Prepare Filter
        # Fetch events since the last successful sync
        last_ts = self.state["last_synced_timestamp"]
        since = Timestamp.from_secs(last_ts + 1)
        
        authors = [PublicKey.parse(npub) for npub in MONITORED_NPUBS]
        f = Filter().authors(authors).kind(Kind(1)).since(since)
        
        print(f"\n📥 Fetching posts since {datetime.fromtimestamp(last_ts)}...")
        
        # Fetch events
        timeout = timedelta(seconds=30)
        events = await self.client.fetch_events(f, timeout)
        event_list = events.to_vec()
        
        # Sort oldest to newest so we post in order
        event_list.sort(key=lambda x: x.created_at().as_secs())
        
        if not event_list:
            print("✅ No new posts found.")
            return

        print(f"found {len(event_list)} new posts.")
        
        new_last_ts = last_ts
        
        for event in event_list:
            event_id = event.id().to_hex()
            
            # Skip duplicates
            if event_id in self.state["synced_event_ids"]:
                continue
                
            # Skip replies
            is_reply = False
            for tag in event.tags().to_vec():
                t = tag.as_vec()
                if len(t) > 0 and t[0] in ['e', 'reply']:
                    is_reply = True
                    break
            
            if is_reply:
                print(f"⏭️  Skipping reply {event_id[:8]}")
                continue

            # Process Content
            content = event.content()
            clean_text, media_urls = extract_media_urls(content)
            ts = datetime.fromtimestamp(event.created_at().as_secs())
            
            print(f"\n📝 Processing post from {ts}:")
            print(f"   \"{clean_text[:80]}...\"" if len(clean_text) > 80 else f"   \"{clean_text}\"")
            
            # Download Media
            media_ids = []
            temp_files = []
            
            if media_urls:
                print(f"   📷 Found {len(media_urls)} media items")
                for url in media_urls:
                    path = download_media(url)
                    if path:
                        temp_files.append(path)
                        if self.twitter_client:
                            try:
                                print(f"     Uploading {os.path.basename(path)}...")
                                media = self.twitter_client.media_upload(filename=path)
                                media_ids.append(media.media_id)
                            except Exception as e:
                                print(f"     ❌ Upload failed: {e}")
            
            # Post to Twitter
            if self.twitter_v2:
                try:
                    tweet_id = self.post_thread(clean_text, media_ids, event_id)
                    if tweet_id:
                        print(f"   ✅ Posted to Twitter (thread)")
                        
                        # Update state immediately after success
                        self.state["synced_event_ids"].append(event_id)
                        if event.created_at().as_secs() > new_last_ts:
                            new_last_ts = event.created_at().as_secs()
                            self.state["last_synced_timestamp"] = new_last_ts
                        
                        save_state(self.state)
                    else:
                        print(f"   ❌ create_tweet returned no tweet ID")
                        
                except Exception as e:
                    print(f"   ❌ Failed to tweet: {e}")
            else:
                print("   [DRY RUN] Would post to Twitter")
            
            # Cleanup
            for path in temp_files:
                try:
                    os.remove(path)
                except:
                    pass
            
            # Small delay to be nice to APIs
            time.sleep(1)

        print("\n Sync Complete!")

if __name__ == "__main__":
    tool = SyncTool()
    asyncio.run(tool.run())