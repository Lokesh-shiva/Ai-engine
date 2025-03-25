import time
import subprocess
import random
from trend_analysis.get_trending_topics import get_trending_videos
from content_generation.generate_video import create_video_with_generated_images
from optimization.generate_tags import generate_tags
from optimization.generate_captions import generate_captions
from posting.post_to_youtube import upload_to_youtube

def automate_ai_engine():
    while True:
        print("⚡ Fetching Trending Topics...")
        topics = get_trending_videos()
        selected_topic = random.choice(topics)
        print(f"🔥 Selected Topic: {selected_topic}")

        print("🖼️ Generating AI Images...")
        subprocess.run(["python", "content_generation/generate_video.py", selected_topic])

        print("🎬 Creating Video...")
        video_path = create_video_with_generated_images(selected_topic)

        print("🏷️ Generating Tags & Captions...")
        tags = generate_tags(selected_topic)
        caption = generate_captions(selected_topic)

        print("🚀 Uploading to YouTube...")
        upload_to_youtube(video_path, tags, caption)

        print("✅ Video Uploaded Successfully!")

        print("⏳ Waiting before next generation...")
        time.sleep(3600)  # Wait 1 hour before generating the next video

if __name__ == "__main__":
    automate_ai_engine()
