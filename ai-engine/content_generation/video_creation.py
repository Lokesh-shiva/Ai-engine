import os
import time
import torch
from datetime import datetime
from diffusers import StableVideoDiffusionPipeline
from diffusers.utils import export_to_video
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip, ImageClip, CompositeVideoClip
from moviepy.video.fx.all import fadein, fadeout
from PIL import Image, ImageDraw, ImageFont
import subprocess
import traceback
from dotenv import load_dotenv
from .image_generation import generate_images_with_huggingface
from .audio_generation import generate_audio_with_audioldm2

# Load API Key from .env file
load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY")

if not HF_API_KEY:
    print("Error: HF_API_KEY not found in .env file")
    exit(1)

# Ensure ImageMagick path is set correctly
os.environ["IMAGEMAGICK_BINARY"] = "magick"

def resize_image(image_path, target_size=(1024, 576)):
    try:
        print(f"Resizing image: {image_path} to {target_size}...")
        img = Image.open(image_path)
        img_resized = img.resize(target_size, Image.BICUBIC)  # Higher quality resizing
        resized_dir = "resized_images"
        os.makedirs(resized_dir, exist_ok=True)
        resized_path = os.path.join(resized_dir, f"resized_{os.path.basename(image_path)}")
        img_resized.save(resized_path)
        print(f"Image resized and saved as: {resized_path}")
        return resized_path
    except Exception as e:
        print(f"Error resizing image {image_path}: {e}")
        traceback.print_exc()
        return None

def generate_video_with_svd(image_path, prompt, output_path):
    try:
        print("Loading Stable Video Diffusion (SVD-XT) pipeline...")
        pipe = StableVideoDiffusionPipeline.from_pretrained(
            "stabilityai/stable-video-diffusion-img2vid-xt",
            torch_dtype=torch.float16,
            variant="fp16"
        )
        device = "cuda" if torch.cuda.is_available() else "cpu"
        pipe = pipe.to(device)
        pipe.enable_model_cpu_offload()

        print(f"Loading and resizing conditioning image from: {image_path}")
        image = Image.open(image_path).convert("RGB").resize((1024, 576), Image.BICUBIC)

        generator = torch.manual_seed(42)
        print(f"Generating video frames with prompt: {prompt}")
        frames = pipe(image, num_inference_steps=50, decode_chunk_size=8, generator=generator).frames[0]

        print(f"Exporting video to: {output_path}")
        export_to_video(frames, output_path, fps=14)
        print(f"Video generated successfully: {output_path}")
        return output_path
    except Exception as e:
        print(f"Error generating video: {e}")
        traceback.print_exc()
        return None


def create_text_overlay(text, size=(1920, 1080), font_size=50):
    """
    Creates a text overlay for the video.

    Args:
        text (str): The text to display.
        size (tuple): Size of the overlay image (width, height).
        font_size (int): Size of the font.

    Returns:
        str: Path to the saved text overlay image.
    """
    img = Image.new("RGBA", size, (0, 0, 0, 0))  # Create an empty image
    draw = ImageDraw.Draw(img)

    # Use a built-in font or specify the path to Arial
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font = ImageFont.truetype(font_path, font_size)

    # Get text bounding box (text size) using textbbox
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]  # Calculate width from bbox
    text_height = bbox[3] - bbox[1]  # Calculate height from bbox

    # Position text in the center of the image (adjust vertically as needed)
    position = ((size[0] - text_width) // 2, 50)  # Centered at the top
    draw.text(position, text, font=font, fill="white")

    # Save the text overlay image
    overlay_path = "text_overlay.png"
    img.save(overlay_path)
    return overlay_path


def merge_video_audio(video_path, audio_path, output_path):
    cmd = [
        "ffmpeg",
        "-i", video_path,  # Input video
        "-i", audio_path,  # Input audio
        "-c:v", "libx264",  # Video codec
        "-c:a", "aac",      # Audio codec
        "-strict", "experimental",
        "-b:a", "192k",
        "-shortest",  # Trim to shortest length
        output_path
    ]
    subprocess.run(cmd, check=True)



def create_video_with_generated_images(prompt, output_dir="generated_videos"):
    image_paths = []
    video_paths = []
    audio_path = None
    try:
        print(f"Generating images for prompt: {prompt}")
        image_paths = generate_images_with_huggingface(prompt, num_images=2)
        if not image_paths:
            print("No images were generated. Exiting video creation process.")
            return
        
        os.makedirs(output_dir, exist_ok=True)
        for idx, image_path in enumerate(image_paths):
            resized_image_path = resize_image(image_path)
            if resized_image_path:
                video_filename = f"generated_video_{idx + 1}.mp4"
                video_path = os.path.join(output_dir, video_filename)
                print(f"Generating video for resized image {resized_image_path}...")
                generated_video = generate_video_with_svd(resized_image_path, prompt, video_path)
                if generated_video:
                    video_paths.append(generated_video)

        if not video_paths:
            print("No videos were generated. Exiting.")
            return

        print("Generating audio...")
        audio_path = os.path.join(output_dir, "generated_audio.wav")
        generate_audio_with_audioldm2(
            prompt=f"Ambient music inspired by: {prompt}",
            negative_prompt="No distortion or noise.",
            output_path=audio_path,
            audio_length_in_s=10.0,
            num_waveforms=1,
            seed=42
        )

        print("Editing and concatenating video clips...")
        video_clips = [VideoFileClip(video).resize(height=1080) for video in video_paths]
        final_video = concatenate_videoclips(video_clips, method="compose")

        print("Adding text overlay...")
        text_overlay_path = create_text_overlay(f"Exploring: {prompt}")
        text_clip = ImageClip(text_overlay_path).set_duration(final_video.duration).set_position("center")
        final_video = final_video.fx(fadein, 1).fx(fadeout, 1)
        final_video = CompositeVideoClip([final_video, text_clip])

        if audio_path and os.path.exists(audio_path):
            print("Adding generated audio to the final video...")
            audio_clip = AudioFileClip(audio_path)
            final_video = final_video.set_audio(audio_clip)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_video_path = os.path.join(output_dir, "final_video.mp4")
        print(f"Writing final video to {final_video_path}...")
        final_video.write_videofile(final_video_path, codec="libx265", audio_codec="aac", fps=24, bitrate="5000k")
        print(f"Final video saved as {final_video_path}")

    except Exception as e:
        print(f"Error during video creation: {e}")
        traceback.print_exc()

    finally:
        print("Cleaning up temporary files...")
        for path in image_paths + video_paths + ([audio_path] if audio_path else []):
            if os.path.exists(path):
                os.remove(path)
