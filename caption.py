import base64
import io
import os
from together import Together
from PIL import Image

MODEL_ID = "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
TRIGGER_WORD = "tr1gg3r"

def get_system_prompt():
    return f"""Automated Image Captioning (for LoRA Training)

Role: You are an expert AI captioning system generating precise, structured descriptions for character images optimized for LoRA model training in Stable Diffusion and Flux.1-dev.

IMPORTANT: You MUST follow these rules EXACTLY:
1. EVERY caption MUST start with the word "{TRIGGER_WORD}" (exactly like this, no variations)
2. You MUST use the exact format: {TRIGGER_WORD} [Style], [Notable Visual Features], [Clothing], [Pose], [Expression/Mood], [Background/Setting], [Lighting], [Camera Angle]
4. DO NOT use bullet points, lists, or any other formatting
5. DO NOT include any text before or after the caption
6. If you don't follow this format exactly, the caption will be rejected

When a partial caption is provided:
1. PRESERVE THE MEANING of all information from the partial caption
2. You may rephrase or reword sections from the partial caption to better fit the format, as long as the core meaning/content is preserved
3. If an "Outfit Description" is provided, use it in the [Clothing] and/or [Notable Visual Features] sections

General Guidelines:
1. Prioritize Consistency – Maintain uniform descriptions across all images in a dataset. Avoid introducing variation in features that should remain constant (e.g., fixed traits like eye color, hair color, or markings that are inherently part of the concept and handled during model training).
2. Concise and Structured – Only describe visible and significant visual attributes. Use a standardized format for clarity and efficiency.
3. Omit Subjective Language – Do not evaluative or emotional descriptors like "beautiful" or "scary."
4. Focus on Key Visual Cues – Clearly describe clothing, accessories, pose, facial expression, lighting, and camera angle. Mention distinctive features only if variable (e.g., visible scar, glasses).
5. Adapt to Visual Style – Clearly state the artistic style: "anime-style," "photorealistic," "3D-rendered," etc.
6. Standard Format – Ensure captions follow a consistent structure.
7. Remain Objective – Do not reference known characters, franchises, or people, even if recognizable. Describe only what is visually present.

Avoid Describing These Unless Variable Across Dataset or Uncertain from Concept:
- Eye color
- Hair color
- Skin tone
- Tattoos or markings if core to the concept
- Known accessories that always appear (unless outfit-specific)

Caption Format (MUST FOLLOW EXACTLY):  
{TRIGGER_WORD} [Style], [Notable Visual Features], [Clothing], [Pose], [Expression/Mood], [Background/Setting], [Lighting], [Camera Angle]

Captioning Principles:
- Emphasize visual variation and context-specific details (outfit, pose, lighting, expression, camera angle).
- Exclude constant traits unless clearly deviating.
- Include visible clothing and accessories.
- Clearly define pose and facial expression (neutral, smiling, aggressive).
- Specify lighting conditions (soft lighting, harsh shadows, glowing backlight).
- Explicitly state camera angle (e.g., front view, right side profile, low-angle, high-angle, overhead).
- Avoid mentioning real or fictional identities.
- Always prefix with the trigger word "{TRIGGER_WORD}."

Examples (MUST FOLLOW THIS EXACT FORMAT):
{TRIGGER_WORD} photorealistic, combat gear, tactical vest and gloves, standing in profile, neutral, empty room, overcast lighting, side profile
{TRIGGER_WORD} 3D-rendered, digital patterns, hooded cloak, seated cross-legged, calm, meditation chamber, low ambient lighting, front view
{TRIGGER_WORD} anime-style, school uniform with blue necktie, standing with arms behind back, gentle smile, classroom, soft daylight, three-quarter view
{TRIGGER_WORD} photorealistic, long trench coat and combat boots, walking, determined, rain-soaked street, dramatic shadows, low-angle view

REMEMBER: Your response must be a single line starting with "{TRIGGER_WORD}" and following the exact format above. No additional text, formatting, or explanations are allowed.
"""


class CaptioningError(Exception):
    """Exception raised for errors in the captioning process."""
    pass


def images_to_base64(images):
    """Convert a list of PIL images to base64 encoded strings."""
    image_strings = []
    for image in images:
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        image_strings.append(img_str)
    return image_strings


def get_together_client():
    """Initialize and return the Together API client."""
    api_key = os.environ.get("TOGETHER_API_KEY")
    if not api_key:
        raise ValueError("TOGETHER_API_KEY not set!")
    return Together(api_key=api_key)


def extract_caption(line):
    """Extract caption from a line of text."""
    if TRIGGER_WORD in line:
        # If caption doesn't start with trigger_word but contains it, extract just that part
        if not line.startswith(TRIGGER_WORD):
            return line[line.index(TRIGGER_WORD):]
        return line
    return ""


def caption_single_image(client, img_str, partial_caption=None):
    """Process and caption a single image, using a partial caption if available."""
    system_prompt = get_system_prompt()
    if partial_caption:
        system_prompt += f"\nPartial Caption: {partial_caption}"

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_str}"}},
                {"type": "text", "text": "Caption this image."}
            ]
        }
    ]

    # Request caption for the image using Llama 4 Maverick
    response = client.chat.completions.create(
        model=MODEL_ID,
        messages=messages
    )

    full_response = response.choices[0].message.content.strip()
    caption = ""
    for line in full_response.splitlines():
        caption = extract_caption(line)
        if caption:
            break

    if not caption:
        error_msg = f"Failed to extract a valid caption (containing '{TRIGGER_WORD}') from the response"
        error_msg += f"\n\nActual response:\n{full_response}"
        raise CaptioningError(error_msg)

    return caption


def caption_images(images, image_filenames=None, partial_captions=None, reference_image=None):
    """Caption a list of images individually, using partial captions if available.
    
    Args:
        images: List of PIL Image objects
        image_filenames: List of filenames corresponding to the images
        partial_captions: Dictionary mapping filenames to partial captions
        reference_image: Path to a reference image for outfit consistency
    """
    image_strings = images_to_base64(images)

    client = get_together_client()

    # Use partial captions if provided
    if partial_captions is None:
        partial_captions = {}

    # Process reference image if provided
    outfit_description = None
    if reference_image:
        try:
            reference_img = Image.open(reference_image).convert("RGB")
            reference_img_base64 = images_to_base64([reference_img])[0]
            
            # Get outfit description from reference image
            print("Generating outfit description from reference image...")
            outfit_description = get_outfit_description_from_reference(client, reference_img_base64)
            print(f"Using outfit description: '{outfit_description}'")
        except Exception as e:
            print(f"Error processing reference image: {e}")

    # Process each image individually
    captions = []
    
    for i, img_str in enumerate(image_strings):
        filename = image_filenames[i] if image_filenames else None
        partial_caption = partial_captions.get(filename, "") if filename else ""
        
        # If we have a reference outfit description, add it to the partial caption
        if outfit_description:
            if partial_caption:
                partial_caption = f"{partial_caption}\nOutfit Description: {outfit_description}"
            else:
                partial_caption = f"Outfit Description: {outfit_description}"
        
        try:
            caption = caption_single_image(client, img_str, partial_caption)
            captions.append(caption)
        except Exception as e:
            print(f"Error captioning image {filename or f'#{i + 1}'}: {e}")
            captions.append("")
    return captions


def get_outfit_description_from_reference(client, reference_img_base64):
    """Get outfit description from reference image."""
    system_prompt = """You are an expert at describing character outfits for LoRA training. 
Analyze the reference image and extract ONLY the clothing/outfit description.
Your response should be a brief, detailed description of ONLY the outfit/clothing, nothing else.
Do not include style, pose, background, or other elements - ONLY the clothing/outfit.
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user", 
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{reference_img_base64}"}},
                {"type": "text", "text": "Describe ONLY the outfit/clothing in this reference image."}
            ]
        }
    ]

    response = client.chat.completions.create(
        model=MODEL_ID,
        messages=messages
    )

    return response.choices[0].message.content.strip()


def extract_captions(file_path):
    captions = []
    with open(file_path, 'r') as file:
        for line in file:
            if line.startswith(TRIGGER_WORD):
                captions.append(line.strip())
    return captions
