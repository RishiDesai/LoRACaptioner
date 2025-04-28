import base64
import io
import os
from together import Together
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

def get_prompt():
    return """Automated Image Captioning (for LoRA Training)

Role: You are an expert AI captioning system generating precise, structured descriptions for character images optimized for LoRA model training in Stable Diffusion and Flux.1-dev.

IMPORTANT: You MUST follow these rules EXACTLY:
1. EVERY caption MUST start with the word "tr1gger" (exactly like this, no variations)
2. You MUST use the exact format: tr1gger [Style], [Notable Visual Features], [Clothing], [Pose], [Expression], [Lighting], [Camera Angle]
3. DO NOT include any additional text, explanations, or formatting
4. DO NOT use bullet points, lists, or any other formatting
5. DO NOT include any text before or after the caption
6. If you don't follow this format exactly, the caption will be rejected

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
tr1gger [Style], [Notable Visual Features], [Clothing], [Pose], [Expression/Mood], [Background/Setting], [Lighting], [Camera Angle]

Captioning Principles:
- Emphasize visual variation and context-specific details (outfit, pose, lighting, expression, camera angle).
- Exclude constant traits unless clearly deviating.
- Include visible clothing and accessories.
- Clearly define pose and facial expression (neutral, smiling, aggressive).
- Specify lighting conditions (soft lighting, harsh shadows, glowing backlight).
- Explicitly state camera angle (e.g., front view, right side profile, low-angle, high-angle, overhead).
- Avoid mentioning real or fictional identities.
- Always prefix with the trigger word "tr1gger."

Examples (MUST FOLLOW THIS EXACT FORMAT):
tr1gger photorealistic, combat gear, tactical vest and gloves, standing in profile, neutral, empty room, overcast lighting, side profile
tr1gger 3D-rendered, digital patterns, hooded cloak, seated cross-legged, calm, meditation chamber, low ambient lighting, front view
tr1gger anime-style, school uniform with blue necktie, standing with arms behind back, gentle smile, classroom, soft daylight, three-quarter view
tr1gger photorealistic, long trench coat and combat boots, walking, determined, rain-soaked street, dramatic shadows, low-angle view

REMEMBER: Your response must be a single line starting with "tr1gger" and following the exact format above. No additional text, formatting, or explanations are allowed.
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
        raise ValueError("TOGETHER_API_KEY is not set in the environment.")
    return Together(api_key=api_key)

def extract_trigger_caption(line):
    """Extract 'tr1gger' caption from a line of text."""
    if "tr1gger" in line:
        # If caption doesn't start with tr1gger but contains it, extract just that part
        if not line.startswith("tr1gger"):
            return line[line.index("tr1gger"):]
        return line
    return ""

def caption_single_image(client, img_str):
    """Process and caption a single image."""
    messages = [
        {"role": "system", "content": get_prompt()},
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
        model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        messages=messages
    )
    
    # Extract caption from the response
    full_response = response.choices[0].message.content.strip()
    
    # Look for the trigger line in the response
    caption = ""
    for line in full_response.splitlines():
        caption = extract_trigger_caption(line)
        if caption:
            break
    
    # Check if caption is valid
    if not caption:
        error_msg = "Failed to extract a valid caption (containing 'tr1gger') from the response"
        error_msg += f"\n\nActual response:\n{full_response}"
        raise CaptioningError(error_msg)
    
    return caption

def caption_batch_images(client, image_strings, category):
    """Process and caption multiple images in a single batch request."""
    # Create a content array with all images
    content = [{"type": "text", "text": f"Here is the batch of images for {category}. Please caption each image on a separate line, starting each caption with 'tr1gger'."}]
    
    # Add all images to the content array
    for i, img_str in enumerate(image_strings):
        content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_str}"}})
        content.append({"type": "text", "text": f"Image {i+1}"})
    
    # Send the batch request
    messages = [
        {"role": "system", "content": get_prompt()},
        {"role": "user", "content": content}
    ]
    
    response = client.chat.completions.create(
        model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        messages=messages
    )
    
    return process_batch_response(response, image_strings)

def process_batch_response(response, image_strings):
    """Process the API response from a batch request and extract captions."""
    # Parse the response to extract captions for each image
    full_response = response.choices[0].message.content.strip()
    lines = full_response.splitlines()
    
    # Extract captions from the response
    image_count = len(image_strings)
    captions = [""] * image_count  # Initialize with empty strings
    
    # Extract lines that start with or contain "tr1gger"
    tr1gger_lines = [line for line in lines if "tr1gger" in line]
    
    # Assign captions to images
    for i in range(image_count):
        if i < len(tr1gger_lines):
            caption = extract_trigger_caption(tr1gger_lines[i])
            captions[i] = caption
    
    validate_batch_captions(captions, image_count, full_response)
    return captions

def validate_batch_captions(captions, image_count, full_response):
    """Validate captions extracted from a batch response."""
    # Check if all captions are empty or don't contain the trigger word
    valid_captions = [c for c in captions if c and "tr1gger" in c]
    if not valid_captions:
        error_msg = "Failed to parse any valid captions from batch response. Response contained no lines with 'tr1gger'"
        error_msg += f"\n\nActual response:\n{full_response}"
        raise CaptioningError(error_msg)
    
    # Check if some captions are missing
    if len(valid_captions) < image_count:
        missing_count = image_count - len(valid_captions)
        invalid_captions = [(i, c) for i, c in enumerate(captions) if not c or "tr1gger" not in c]
        error_msg = f"Failed to parse captions for {missing_count} of {image_count} images in batch mode"
        error_msg += "\n\nMalformed captions:"
        for idx, caption in invalid_captions:
            error_msg += f"\nImage {idx+1}: '{caption}'"
        raise CaptioningError(error_msg)

def caption_images(images, category=None, batch_mode=False):
    """Caption a list of images, either individually or in batch mode."""
    # Convert PIL images to base64 encoded strings
    image_strings = images_to_base64(images)
    
    # Initialize the API client
    client = get_together_client()
    
    # Process images based on the mode
    if batch_mode and category:
        return caption_batch_images(client, image_strings, category)
    else:
        # Process each image individually
        return [caption_single_image(client, img_str) for img_str in image_strings]

def extract_captions(file_path):
    captions = []
    with open(file_path, 'r') as file:
        for line in file:
            if line.startswith("tr1gger"):
                captions.append(line.strip())
    return captions
