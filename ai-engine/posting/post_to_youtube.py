# -*- coding: utf-8 -*-

import os
import pickle
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

# Define the scope of access to YouTube
SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",  # For reading channel data
    "https://www.googleapis.com/auth/youtube.upload"     # For uploading videos
]

def authenticate_youtube_api():
    """Authenticate with YouTube API using OAuth2."""
    credentials = None
    if os.path.exists("token.pickle"):
        try:
            with open("token.pickle", "rb") as token:
                credentials = pickle.load(token)
        except (OSError, pickle.PickleError) as e:
            print(f"Error loading token.pickle: {e}")
            return None

    if not credentials or not credentials.valid:
        try:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                print("Credentials not found or expired, need re-authentication.")
                flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES)
                credentials = flow.run_local_server(port=57713)

            with open("token.pickle", "wb") as token:
                pickle.dump(credentials, token)
        except Exception as e:
            print(f"Error during authentication: {e}")
            return None

    return credentials

def upload_to_youtube(video_file, title, description, tags, category="22"):
    """Upload a video to YouTube using the authenticated API client."""
    credentials = authenticate_youtube_api()
    if not credentials:
        print("Failed to authenticate YouTube API.")
        return None

    try:
        youtube = googleapiclient.discovery.build("youtube", "v3", credentials=credentials)

        if not os.path.exists(video_file):
            print(f"Video file {video_file} not found!")
            return None

        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": tags,
                    "categoryId": category
                },
                "status": {
                    "privacyStatus": "public"  # You can set it to "private" or "unlisted" if needed
                }
            },
            media_body=MediaFileUpload(video_file, chunksize=-1, resumable=True)
        )

        response = request.execute()  # Executes the upload request
        print(f"Video uploaded successfully! Video ID: {response['id']}")
        return response['id']

    except googleapiclient.errors.HttpError as e:
        print(f"HTTP error occurred during the upload: {e}")
        print(f"Details: {e.content}")
        return None
    except Exception as e:
        print(f"An error occurred during the upload: {e}")
        return None

def fetch_channel_info(channel_id="UC_x5XG1OV2P6uZZ5FSM9Ttw"):
    """Fetch channel information using YouTube API."""
    credentials = authenticate_youtube_api()
    if not credentials:
        print("Failed to authenticate YouTube API.")
        return None

    try:
        youtube = googleapiclient.discovery.build("youtube", "v3", credentials=credentials)

        request = youtube.channels().list(
            part="snippet,contentDetails,statistics",
            id=channel_id
        )
        response = request.execute()
        print("Channel Info:")
        print(response)
        return response

    except googleapiclient.errors.HttpError as e:
        print(f"HTTP error occurred while fetching channel info: {e}")
        print(f"Details: {e.content}")
        return None
    except Exception as e:
        print(f"An error occurred while fetching channel info: {e}")
        return None

def main():
    # Example of fetching channel info
    channel_info = fetch_channel_info(channel_id="UC_x5XG1OV2P6uZZ5FSM9Ttw")  # Example channel ID
    if not channel_info:
        print("Failed to fetch channel information.")
        return

    # Example of uploading a video
    video_file = "final_video.mp4"  # Ensure this is a valid video file path
    title = "Sample Video Title"
    description = "This is a description of the video."
    tags = ["sample", "video", "youtube", "api"]

    video_id = upload_to_youtube(video_file, title, description, tags)
    if video_id:
        print(f"Uploaded video ID: {video_id}")
    else:
        print("Failed to upload the video.")

if __name__ == "__main__":
    main()
