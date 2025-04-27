import base64
import io
import os
from openai import OpenAI
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

def get_prompt():
    return """Automated Image Captioning (for LoRA Training)

Role: You are an expert AI captioning system generating precise, structured descriptions for AI-generated character images optimized for LoRA model training in Stable Diffusion and Flux.1-dev.

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

Updated Caption Format:  
tr1gger [Style], [Notable Visual Features], [Clothing], [Pose], [Expression], [Lighting], [Camera Angle]

Captioning Principles:
- Emphasize visual variation and context-specific details (outfit, pose, lighting, expression, camera angle).
- Exclude constant traits unless clearly deviating.
- Include visible clothing and accessories.
- Clearly define pose and facial expression (neutral, smiling, aggressive).
- Specify lighting conditions (soft lighting, harsh shadows, glowing backlight).
- Explicitly state camera angle (e.g., front view, right side profile, low-angle, high-angle, overhead).
- Avoid mentioning real or fictional identities.
- Always prefix with the trigger word "tr1gger."

Updated Examples:
- tr1gger photorealistic, tactical vest and gloves, standing in profile, neutral expression, overcast lighting, side profile
- tr1gger 3D-rendered, hooded cloak with digital pattern, seated cross-legged, calm expression, low ambient lighting, front view
- tr1gger anime-style, school uniform with blue necktie, standing with arms behind back, gentle smile, soft daylight, three-quarter view
- tr1gger photorealistic, long trench coat and combat boots, walking through rain-soaked street, determined expression, dramatic shadows, low-angle view
"""

def caption_images(images):
    # Convert PIL images to base64 encoded strings
    image_strings = []
    for image in images:
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        image_strings.append(img_str)
    
    client = OpenAI()
    captions = []

    # Start a separate chat session for each image
    for img_str in image_strings:
        messages = [
            {"role": "system", "content": get_prompt()},
            {
                "role": "user", 
                "content": [
                    {"type": "text", "text": "Caption this image according to the guidelines."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_str}"}}
                ]
            }
        ]
        
        # Request caption for the image in a single chat
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=512  # Adjust max_tokens as needed
        )
        
        # Extract caption from the response
        caption = response.choices[0].message.content.strip()
        captions.append(caption)
    
    return captions

# Example usage
if __name__ == "__main__":
    if not os.environ.get("OPENAI_API_KEY"):
        print("Please update the .env file with your OpenAI API key.")
        exit(1)

    # Load images
    image_paths = ['input/daenyrs_hd.jpg', 'input/girl_body.png']
    images = [Image.open(path).convert("RGB") for path in image_paths]

    # Generate captions
    captions = caption_images(images)
    for i, caption in enumerate(captions):
        print(f"Generated Caption for Image {i+1}: {caption}")
