import os
import scipy
import torch
from diffusers import AudioLDM2Pipeline
from dotenv import load_dotenv
import traceback

# Load environment variables from .env
load_dotenv()

def generate_audio_with_audioldm2(prompt, negative_prompt=None, output_path="generated_audio.wav", 
                                  num_inference_steps=200, audio_length_in_s=10.0, num_waveforms=1, seed=0):
    """
    Generate AI audio using the AudioLDM2 model.

    Args:
        prompt (str): Text describing the audio to generate.
        negative_prompt (str): Text describing what to avoid in the audio.
        output_path (str): Path to save the generated audio file.
        num_inference_steps (int): Number of inference steps for generation.
        audio_length_in_s (float): Length of the generated audio in seconds.
        num_waveforms (int): Number of waveforms to generate per prompt.
        seed (int): Random seed for reproducibility.

    Returns:
        str: Path to the generated audio file if successful, None otherwise.
    """
    try:
        print("Initializing AudioLDM2 pipeline...")
        repo_id = "cvssp/audioldm2"
        pipe = AudioLDM2Pipeline.from_pretrained(repo_id, torch_dtype=torch.float16)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        pipe = pipe.to(device)

        # Set the random seed for reproducibility
        generator = torch.Generator(device).manual_seed(seed)

        # Generate audio
        print(f"Generating audio for prompt: '{prompt}'")
        audio = pipe(
            prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=num_inference_steps,
            audio_length_in_s=audio_length_in_s,
            num_waveforms_per_prompt=num_waveforms,
            generator=generator,
        ).audios

        # Save the best audio (first waveform) to the output path
        print(f"Saving generated audio to: {output_path}")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        scipy.io.wavfile.write(output_path, rate=16000, data=audio[0])
        
        print(f"Audio generated and saved successfully: {output_path}")
        return output_path

    except Exception as e:
        print(f"Error generating audio: {e}")
        traceback.print_exc()
        return None


# Example Usage
if __name__ == "__main__":
    example_prompt = "A relaxing piano melody in a calm environment."
    negative_example_prompt = "No noise or distortion."
    output_file = "output_audio/relaxing_piano.wav"

    generate_audio_with_audioldm2(
        prompt=example_prompt,
        negative_prompt=negative_example_prompt,
        output_path=output_file,
        num_inference_steps=200,
        audio_length_in_s=20.0,
        num_waveforms=1,
        seed=42
    )
