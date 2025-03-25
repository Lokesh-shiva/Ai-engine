import os
from dotenv import load_dotenv
from .video_creation import create_video_with_generated_images  # Ensure the relative import is correct

if __name__ == "__main__":
    # Load environment variables from the .env file
    load_dotenv()

    # Check if the Hugging Face API key exists
    HF_API_KEY = os.getenv("HF_API_KEY")
    if not HF_API_KEY:
        print("Error: HF_API_KEY not found in the .env file. Exiting.")
        exit(1)

    # Define the prompt for video generation
    prompt = "A cinematic view of a serene sunset over a mountain range with golden light reflecting on a calm lake"

    # Output directory for generated videos
    output_dir = "generated_videos"
    os.makedirs(output_dir, exist_ok=True)

    # Call the function to create a video with the given prompt
    print(f"Starting video creation for the prompt: '{prompt}'")
    try:
        create_video_with_generated_images(prompt, output_dir=output_dir)
        print("Video creation process completed successfully.")
    except Exception as e:
        print(f"An error occurred during the video creation process: {e}")

