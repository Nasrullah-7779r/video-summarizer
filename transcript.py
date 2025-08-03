import requests
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi as yta


def fetch_transcript_with_ytdlp(video_url: str) -> str:
    opts = {
        "skip_download": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["en"],
        "subtitlesformat": "vtt",
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(video_url, download=False)

    # 1) look for automatic captions (old API)
    captions = info.get("automatic_captions", {}).get("en")
    # 2) fallback to requested_subtitles (newer field)
    if not captions:
        sub = info.get("requested_subtitles", {}).get("en")
        captions = [sub] if isinstance(sub, dict) else sub

    if not captions:
        raise RuntimeError("No English subtitles found via yt-dlp")

    # captions may be a list of tracks or a single dict
    track = captions[0] if isinstance(captions, list) else captions
    vtt_url = track["url"]
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    }
    vtt_data = requests.get(vtt_url, headers=headers).text

    # strip VTT cues → plain text
    lines = []
    for line in vtt_data.splitlines():
        line = line.strip()
        if not line or "-->" in line or line.isdigit():
            continue
        lines.append(line)
    return " ".join(lines)


EN_CODES = ["en", "en-US", "en-GB"]

# def vtt_to_text(vtt: str) -> str:
#     lines = []
#     for line in vtt.splitlines():
#         s = line.strip()
#         if not s or s.startswith("WEBVTT") or "-->" in s or s.isdigit():
#             continue
#         s = s.replace("<c>", "").replace("</c>", "").replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", "")
#         lines.append(s)
#     return " ".join(lines)




def english_captions(url: str) -> str:
    # extract the 11-char ID, e.g. “i4b_ETwPoTE”
    vid = url.split("v=")[-1].split("&")[0].replace("youtu.be/", "")
    text = " ".join(seg["text"] for seg in yta.get_transcript(vid, languages=["en"]))
    return text

def get_auto_cc(video_id: str) -> str | None:
    # 1) fetch Invidious metadata
    meta = requests.get(f"https://yewtu.be/api/v1/videos/{video_id}").json()
    subs = meta.get("subtitles", [])
    # 2) find the auto‑CC URL
    entry = next((s for s in subs if s["lang"]=="en" and s["kind"]=="asr"), None)
    if not entry:
        return None
    # 3) download & clean
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    }
    vtt = requests.get(entry["url"], headers=headers).text
    lines = [
        line for line in vtt.splitlines()
        if line and not line[0].isdigit() and "-->" not in line
    ]
    return " ".join(lines)

