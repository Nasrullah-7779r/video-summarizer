
import json
import time
import random
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import yt_dlp
import re
import requests
import xml.etree.ElementTree as ET
from urllib.parse import unquote
from fastapi import HTTPException
import os, glob, tempfile


def extract_video_id(url):
    """Extract video ID from various YouTube URL formats"""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def parse_youtube_xml_captions(xml_content):
    """Parse YouTube XML captions"""
    try:
        # Clean up the XML content
        xml_content = xml_content.replace('&', '&amp;')
        
        root = ET.fromstring(xml_content)
        transcript_text = ""
        
        for text_elem in root.findall('.//text'):
            if text_elem.text:
                # Decode HTML entities
                text = unquote(text_elem.text)
                text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
                transcript_text += text + " "
        
        return transcript_text.strip()
    
    except Exception as e:
        print(f"XML parsing error: {e}")
        return None

def parse_youtube_xml_captions(xml_content):
    """Parse YouTube XML captions with better error handling"""
    try:
        # Check if response is actually XML
        if not xml_content.strip().startswith('<?xml') and not xml_content.strip().startswith('<transcript'):
            print("Response is not XML format")
            return None
        
        # Clean up common XML issues
        xml_content = xml_content.replace('&', '&amp;')
        xml_content = xml_content.replace('&amp;amp;', '&amp;')
        
        root = ET.fromstring(xml_content)
        transcript_text = ""
        
        # Handle different XML structures
        text_elements = root.findall('.//text') or root.findall('.//p')
        
        for text_elem in text_elements:
            if text_elem.text:
                # Decode HTML entities
                text = unquote(text_elem.text)
                text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
                text = text.replace('\n', ' ').strip()
                if text:
                    transcript_text += text + " "
        
        return transcript_text.strip()
    except ET.ParseError as e:
        print(f"XML parsing error: {e}")
        print(f"Response preview: {xml_content[:200]}...")
        return None
    except Exception as e:
        print(f"General parsing error: {e}")
        return None

def get_english_transcript_v1(video_url):
    """Method 1: Using youtube-transcript-api with better error handling"""
    try:
        video_id = extract_video_id(video_url)
        if not video_id:
            return None
        
        # Add delay to avoid rate limiting
        time.sleep(random.uniform(0.5, 1.5))
        
        # Try to get English transcript
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Try manual first, then auto-generated
        try:
            transcript = transcript_list.find_manually_created_transcript(['en'])
        except:
            try:
                transcript = transcript_list.find_generated_transcript(['en'])
            except Exception as e:
                print(f"No English transcript available: {e}")
                return None
        
        # Get transcript data
        transcript_data = transcript.fetch()
        
        # Manual formatting instead of TextFormatter
        transcript_text = ""
        for entry in transcript_data:
            transcript_text += entry['text'] + " "
        
        return transcript_text.strip()
        
    except Exception as e:
        print(f"Method 1 failed: {e}")
        return None   

def get_english_transcript_v2(video_url):
    """Method 2: Using yt-dlp with caption parsing"""
    try:
        ydl_opts = {
            'writeautomaticsub': True,
            'writesubtitles': True,
            'subtitleslangs': ['en'],
            'skip_download': True,
            'quiet': True,
            'no_warnings': True,
            'sleep_interval': 2,
            'max_sleep_interval': 5,
            'extractor_retries': 2,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            time.sleep(random.uniform(2, 4))
            
            info = ydl.extract_info(video_url, download=False)
            
            # Try manual subtitles first
            if 'subtitles' in info and 'en' in info['subtitles']:
                subtitle_url = info['subtitles']['en'][0]['url']
                response = requests.get(subtitle_url, timeout=10)
                if response.status_code == 200:
                    return parse_youtube_xml_captions(response.text)
            
            # Try auto captions
            elif 'automatic_captions' in info and 'en' in info['automatic_captions']:
                subtitle_url = info['automatic_captions']['en'][0]['url']
                response = requests.get(subtitle_url, timeout=10)
                if response.status_code == 200:
                    return parse_youtube_xml_captions(response.text)
                
    except Exception as e:
        print(f"Method 2 failed: {e}")
        return None
EN_CODES = ["en", "en-US", "en-GB"]

def get_english_transcript_v3(video_url):
    """Method 3: Direct API approach"""
    try:
        video_id = extract_video_id(video_url)
        if not video_id:
            return None
        
        # Try direct YouTube API approach
        base_url = "https://www.youtube.com/api/timedtext"
        params = {
            'v': video_id,
            'lang': 'en',
            'fmt': 'srv3'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        time.sleep(random.uniform(1, 2))
        response = requests.get(base_url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200 and response.text.strip():
            return parse_youtube_xml_captions(response.text)
            
    except Exception as e:
        print(f"Method 3 failed: {e}")
        return None
    

def json3_to_text(payload: str) -> str:
    """Convert a json3 captions payload (string) into plain text."""
    data = json.loads(payload)
    parts = []
    for ev in data.get("events", []):
        segs = ev.get("segs")
        if not segs:
            continue
        tokens = []
        for seg in segs:
            t = seg.get("utf8", "")
            if t == "\n":
                continue
            tokens.append(t)
        if tokens:
            parts.append("".join(tokens))
    # fix spaces before punctuation, collapse multiples
    text = " ".join(parts)
    text = re.sub(r"\s+([.,!?;:])", r"\1", text)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text

def vtt_to_text(vtt: str) -> str:
    """Convert a WEBVTT payload (string) into plain text."""
    lines = []
    for line in vtt.splitlines():
        s = line.strip()
        if not s or s.startswith("WEBVTT") or "-->" in s or s.isdigit():
            continue
        s = (s.replace("<c>", "").replace("</c>", "")
               .replace("<b>", "").replace("</b>", "")
               .replace("<i>", "").replace("</i>", ""))
        lines.append(s)
    text = " ".join(lines)
    text = re.sub(r"\s+([.,!?;:])", r"\1", text).strip()
    return text

# def get_english_transcript(url: str) -> str | None:
#     """
#     Straightforward: ask yt-dlp for English captions, prefer json3 (easiest to parse),
#     else fall back to VTT. Returns plain text or None.
#     """
#     ydl_opts = {
#         "skip_download": True,
#         "quiet": True,
#         "no_warnings": True,
#         "writeautomaticsub": True,               # auto-CC
#         "subtitleslangs": EN_CODES,              # en variants
#         "subtitlesformat": "json3",              # ask for json3 first
#         "extractor_args": {"youtube": {"player_client": ["ios","web"]}},
#     }
#     with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#         info = ydl.extract_info(url, download=False)

#     # Prefer json3 if available
#     for key in ("automatic_captions", "requested_subtitles", "subtitles"):
#         tracks_by_lang = info.get(key) or {}
#         for code in EN_CODES:
#             tracks = tracks_by_lang.get(code)
#             if not tracks:
#                 continue
#             track = tracks[0] if isinstance(tracks, list) else tracks
#             track_url = track.get("url")
#             ext = (track.get("ext") or track.get("format"))  # ext can be 'json3' | 'vtt' | ...
#             if not track_url:
#                 continue

#             headers = {
#                 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
#             }
#             resp = requests.get(track_url, headers=headers, timeout=20)
#             resp.raise_for_status()
#             if (ext or "").lower() == "json3" or (track_url and "fmt=json3" in track_url):
#                 print("error here")
#                 return json3_to_text(resp.text)
#             else:
#                 # fallback: treat as VTT
#                 return vtt_to_text(resp.text)

#     return None



EN_CODES = ["en", "en-US", "en-GB", "en-IN"]

def get_english_transcript(url: str) -> str | None:
    with tempfile.TemporaryDirectory() as td:
        ydl_opts = {
            "skip_download": True,
            "quiet": True,
            "no_warnings": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": EN_CODES[:1],
            "subtitlesformat": "json3",
            "outtmpl": os.path.join(td, "%(id)s.%(ext)s"),
            "geo_bypass": True,
            # If you still see 403, uncomment one of these:
            # "cookiesfrombrowser": ("chrome",),   # uses your Chrome session
            # "cookiefile": "/path/to/cookies.txt",
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            ydl.download([url])  # yt-dlp fetches subs with correct headers/cookies

        vid = info["id"]
        # Prefer json3; fallback to vtt
        for code in EN_CODES[:1]:
            p_json = glob.glob(os.path.join(td, f"{vid}.{code}.json3"))
            if p_json:
                data = open(p_json[0], "r", encoding="utf-8", errors="ignore").read()
                return json3_to_text(data)
            # p_vtt = glob.glob(os.path.join(td, f"{vid}.{code}.vtt"))
            # if p_vtt:
            #     data = open(p_vtt[0], "r", encoding="utf-8", errors="ignore").read()
            #     return vtt_to_text(data)
        

    return None
