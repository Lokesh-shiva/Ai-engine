import os
from trend_analysis.get_trending_topics import get_trending_videos
from content_generation.generate_video import create_video_with_generated_images
from optimization.generate_tags import initialize_model, generate_tags
from posting.post_to_youtube import upload_to_youtube
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def sanitize_tags(tags):
    """
    Sanitize and clean up the tags to ensure they are valid for YouTube.
    """
    try:
        if not isinstance(tags, list):
            raise ValueError("Tags must be a list.")

        valid_tags = []
        for tag in tags:
            # Clean the tag: remove invalid characters, ensure it's a single word, and limit length
            cleaned_tag = ''.join(c for c in tag if c.isalnum()).strip()  # Keep only alphanumeric characters
            cleaned_tag = cleaned_tag.lower()  # Convert to lowercase

            # Avoid adding overly long or irrelevant tags
            if len(cleaned_tag) > 2 and len(cleaned_tag) <= 30:
                valid_tags.append(f"#{cleaned_tag[:30]}")  # Limit tag length to 30 characters and add "#"

        # Ensure a maximum of 10 tags
        return valid_tags[:10] if valid_tags else ["#trending", "#video", "#defaulttag"]
    except Exception as e:
        print(f"Error sanitizing tags: {e}")
        return ["#trending", "#video", "#defaulttag"]

def generate_video_title(trending_topic):
    """
    Generate a video title using the trending topic.
    """
    return f"Exploring: {trending_topic}"

def generate_video_description(title, tags):
    """
    Create a dynamic description by appending tags to the title.
    """
    tags_string = ", ".join(tags)
    return f"Check out the latest trends in {title}! Stay updated with the most popular topics today.\n\nTags: {tags_string}"

if __name__ == "__main__":
    # Step 1: Allow user to provide a custom prompt or default to trending topics
    print("Welcome to the AI Video Generator!")
    print("Would you like to enter a custom prompt? (Press Enter to skip and use trending topics.)")
    custom_prompt = input("Custom Prompt: ").strip()

    if custom_prompt:
        print(f"Using custom prompt: {custom_prompt}")
        dynamic_prompt = custom_prompt
        trending_topic = "Custom Topic"  # Placeholder, as we're using a custom prompt
    else:
        # Fetch trending topics
        print("Fetching trending topics...")
        try:
            trends = get_trending_videos()
            if not trends:
                raise ValueError("No trending videos available. Please check your API key or try again later.")
        except Exception as e:
            print(f"Error fetching trending topics: {e}")
            exit(1)

        # Use the first trending topic to generate video content
        trending_topic = trends[0][0]
        print(f"Selected trending topic: {trending_topic}")

        # Dynamic prompt is fetched from `get_trending_topics.py`
        dynamic_prompt = f"Create a fun and visually appealing image about '{trending_topic}'. " \
                         f"Include vibrant colors, smooth transitions, and engaging graphics."
        print(f"Generated Dynamic Prompt: {dynamic_prompt}")

    # Step 2: Generate video
    output_dir = "generated_videos"
    os.makedirs(output_dir, exist_ok=True)

    try:
        print(f"Generating video for prompt: {dynamic_prompt}")
        create_video_with_generated_images(prompt=dynamic_prompt, output_dir=output_dir)
        print("Video generated successfully.")
    except Exception as e:
        print(f"Error generating video: {e}")
        exit(1)

    # Step 3: Generate tags for the video
    print("Generating tags for the video...")
    try:
        # Initialize the Hugging Face model
        generator = initialize_model()
        if generator is None:
            raise ValueError("Failed to initialize the text generation model.")

        # Generate raw tags using `generate_tags`
        raw_tags = generate_tags(f"Generate relevant tags for a video about {trending_topic}", generator)
        print(f"Raw tags generated: {raw_tags}")

        # Sanitize the tags
        valid_tags = sanitize_tags(raw_tags)
        print(f"Sanitized tags: {valid_tags}")
    except Exception as e:
        print(f"Error generating or sanitizing tags: {e}")
        valid_tags = ["#trending", "#video", "#defaulttag"]

    # Step 4: Generate the video title and description
    print("Generating video title and description...")
    try:
        title = generate_video_title(trending_topic)
        description = generate_video_description(title, valid_tags)
        print(f"Generated Title: {title}")
        print(f"Generated Description: {description}")
    except Exception as e:
        print(f"Error generating title or description: {e}")
        title = "Default Video Title"
        description = "Default video description."

    # Step 5: Post video to YouTube
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
        else:
            print("Failed to upload the video.")
    except Exception as e:
        print(f"An error occurred during the upload: {str(e)}")

