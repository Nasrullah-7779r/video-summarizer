from pydantic import BaseModel


class VideoURLRequest(BaseModel):
    video_url: str