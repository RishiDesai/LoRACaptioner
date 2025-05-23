import os
import argparse
from pathlib import Path
from PIL import Image
from caption import (
    get_system_prompt, 
    get_together_client, 
    extract_captions, 
    MODEL_ID, 
    images_to_base64,
    get_outfit_description_from_reference
)

def optimize_prompt(user_prompt, captions_dir=None, captions_list=None, reference_image=None):
    """Optimize a user prompt to follow the same format as training captions.
    
    Args:
        user_prompt (str): The simple user prompt to optimize
        captions_dir (str, optional): Directory containing caption .txt files
        captions_list (list, optional): List of captions to use instead of loading from files
        reference_image (str, optional): Path to a reference image for outfit consistency
    """
    all_captions = []
    if captions_list:
        all_captions = captions_list
    elif captions_dir:
        # Collect all captions from text files in the directory
        captions_path = Path(captions_dir)
        for file_path in captions_path.glob("*.txt"):
            captions = extract_captions(file_path)
            all_captions.extend(captions)

    if not all_captions:
        raise ValueError("Please provide either caption files or a list of captions!")

    # Concatenate all captions with newlines
    captions_text = "\n".join(all_captions)

    client = get_together_client()
    
    # Process reference image if provided
    outfit_description = None
    if reference_image:
        try:
            ref_img = Image.open(reference_image).convert("RGB")
            ref_img_base64 = images_to_base64([ref_img])[0]
            
            # Get outfit description from reference image
            print("Generating outfit description from reference image...")
            outfit_description = get_outfit_description_from_reference(client, ref_img_base64)
            print(f"Using outfit description: '{outfit_description}'")
        except Exception as e:
            print(f"Error processing reference image: {e}")
    
    # Build the content for the API request
    content = (
        f"These are all of the captions used to train the LoRA:\n\n"
        f"{captions_text}\n\n"
    )
    
    # Add outfit description if available
    if outfit_description:
        content += f"Use this outfit description for the character: {outfit_description}\n\n"
    
    content += f"Now optimize this prompt to follow the caption format used in training: {user_prompt}"
    
    messages = [
        {"role": "system", "content": get_system_prompt()},
        {"role": "user", "content": content}
    ]

    response = client.chat.completions.create(
        model=MODEL_ID,
        messages=messages
    )

    optimized_prompt = response.choices[0].message.content.strip()
    return optimized_prompt


def main():
    parser = argparse.ArgumentParser(description='Optimize prompts based on existing captions.')
    parser.add_argument('--prompt', type=str, required=True, help='User prompt to optimize')
    parser.add_argument('--captions', type=str, required=True, help='Directory containing caption .txt files')
    parser.add_argument('--reference_image', type=str, help='Path to a reference image for outfit consistency')

    args = parser.parse_args()
    if not os.path.isdir(args.captions):
        print(f"Error: Captions directory '{args.captions}' does not exist.")
        return

    try:
        optimized_prompt = optimize_prompt(args.prompt, args.captions, reference_image=args.reference_image)
        print("\nOptimized Prompt:")
        print(optimized_prompt)

    except Exception as e:
        print(f"Error optimizing prompt: {e}")


if __name__ == "__main__":
    main()
