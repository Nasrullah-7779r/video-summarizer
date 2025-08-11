# Gemini Code Understanding

This document provides a summary of the project's context, based on an analysis of the codebase.

## Project Overview

This project is a FastAPI-based web service that provides summaries of YouTube videos. The user submits a YouTube video URL, and the service extracts the transcript, summarizes it using a Hugging Face model, and returns the summary.

## Project Structure

The project is structured as follows:

```
├───.gitignore
├───api.rest
├───base_models.py
├───get_transcript_variations.py
├───main.py
├───requirements.txt
├───transcript.py
├───video_processing.py
```

## Key Files

*   **`main.py`**: The main entry point of the application. It defines the FastAPI app, CORS middleware, and the `/summary` endpoint.
*   **`video_processing.py`**: This file contains the core logic for extracting the video ID from a YouTube URL, fetching the transcript, and summarizing the transcript using a Hugging Face model.
*   **`transcript.py`**: This file contains functions for fetching video transcripts using different methods, including `yt-dlp` and the `youtube_transcript_api`.
*   **`get_transcript_variations.py`**: This file provides alternative ways to get video transcripts, with a focus on robustness and handling different caption formats.
*   **`base_models.py`**: This file defines the Pydantic model for the request body of the `/summary` endpoint.
*   **`requirements.txt`**: This file lists the Python dependencies for the project.
*   **`api.rest`**: This file contains examples of how to make requests to the API.

## How to Run the Project

1.  Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```
2.  Set the `HF_TOKEN` environment variable with your Hugging Face API token.
3.  Run the FastAPI application:
    ```bash
    uvicorn main:app --reload
    ```
4.  Send a POST request to the `/summary` endpoint with a JSON payload containing the `video_url`.

## Dependencies

The project uses the following key dependencies:

*   **fastapi**: A modern, fast (high-performance), web framework for building APIs with Python 3.7+ based on standard Python type hints.
*   **uvicorn**: A lightning-fast ASGI server implementation, using uvloop and httptools.
*   **pydantic**: Data validation and settings management using Python type annotations.
*   **youtube-transcript-api**: A Python library for fetching YouTube video transcripts.
*   **yt-dlp**: A command-line program to download videos from YouTube and other video sites.
*   **requests**: A simple, yet elegant, HTTP library.
*   **python-dotenv**: A Python library for reading key-value pairs from a `.env` file and setting them as environment variables.

## API

The API has one endpoint:

*   **`POST /summary`**:
    *   **Request Body**:
        ```json
        {
            "video_url": "https://www.youtube.com/watch?v=..."
        }
        ```
    *   **Response**:
        ```json
        {
            "summary": "..."
        }
        ```