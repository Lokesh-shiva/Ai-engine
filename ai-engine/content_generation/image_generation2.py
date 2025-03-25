import sys
import time
import os
import random
import traceback
import torch
import numpy as np
from PIL import Image, ImageEnhance
import torchvision.transforms as T

# Add TotoroUI path
sys.path.append('/teamspace/studios/this_studio/TotoroUI')  

# Import TotoroUI modules
from totoro_extras import nodes_custom_sampler
from totoro import model_management
from nodes import NODE_CLASS_MAPPINGS

# TotoroUI setup
DualCLIPLoader = NODE_CLASS_MAPPINGS["DualCLIPLoader"]()
UNETLoader = NODE_CLASS_MAPPINGS["UNETLoader"]()
RandomNoise = nodes_custom_sampler.NODE_CLASS_MAPPINGS["RandomNoise"]()
BasicScheduler = nodes_custom_sampler.NODE_CLASS_MAPPINGS["BasicScheduler"]()
SamplerCustomAdvanced = nodes_custom_sampler.NODE_CLASS_MAPPINGS["SamplerCustomAdvanced"]()
VAELoader = NODE_CLASS_MAPPINGS["VAELoader"]()
VAEDecode = NODE_CLASS_MAPPINGS["VAEDecode"]()
EmptyLatentImage = NODE_CLASS_MAPPINGS["EmptyLatentImage"]()
BasicGuider = nodes_custom_sampler.NODE_CLASS_MAPPINGS["BasicGuider"]()
KSamplerSelect = nodes_custom_sampler.NODE_CLASS_MAPPINGS["KSamplerSelect"]()

# Load TotoroUI models with optimized memory management
clip = DualCLIPLoader.load_clip("t5xxl_fp8_e4m3fn.safetensors", "clip_l.safetensors", "flux")[0]
unet = UNETLoader.load_unet("flux1-dev-fp8.safetensors", "fp8_e4m3fn")[0]
vae = VAELoader.load_vae("ae.sft")[0]

# Move models to float16 if supported
if isinstance(clip, torch.nn.Module):
    clip = clip.to(dtype=torch.float16)

if isinstance(unet, torch.nn.Module):
    unet = unet.to(dtype=torch.float16)

if isinstance(vae, torch.nn.Module):
    vae = vae.to(dtype=torch.float16)


# Function to round to nearest multiple of 'base'
def closestNumber(x, base):
    return base * round(x / base)


# Function to enhance and generate multiple high-quality images
def generate_images_with_huggingface(prompt, num_images=5, output_dir="generated_images"):
    """
    Generate multiple high-quality images using TotoroUI with memory optimizations.
    """
    print(f"Generating {num_images} images for prompt: '{prompt}' with TotoroUI...")
    generated_images = []

    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        width, height = 768, 768  # Reduced from 1024x1024 to save memory
        steps = 20
        sampler_name = "euler"
        scheduler = "simple"
        seed = random.randint(0, 18446744073709551615)
        print(f"Using seed: {seed}")

        # Encode prompt
        cond, pooled = clip.encode_from_tokens(clip.tokenize(prompt), return_pooled=True)
        cond = [[cond, {"pooled_output": pooled}]]

        # Generate latent image
        latent_image = EmptyLatentImage.generate(closestNumber(width, 16), closestNumber(height, 16))[0]

        for i in range(num_images):
            torch.cuda.empty_cache()  # Free up GPU memory before each image
            with torch.no_grad():  # Disable gradients to save memory
                image_prompt = (
                    f"{prompt}, cinematic, ultra-detailed, 8K resolution, HDR lighting, photorealistic, "
                    f"intricate textures, vivid colors, sharp focus, extremely detailed, perfect composition"
                )
                print(f"Using dynamic prompt: {image_prompt}")

                noise = RandomNoise.get_noise(seed)[0]

                guider = BasicGuider.get_guider(unet, cond)[0]
                sampler = KSamplerSelect.get_sampler(sampler_name)[0]
                sigmas = BasicScheduler.get_sigmas(unet, scheduler, steps, 1.0)[0]

                # Sample from noise
                sample, sample_denoised = SamplerCustomAdvanced.sample(noise, guider, sampler, sigmas, latent_image)

                # Decode image
                # Decode image from latent space
                decoded = VAEDecode.decode(vae, sample)[0].detach().cpu()

# Ensure tensor shape is correct (C, H, W) → (H, W, C)
                if decoded.dim() == 4:  
                    decoded = decoded.squeeze(0)  # Remove batch dimension
                if decoded.shape[0] in [1, 3]:  
                    decoded = decoded.permute(1, 2, 0)  # Convert to (H, W, C)

# Normalize tensor (Scale values between 0-255)
                decoded = (decoded - decoded.min()) / (decoded.max() - decoded.min())  # Normalize
                decoded = (decoded * 255).byte().numpy()  # Convert to uint8

# Convert to PIL image safely
                decoded_image = Image.fromarray(decoded)

# Apply sharpness enhancement
                enhancer = ImageEnhance.Sharpness(decoded_image)
                enhanced_image = enhancer.enhance(1.5)

# Save the image
                file_path = os.path.join(output_dir, f"generated_image_{i + 1}.png")
                enhanced_image.save(file_path)

                generated_images.append(file_path)

                print(f"Image {i+1}/{num_images} saved. Waiting 7 seconds for VRAM recovery...")
                time.sleep(7)  # Increase delay for better VRAM management

        print("Image generation successful.")
        return generated_images
    except Exception as e:
        print(f"Error generating images: {e}")
        traceback.print_exc()
        return []


# Example usage
if __name__ == "__main__":
    prompt = "A futuristic cyberpunk cityscape at night with neon lights"
    generate_images_with_huggingface(prompt)
