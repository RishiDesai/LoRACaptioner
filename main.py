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
        print("Warning: Text files detected in the input directory.")
        print("The following text files will be overwritten:")
        for file in text_files:
            print(f"  - {file}")


def collect_all_images(input_path):
    """Collect all valid images from the input directory."""
    images = []
    image_paths = []

    for file_path in input_path.iterdir():
        if file_path.is_file() and is_image_file(file_path.name):
            try:
                image = Image.open(file_path).convert("RGB")
                images.append(image)
                image_paths.append(file_path)
            except Exception as e:
                print(f"Error loading {file_path.name}: {e}")

    return images, image_paths


def process_images(input_dir, output_dir, partial_captions={}, reference_image=None):
    """Process all images in the input directory and generate captions."""
    input_path = Path(input_dir)
    output_path = Path(output_dir) if output_dir else input_path

    validate_input_directory(input_dir)
    os.makedirs(output_path, exist_ok=True)

    # Process reference image if provided
    reference_image_path = None
    if reference_image:
        # First check if it's a filename in the input directory
        input_ref_path = input_path / reference_image
        if input_ref_path.exists() and is_image_file(input_ref_path.name):
            reference_image_path = input_ref_path
            print(f"Using reference image from input directory: {reference_image}")
        else:
            # Then check if it's an absolute path
            abs_ref_path = Path(reference_image)
            if abs_ref_path.exists() and is_image_file(abs_ref_path.name):
                reference_image_path = abs_ref_path
                print(f"Using reference image from absolute path: {reference_image}")
            else:
                print(f"Error: Reference image '{reference_image}' not found in input directory or as absolute path.")
                return

    # Collect all images
    images, image_paths = collect_all_images(input_path)

    # Log the number of images found
    total_images = len(images)
    print(f"Found {total_images} images to process.")

    if not total_images:
        print("No valid images found to process.")
        return

    # Process all images individually
    processed_count = 0
    try:
        # Get filenames for all images
        filenames = [path.name for path in image_paths]
        captions = caption_images(images, image_filenames=filenames, 
                                 partial_captions=partial_captions, reference_image=reference_image_path)
        write_captions(image_paths, captions, input_path, output_path)
        processed_count = len(images)
    except Exception as e:
        print(f"Error generating captions: {e}")

    print(f"\nProcessing complete. {processed_count} images were captioned.")


def write_captions(image_paths, captions, input_path, output_path):
    """Helper function to write captions to files."""
    for file_path, caption in zip(image_paths, captions):
        try:
            # Create caption file path (same name but with .txt extension)
            caption_filename = file_path.stem + ".txt"
            caption_path = input_path / caption_filename

            with open(caption_path, 'w', encoding='utf-8') as f:
                f.write(caption)

            # If output directory is different from input, copy files
            if output_path != input_path:
                shutil.copy2(file_path, output_path / file_path.name)
                shutil.copy2(caption_path, output_path / caption_filename)
            print(f"Processed {file_path.name} → {caption_filename}")
        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")


def main():
    parser = argparse.ArgumentParser(description='Generate captions for images using Llama 4 Maverick.')
    parser.add_argument('--input', type=str, required=True, help='Directory containing images')
    parser.add_argument('--output', type=str, help='Directory to save images and captions (defaults to input directory)')
    parser.add_argument('--partial_captions', type=str, help='Path to a JSON file containing partial captions for images')
    parser.add_argument('--reference_image', type=str, help='Reference image for outfit consistency. The outfit from this image will be used in all captions. Can be a filename in the input directory or an absolute path.')

    args = parser.parse_args()

    if not os.path.isdir(args.input):
        print(f"Error: Input directory '{args.input}' does not exist.")
        return

    # Load partial captions if provided
    partial_captions = {}
    if args.partial_captions:
        import json
        with open(args.partial_captions, 'r') as f:
            partial_captions = json.load(f)

    process_images(args.input, args.output, partial_captions, args.reference_image)


if __name__ == "__main__":
    main()
