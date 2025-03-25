import torch
from diffusers import StableDiffusion3Pipeline
import os
import time

# Load Stable Diffusion 3.5 Turbo
pipe = StableDiffusion3Pipeline.from_pretrained(
    "stabilityai/stable-diffusion-3.5-large-turbo",
    torch_dtype=torch.bfloat16
).to("cuda")

# Optionally enable xFormers memory efficient attention for improved performance
try:
    pipe.enable_xformers_memory_efficient_attention()
except Exception as e:
    print("xFormers memory efficient attention not enabled:", e)

# Ensure output directory exists
output_dir = "generated_images"
os.makedirs(output_dir, exist_ok=True)

def generate_images_with_huggingface(prompt, num_images=2):
    print(f"Generating {num_images} images for prompt: '{prompt}'...")

    generated_images = []
    # Create a fixed generator for reproducibility
    generator = torch.Generator("cuda").manual_seed(42)
    
    for i in range(num_images):
        torch.cuda.empty_cache()  # Free up GPU memory

        # Generate image with increased inference steps and guidance scale
        image = pipe(
            prompt,
            num_inference_steps=50,  # Increased steps for better detail
            guidance_scale=8.5,      # Increased guidance to adhere closer to the prompt
            generator=generator
        ).images[0]

        # Save image
        file_path = os.path.join(output_dir, f"generated_image_{i+1}.png")
        image.save(file_path)
        generated_images.append(file_path)

        print(f"Saved Image {i+1}/{num_images}")
        time.sleep(2)  # Shorter delay for efficiency

    print("Image generation complete.")
    return generated_images

# Example usage
if __name__ == "__main__":
    prompt = "A futuristic cyberpunk cityscape at night with neon lights"
    generate_images_with_huggingface(prompt, num_images=2)
