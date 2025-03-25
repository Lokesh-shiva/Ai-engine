import os
from flask import Flask, request, jsonify
from trend_analysis.get_trending_topics import get_trending_videos
from content_generation.generate_video import create_video_with_generated_images
from optimization.generate_tags import initialize_model, generate_tags
from posting.post_to_youtube import upload_to_youtube
from dotenv import load_dotenv

# Set ImageMagick binary path explicitly
os.environ["IMAGEIO_IMAGEMAGICK_BINARY"] = "/usr/bin/magick"

# Load environment variables
load_dotenv()

app = Flask(__name__)

def sanitize_tags(tags):
    """
    Sanitize and clean up the tags to ensure they are valid for YouTube.
    """
    try:
        if not isinstance(tags, list):
            raise ValueError("Tags must be a list.")

        valid_tags = []
        for tag in tags:
            cleaned_tag = ''.join(c for c in tag if c.isalnum()).strip()  # Keep only alphanumeric characters
            cleaned_tag = cleaned_tag.lower()  # Convert to lowercase

            if len(cleaned_tag) > 2 and len(cleaned_tag) <= 30:
                valid_tags.append(f"#{cleaned_tag[:30]}")  # Limit tag length to 30 characters

        return valid_tags[:10] if valid_tags else ["#trending", "#video", "#defaulttag"]
    except Exception as e:
        print(f"Error sanitizing tags: {e}")
        return ["#trending", "#video", "#defaulttag"]

def generate_video_title(trending_topic):
    return f"Exploring: {trending_topic}"

def generate_video_description(title, tags):
    tags_string = ", ".join(tags)
    return f"Check out the latest trends in {title}! Stay updated with the most popular topics today.\n\nTags: {tags_string}"

@app.route("/")
def home():
    return "AI Video Generator Backend is running!"

@app.route("/generate_video", methods=["POST"])
def generate_video():
    """
    API to generate a video based on a trending topic or custom prompt.
    """
    data = request.json
    custom_prompt = data.get("prompt", "").strip()

    if custom_prompt:
        print(f"Using custom prompt: {custom_prompt}")
        dynamic_prompt = custom_prompt
        trending_topic = "Custom Topic"
    else:
        print("Fetching trending topics...")
        try:
            trends = get_trending_videos()
            if not trends:
                return jsonify({"success": False, "error": "No trending videos available."}), 400
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

        trending_topic = trends[0][0]
        print(f"Selected trending topic: {trending_topic}")

        dynamic_prompt = f"Create a fun and visually appealing image about '{trending_topic}'. " \
                         f"Include vibrant colors, smooth transitions, and engaging graphics."
        print(f"Generated Dynamic Prompt: {dynamic_prompt}")

    output_dir = "generated_videos"
    os.makedirs(output_dir, exist_ok=True)

    try:
        print(f"Generating video for prompt: {dynamic_prompt}")
        create_video_with_generated_images(prompt=dynamic_prompt, output_dir=output_dir)
        print("Video generated successfully.")
    except Exception as e:
        return jsonify({"success": False, "error": f"Error generating video: {e}"}), 500

    print("Generating tags for the video...")
    try:
        generator = initialize_model()
        if generator is None:
            raise ValueError("Failed to initialize the text generation model.")

        raw_tags = generate_tags(f"Generate relevant tags for a video about {trending_topic}", generator)
        valid_tags = sanitize_tags(raw_tags)
        print(f"Sanitized tags: {valid_tags}")
    except Exception as e:
        valid_tags = ["#trending", "#video", "#defaulttag"]
        print(f"Error generating or sanitizing tags: {e}")

    print("Generating video title and description...")
    try:
        title = generate_video_title(trending_topic)
        description = generate_video_description(title, valid_tags)
    except Exception as e:
        title = "Default Video Title"
        description = "Default video description."

    final_video_path = os.path.join(output_dir, "final_video.mp4")
    print("Uploading video to YouTube...")
    try:
        video_id = upload_to_youtube(
            video_file=final_video_path,
            title=title,
            description=description,
            tags=valid_tags
        )
        if video_id:
            print(f"Video uploaded successfully. Video ID: {video_id}")
            return jsonify({"success": True, "video_id": video_id})
        else:
            print("Failed to upload the video.")
            return jsonify({"success": False, "error": "Failed to upload video."}), 500
    except Exception as e:
        return jsonify({"success": False, "error": f"Error uploading video: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)