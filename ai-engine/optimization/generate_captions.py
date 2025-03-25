from transformers import pipeline

def generate_captions(prompt, model_name="gpt2", max_length=100, temperature=0.7):
    """
    Generate captions using a Hugging Face model.
    
    Args:
    - prompt (str): The text prompt for the model.
    - model_name (str): The name of the Hugging Face model (default: "gpt2").
    - max_length (int): The maximum length of the generated text (default: 100).
    - temperature (float): Sampling temperature; higher values = more randomness (default: 0.7).
    
    Returns:
    - str: Generated captions or an error message.
    """
    try:
        # Load the Hugging Face pipeline for text generation
        generator = pipeline("text-generation", model=model_name)
        
        # Generate text based on the prompt
        generated_text = generator(
            prompt,
            max_length=max_length,
            temperature=temperature,
            num_return_sequences=1
        )
        
        # Extract the generated captions
        return generated_text[0]['generated_text']
    
    except Exception as e:
        return f"An error occurred: {str(e)}"

if __name__ == "__main__":
    # Example prompt
    prompt = "Generate captions for a video about AI trends."
    
    # Generate captions using the Hugging Face pipeline
    captions = generate_captions(prompt, model_name="gpt2")
    
    print("Generated Captions:", captions)
