from fastapi import FastAPI, HTTPException
from base_models import VideoURLRequest
from video_processing import get_transcript, summarize_video
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/ping")
async def ping():
    return {"message": "pong"}


@app.post("/summary")
async def get_summary(request: VideoURLRequest):
    video_url = request.video_url
    transcript = get_transcript(video_url)
    if "Error" in transcript:
        raise HTTPException(status_code=400, detail=transcript)

    summary = summarize_video(transcript)
    if summary:
        return {"summary": summary}
    else:
        raise HTTPException(status_code=500, detail="Failed to get the summary.")