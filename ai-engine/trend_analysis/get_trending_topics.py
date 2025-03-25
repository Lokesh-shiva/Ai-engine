import requests
import random
import os
import torch
import gc
from transformers import pipeline

# Load API Key securely from environment variables
API_KEY = "AIzaSyCgMaYMZT0_scPWnMAmRCFQq-H7lSN4wig"
if not API_KEY:
    raise ValueError("Missing YOUTUBE_API_KEY environment variable")

# Define the DeepSeek R1 model name (Qwen 14B version) for text generation
MODEL_NAME = "deepseek-ai/DeepSeek-R1-Distill-Qwen-14B"

# Define offload folder and max_memory configuration
offload_folder = "./offload"
if not os.path.exists(offload_folder):
    os.makedirs(offload_folder)

# Adjust max_memory per device (limit GPU memory to 40GB)
max_memory = {"cuda:0": "40GB"}

# Optional: Mitigate memory fragmentation issues
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

def unload_model(model):
    """Unload a model from GPU memory."""
    del model
    torch.cuda.empty_cache()
    gc.collect()

def load_deepseek_pipeline():
    """Load the DeepSeek R1 pipeline for text generation."""
    pipe = pipeline(
        "text-generation",
        model=MODEL_NAME,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="sequential",       # Load layers sequentially to reduce peak memory usage
        trust_remote_code=True,
        offload_folder=offload_folder, # Offload unused model layers to CPU
        max_memory=max_memory          # Sets a memory cap on your GPU device
    )
    return pipe

def generate_ai_prompt(pipe, prompt, max_new_tokens=100, temperature=0.8):
    """
    Generate text using the provided pipeline and prompt.
    Temperature is set to encourage creative expansion.
    """
    pad_token_id = getattr(pipe.tokenizer, "eos_token_id", None)
    result = pipe(
        prompt,
        max_new_tokens=max_new_tokens,
        pad_token_id=pad_token_id,
        temperature=temperature
    )
    result_list = list(result) if not isinstance(result, list) else result
    if result_list:
        return result_list[0].get("generated_text", "")
    return ""

def get_trending_videos(region_code="US"):
    """Fetch trending video titles from YouTube."""
    url = (
        f"https://www.googleapis.com/youtube/v3/videos"
        f"?part=snippet&chart=mostPopular&regionCode={region_code}&maxResults=10&key={API_KEY}"
    )
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        data = response.json()
        return [(video["snippet"]["title"], video["id"]) for video in data.get("items", [])]
    except requests.exceptions.RequestException as e:
        print("Error fetching trending videos:", e)
        return []

def generate_dynamic_prompts(pipe, region_code="US"):
    """
    Generate a base prompt using either custom input or trending topics from YouTube.
    This base prompt will later be enhanced.
    """
    user_input = input("Would you like to enter a custom prompt? (Press Enter to skip and use trending topics.)\nCustom Prompt: ").strip()
    if user_input:
        print(f"Using custom prompt: {user_input}")
        return user_input  # Return the custom prompt; will be enhanced below.
    
    print("Fetching trending topics...")
    trending_videos = get_trending_videos(region_code=region_code)
    if trending_videos:
        video_titles = [title for title, _ in trending_videos]
        print("\nTrending Video Titles:")
        for idx, title in enumerate(video_titles, start=1):
            print(f"{idx}. {title}")
        selected_title = random.choice(video_titles)
        ai_prompt = f"Generate a creative and engaging base prompt for an AI video or image based on: {selected_title}"
        base_prompt = generate_ai_prompt(pipe, ai_prompt, max_new_tokens=100)
        print(f"\nBase prompt: {base_prompt}")
        return base_prompt
    else:
        print("No trending videos found. Using default base prompt.")
        return generate_ai_prompt(pipe, "Create an AI-generated video prompt about a futuristic world.", max_new_tokens=100)

def enhance_prompt(pipe, prompt, max_tokens=77):
    """
    Enhance the given prompt with creative, vivid, and descriptive details
    tailored for image and video generation. The final output is limited to max_tokens tokens.
    """
    enhancement_instruction = (
        "Enhance the following prompt for high-quality image and video generation by adding "
        "creative, vivid, and detailed descriptions. Include references to mood, setting, and visual elements. "
        "Ensure that the final result is concise and does not exceed {max_tokens} tokens. "
        "Prompt: {prompt}"
    ).format(max_tokens=max_tokens, prompt=prompt)
    
    # Generate an enhanced version with higher temperature for creative expansion.
    enhanced_text = generate_ai_prompt(pipe, enhancement_instruction, max_new_tokens=200, temperature=0.9)
    
    # Debug: Print the full enhanced output before token truncation.
    print("\nEnhanced text before token truncation:")
    print(enhanced_text)
    
    # Truncate to at most max_tokens tokens (splitting on whitespace).
    tokens = enhanced_text.split()
    limited_text = " ".join(tokens[:max_tokens])
    return limited_text

if __name__ == "__main__":
    print("Loading DeepSeek R1 model for text generation...")
    deepseek_pipe = load_deepseek_pipeline()
    
    # Generate the base prompt (via custom input or trending topics)
    base_prompt = generate_dynamic_prompts(deepseek_pipe, region_code="US")
    print(f"\nBase prompt: {base_prompt}")
    
    # Enhance the base prompt and limit the result to 77 tokens.
    final_enhanced_prompt = enhance_prompt(deepseek_pipe, base_prompt, max_tokens=77)
    print(f"\nFinal Enhanced Prompt (77 tokens max): {final_enhanced_prompt}")
    
    # This variable is the prompt container used by other files.
    prompt = final_enhanced_prompt
    
    # For debugging, show the prompt container.
    print("\nPrompt Container to be passed to other modules:")
    print(prompt)
    
    print("DeepSeek R1 model unloaded.")
