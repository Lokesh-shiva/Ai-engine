import os
import torch
import gc
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM

# Model configuration: Use env var or default to DeepSeek model.
MODEL_NAME = os.environ.get("HF_MODEL_NAME", "deepseek-ai/DeepSeek-R1-Distill-Qwen-14B")

# Define offload folder and max memory configuration for GPU
offload_folder = "./offload"
if not os.path.exists(offload_folder):
    os.makedirs(offload_folder)

max_memory = {"cuda:0": "40GB"} if torch.cuda.is_available() else None

# Mitigate memory fragmentation issues
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"


def unload_model(model):
    """Unload the model from GPU memory to free resources."""
    del model
    torch.cuda.empty_cache()
    gc.collect()


def initialize_model():
    """
    Initialize the DeepSeek R1 Distill model with offloading and CPU fallback.
    """
    try:
        print(f"Initializing model: {MODEL_NAME}")
        # Try GPU mode first if available
        if torch.cuda.is_available():
            try:
                device_map = "sequential"  # Load layers sequentially to reduce peak memory usage
                torch_dtype = torch.float16
                tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
                model = AutoModelForCausalLM.from_pretrained(
                    MODEL_NAME,
                    torch_dtype=torch_dtype,
                    device_map=device_map,
                    trust_remote_code=True,
                    offload_folder=offload_folder,
                    max_memory=max_memory
                )
                generator = pipeline("text-generation", model=model, tokenizer=tokenizer, device=0)
                print("Model loaded on GPU with offloading.")
                return generator
            except Exception as gpu_error:
                print(f"GPU mode failed: {gpu_error}. Falling back to CPU mode.")
        # CPU fallback
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            torch_dtype=torch.float32,
            device_map="cpu",
            trust_remote_code=True
        )
        generator = pipeline("text-generation", model=model, tokenizer=tokenizer, device=-1)
        print("Model loaded on CPU.")
        return generator

    except Exception as e:
        print(f"Error initializing DeepSeek model: {e}")
        return None


def generate_tags(prompt, model):
    """
    Generate and sanitize tags using DeepSeek.
    """
    try:
        print(f"Generating tags for prompt: {prompt}")
        # Explicitly enable truncation to avoid warnings.
        response = model(
            prompt,
            max_length=50,
            truncation=True,
            num_return_sequences=1,
            do_sample=True,
            top_k=50,
            top_p=0.9
        )
        raw_output = response[0]["generated_text"]

        # Check for placeholder or invalid responses
        if "<think>" in raw_output.lower() or raw_output.strip() == "":
            print("Invalid model output. Using fallback tags.")
            return ["#trending", "#AI", "#innovation"]

        # Split output into potential tags
        raw_tags = raw_output.replace("\n", ",").replace("|", ",").split(",")
        clean_tags = [tag.strip() for tag in raw_tags if tag.strip()]
        hashtags = [f"#{tag.replace(' ', '_')[:50]}" for tag in clean_tags][:10]

        return hashtags
    except Exception as e:
        print(f"Error generating tags: {e}")
        return ["#trending", "#AI", "#innovation"]


def clean_tags(tags):
    """
    Sanitize and clean up the tags.
    """
    try:
        valid_tags = []
        for tag in tags:
            cleaned_tag = ''.join(c for c in tag if c.isalnum() or c == "_").strip()
            if len(cleaned_tag) > 2:
                valid_tags.append(cleaned_tag[:50])
        return valid_tags[:10] if valid_tags else ["#trending", "#AI", "#innovation"]
    except Exception as e:
        print(f"Error sanitizing tags: {e}")
        return ["#trending", "#AI", "#innovation"]


if __name__ == "__main__":
    generator = initialize_model()

    if generator is None:
        print("Error: Model failed to initialize.")
        exit(1)

    prompt = "Generate hashtags for a video about AI image generation, Stable Diffusion, and technology trends."
    raw_tags = generate_tags(prompt, generator)

    if isinstance(raw_tags, list) and raw_tags:
        tags = clean_tags(raw_tags)
        print("Generated Tags:", tags)
    else:
        print("Fallback Tags:", ["#AI", "#StableDiffusion", "#AIContentCreation"])

    # Unload model after use to free memory
    unload_model(generator)
