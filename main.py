import os
import argparse
import shutil
import sys
from pathlib import Path
from PIL import Image
from caption import caption_images

def is_image_file(filename):
    """Check if a file is an allowed image type."""
    allowed_extensions = ['.png', '.jpg', '.jpeg', '.webp']
    return any(filename.lower().endswith(ext) for ext in allowed_extensions)

def is_unsupported_image(filename):
    """Check if a file is an image but not of an allowed type."""
    unsupported_extensions = ['.bmp', '.gif', '.tiff', '.tif', '.ico', '.svg']
    return any(filename.lower().endswith(ext) for ext in unsupported_extensions)

def is_text_file(filename):
    """Check if a file is a text file."""
    return filename.lower().endswith('.txt')

def validate_input_directory(input_dir):
    """Validate that the input directory only contains allowed image formats."""
    input_path = Path(input_dir)
    
    unsupported_files = []
    text_files = []
    
    for file_path in input_path.iterdir():
        if file_path.is_file():
            if is_unsupported_image(file_path.name):
                unsupported_files.append(file_path.name)
            elif is_text_file(file_path.name):
                text_files.append(file_path.name)
    
    if unsupported_files:
        print("Error: Unsupported image formats detected.")
        print("Only .png, .jpg, .jpeg, and .webp files are allowed.")
        print("The following files are not supported:")
        for file in unsupported_files:
            print(f"  - {file}")
        sys.exit(1)
    
    if text_files:
        print("Error: Text files detected in the input directory.")
        print("The input directory should only contain image files to prevent overwriting existing text files.")
        print("The following text files were found:")
        for file in text_files:
            print(f"  - {file}")
        sys.exit(1)

def process_images(input_dir, output_dir, fix_outfit=False):
    """Process all images in the input directory and generate captions."""
    input_path = Path(input_dir)
    output_path = Path(output_dir) if output_dir else input_path
    
    # Validate the input directory first
    validate_input_directory(input_dir)
    
    # Create output directory if it doesn't exist
    os.makedirs(output_path, exist_ok=True)
    
    # Track the number of processed images
    processed_count = 0
    
    # Collect all images into a list
    images = []
    image_paths = []

    # Get all files in the input directory
    for file_path in input_path.iterdir():
        if file_path.is_file() and is_image_file(file_path.name):
            try:
                # Load the image
                image = Image.open(file_path).convert("RGB")
                images.append(image)
                image_paths.append(file_path)
            except Exception as e:
                print(f"Error loading {file_path.name}: {e}")

    # Log the number of images found
    print(f"Found {len(images)} images to process.")

    if not images:
        print("No valid images found to process.")
        return

    # Generate captions for all images
    try:
        captions = caption_images(images)
    except Exception as e:
        print(f"Error generating captions: {e}")
        return

    # Write captions to files
    for file_path, caption in zip(image_paths, captions):
        try:
            # Create caption file path (same name but with .txt extension)
            caption_filename = file_path.stem + ".txt"
            caption_path = input_path / caption_filename

            # Write caption to file
            with open(caption_path, 'w', encoding='utf-8') as f:
                f.write(caption)

            # If output directory is different from input, copy files
            if output_path != input_path:
                # Copy image to output directory
                shutil.copy2(file_path, output_path / file_path.name)
                # Copy caption to output directory
                shutil.copy2(caption_path, output_path / caption_filename)

            processed_count += 1
            print(f"Processed {file_path.name} → {caption_filename}")
        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")

    print(f"\nProcessing complete. {processed_count} images were captioned.")

def main():
    parser = argparse.ArgumentParser(description='Generate captions for images using GPT-4o.')
    parser.add_argument('--input', type=str, required=True, help='Directory containing images')
    parser.add_argument('--output', type=str, help='Directory to save images and captions (defaults to input directory)')
    parser.add_argument('--fix_outfit', action='store_true', help='Flag to indicate if character has one outfit')
    
    args = parser.parse_args()
    
    # Validate input directory
    if not os.path.isdir(args.input):
        print(f"Error: Input directory '{args.input}' does not exist.")
        return
    
    # Process images
    process_images(args.input, args.output, args.fix_outfit)

if __name__ == "__main__":
    main() 