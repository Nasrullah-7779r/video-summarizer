from fastapi import FastAPI, HTTPException
from base_models import VideoURLRequest
from get_transcript_variations import get_english_transcript
from video_processing import summarize_video
from fastapi.middleware.cors import CORSMiddleware
from transcript_text import test_transcript
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

INVIDIOUS_INSTANCES = [
    "https://yewtu.be",
    "https://yewtu.eu",
    "https://yewtu.kavin.rocks",
    "https://yewtu.snopyta.org",
    "https://yewtu.imy.at",
    "https://yewtu.cloud",
]

@app.get("/ping")
async def ping():
    return {"message": "pong"}


@app.post("/summary")
async def get_summary(request: VideoURLRequest):


    video_url = request.video_url
    # vid_id = get_video_id(video_url)
    # if not vid_id:
    #     raise HTTPException(status_code=400, detail="Invalid YouTube URL")
    # try:

    url = "https://www.youtube.com/watch?v=i4b_ETwPoTE&ab_channel=HiteshChoudhary"
    test_url = "https://youtu.be/LS1AszxJypc?si=m73HLwCK0Y09gan6"
    
    transcript = get_english_transcript(video_url)

    if transcript:
        print("this is transcript",transcript)
    else:
        return {"message": "No auto‑CC found"}

    summary = await summarize_video(transcript)
    if summary:
        return {"summary": summary}
    else:
        raise HTTPException(status_code=500, detail="Failed to get the summary.")