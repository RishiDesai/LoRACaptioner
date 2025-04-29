import gradio as gr
import os
import zipfile
from io import BytesIO
import time
import tempfile
from main import collect_images_by_category, is_image_file
from pathlib import Path
from caption import caption_images
from PIL import Image

# Maximum number of images
MAX_IMAGES = 30

# ------- File Operations -------

def create_download_file(image_paths, captions):
    """Create a zip file with images and their captions"""
    zip_io = BytesIO()
    with zipfile.ZipFile(zip_io, 'w') as zip_file:
        for i, (image_path, caption) in enumerate(zip(image_paths, captions)):
            # Get original filename without extension
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            img_name = f"{base_name}.png"
            caption_name = f"{base_name}.txt"
            
            # Add image to zip
            with open(image_path, 'rb') as img_file:
                zip_file.writestr(img_name, img_file.read())
            
            # Add caption to zip
            zip_file.writestr(caption_name, caption)
    
    return zip_io.getvalue()

def save_images_to_temp(image_paths, temp_dir):
    """Copy images to temporary directory and return mapping"""
    temp_image_paths = []
    original_to_temp = {}  # Map original paths to temp paths
    
    for path in image_paths:
        # Keep original filename to preserve categorization
        filename = os.path.basename(path)
        temp_path = os.path.join(temp_dir, filename)
        
        # Ensure we're using consistent path formats
        orig_path_str = str(path)
        temp_path_str = str(temp_path)
        
        with open(path, 'rb') as src, open(temp_path, 'wb') as dst:
            dst.write(src.read())
        
        temp_image_paths.append(temp_path_str)
        original_to_temp[orig_path_str] = temp_path_str
        print(f"Copied {orig_path_str} to {temp_path_str}")
    
    print(f"Created {len(temp_image_paths)} temporary files")
    return temp_image_paths, original_to_temp

def process_by_category(images_by_category, image_paths_by_category, image_paths, original_to_temp):
    """Process images by category and map captions back to original images"""
    captions = [""] * len(image_paths)  # Initialize with empty strings
    
    # Create a mapping from temp path to index in the original image_paths
    temp_to_original_idx = {}
    for i, orig_path in enumerate(image_paths):
        if orig_path in original_to_temp:
            temp_to_original_idx[original_to_temp[orig_path]] = i
    
    print(f"Created mapping for {len(temp_to_original_idx)} images")
    
    for category, images in images_by_category.items():
        category_paths = image_paths_by_category[category]
        print(f"Processing category '{category}' with {len(images)} images")
        
        # Create mapping of image to its position in the category
        category_image_map = {}
        for i, (img, path) in enumerate(zip(images, category_paths)):
            category_image_map[str(path)] = i
        
        try:
            # Use the same code path as CLI
            category_captions = caption_images(images, category=category, batch_mode=True)
            print(f"Generated {len(category_captions)} captions for category '{category}'")
            
            # Map captions back to original paths using our direct mapping
            for i, temp_path in enumerate(category_paths):
                temp_path_str = str(temp_path)
                if i < len(category_captions) and temp_path_str in temp_to_original_idx:
                    original_idx = temp_to_original_idx[temp_path_str]
                    captions[original_idx] = category_captions[i]
        except Exception as e:
            print(f"Error processing category '{category}': {e}")
            # Fall back to individual processing for this category
            try:
                print(f"Falling back to individual processing for category '{category}'")
                for i, img in enumerate(images):
                    if i >= len(category_paths):
                        continue
                    temp_path = category_paths[i]
                    temp_path_str = str(temp_path)
                    
                    try:
                        single_captions = caption_images([img], batch_mode=False)
                        if single_captions and len(single_captions) > 0:
                            if temp_path_str in temp_to_original_idx:
                                original_idx = temp_to_original_idx[temp_path_str]
                                captions[original_idx] = single_captions[0]
                    except Exception as inner_e:
                        print(f"Error processing individual image {i} in '{category}': {inner_e}")
            except Exception as fallback_e:
                print(f"Error in fallback processing for '{category}': {fallback_e}")
    
    return captions

def process_all_images(all_images, all_image_paths, image_paths):
    """Process all images at once without categorization"""
    print(f"Processing all {len(all_images)} images at once")
    
    # Initialize empty captions list
    captions = [""] * len(image_paths)  # Initialize with empty strings for all original paths
    
    # If there are no images, return empty captions
    if not all_images:
        print("No images to process, returning empty captions")
        return captions
    
    # Create a mapping from temp paths to original indexes for efficient lookup
    path_to_idx = {str(path): i for i, path in enumerate(image_paths)}
    
    try:
        all_captions = caption_images(all_images, batch_mode=False)
        print(f"Generated {len(all_captions)} captions")
        
        # Map captions to the right images using the prepared image_paths
        for i, (path, caption) in enumerate(zip(all_image_paths, all_captions)):
            if i < len(all_captions) and path in path_to_idx:
                idx = path_to_idx[path]
                captions[idx] = caption
    except Exception as e:
        print(f"Error generating captions: {e}")
    
    return captions

def process_uploaded_images(image_paths, batch_by_category=False):
    """Process uploaded images using the same code path as CLI"""
    try:
        # Convert all image paths to strings for consistency
        image_paths = [str(path) for path in image_paths]
        print(f"Processing {len(image_paths)} images, batch_by_category={batch_by_category}")
        
        # Create temporary directory with images
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save images to temp directory
            temp_image_paths, original_to_temp = save_images_to_temp(image_paths, temp_dir)
            
            # Use Path object for consistency with main.py
            temp_dir_path = Path(temp_dir)
            
            # List files in temp directory for debugging
            print(f"Files in temp directory {temp_dir}:")
            for f in temp_dir_path.iterdir():
                print(f"  - {f} (is_file: {f.is_file()}, is_image: {is_image_file(f.name)})")
            
            # Collect images by category using the function from main.py
            images_by_category, image_paths_by_category = collect_images_by_category(temp_dir_path)
            
            # Print categories and counts for debugging
            print(f"Collected images into {len(images_by_category)} categories")
            for category, images in images_by_category.items():
                print(f"  - Category '{category}': {len(images)} images")
            
            # Check if we actually have images to process
            total_images = sum(len(images) for images in images_by_category.values())
            if total_images == 0:
                print("No images were properly categorized. Adding all images directly.")
                # Add all images directly without categorization
                default_category = "default"
                images_by_category[default_category] = []
                image_paths_by_category[default_category] = []
                
                for path in image_paths:
                    path_str = str(path)
                    try:
                        if path_str in original_to_temp:
                            temp_path = original_to_temp[path_str]
                            temp_path_obj = Path(temp_path)
                            img = Image.open(temp_path).convert("RGB")
                            images_by_category[default_category].append(img)
                            image_paths_by_category[default_category].append(temp_path_obj)
                    except Exception as e:
                        print(f"Error loading image {path}: {e}")
            
            # Map back to original paths for consistent ordering
            all_images = []
            all_image_paths = []
            
            # Create reverse mapping for lookup
            temp_to_orig = {v: k for k, v in original_to_temp.items()}
            
            # Go through each category and map back to original
            for category in images_by_category:
                for i, temp_path in enumerate(image_paths_by_category[category]):
                    temp_path_str = str(temp_path)
                    if temp_path_str in temp_to_orig:
                        orig_path = temp_to_orig[temp_path_str]
                        if i < len(images_by_category[category]):
                            all_images.append(images_by_category[category][i])
                            all_image_paths.append(orig_path)
            
            # Ensure we maintain original order
            ordered_images = []
            ordered_paths = []
            
            for orig_path in image_paths:
                path_str = str(orig_path)
                for i, path in enumerate(all_image_paths):
                    if path == path_str and i < len(all_images):
                        ordered_images.append(all_images[i])
                        ordered_paths.append(path)
                        break
            
            print(f"Collected {len(ordered_images)} images in correct order")
            
            # Process based on batch setting
            if batch_by_category and len(images_by_category) > 0:
                captions = process_by_category(images_by_category, image_paths_by_category, image_paths, original_to_temp)
            else:
                # Use our own function for non-batch mode since it needs to map back to UI
                captions = process_all_images(ordered_images, ordered_paths, image_paths)
            
            print(f"Returning {len(captions)} captions")
            return captions
            
    except Exception as e:
        print(f"Error in processing: {e}")
        raise

# ------- UI Interaction Functions -------

def load_captioning(files):
    """Process uploaded images and show them in the UI"""
    if not files:
        return [], gr.update(visible=False), gr.update(interactive=False), gr.update(interactive=False), gr.update(visible=False), gr.update(value="Upload images to begin"), *[gr.update(visible=False) for _ in range(MAX_IMAGES)]
    
    # Filter to only keep image files
    image_paths = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'))]
    
    if not image_paths or len(image_paths) < 1:
        gr.Warning(f"Please upload at least one image")
        return [], gr.update(visible=False), gr.update(interactive=False), gr.update(interactive=False), gr.update(visible=False), gr.update(value="No valid images found"), *[gr.update(visible=False) for _ in range(MAX_IMAGES)]
    
    if len(image_paths) > MAX_IMAGES:
        gr.Warning(f"Only the first {MAX_IMAGES} images will be processed")
        image_paths = image_paths[:MAX_IMAGES]
    
    # Update row visibility
    row_updates = []
    for i in range(MAX_IMAGES):
        if i < len(image_paths):
            row_updates.append(gr.update(visible=True))
        else:
            row_updates.append(gr.update(visible=False))
    
    return (
        image_paths,  # stored_image_paths
        gr.update(visible=True),  # captioning_area
        gr.update(interactive=True),  # caption_btn
        gr.update(interactive=False),  # download_btn - initially disabled until captioning is done
        gr.update(visible=False),  # download_output
        gr.update(value=f"{len(image_paths)} images ready for captioning"),  # status_text
        *row_updates  # image_rows
    )

def update_images(image_paths):
    """Update the image components with the uploaded images"""
    print(f"Updating images with paths: {image_paths}")
    updates = []
    for i in range(MAX_IMAGES):
        if i < len(image_paths):
            updates.append(gr.update(value=image_paths[i]))
        else:
            updates.append(gr.update(value=None))
    return updates

def update_caption_labels(image_paths):
    """Update caption labels to include the image filename"""
    updates = []
    for i in range(MAX_IMAGES):
        if i < len(image_paths):
            filename = os.path.basename(image_paths[i])
            updates.append(gr.update(label=filename))
        else:
            updates.append(gr.update(label=""))
    return updates

def run_captioning(image_paths, batch_category):
    """Generate captions for the images using the CLI code path"""
    if not image_paths:
        return [gr.update(value="") for _ in range(MAX_IMAGES)] + [gr.update(value="No images to process")]
            
    try:
        print(f"Starting captioning for {len(image_paths)} images, batch_by_category={batch_category}")
        captions = process_uploaded_images(image_paths, batch_category)
        
        # Count valid captions
        valid_captions = sum(1 for c in captions if c and c.strip())
        print(f"Generated {valid_captions} valid captions out of {len(captions)} images")
        
        if valid_captions < len(captions):
            gr.Warning(f"{len(captions) - valid_captions} images could not be captioned properly")
            status = gr.update(value=f"✅ Captioning complete - {valid_captions}/{len(captions)} successful")
        else:
            gr.Info("Captioning complete!")
            status = gr.update(value="✅ Captioning complete")
                
        print("Sample captions:", captions[:2] if len(captions) >= 2 else captions)
    except Exception as e:
        print(f"Error in captioning: {str(e)}")
        gr.Error(f"Captioning failed: {str(e)}")
        captions = [""] * len(image_paths)  # Use empty strings
        status = gr.update(value=f"❌ Error: {str(e)}")
    
    # Update caption textboxes
    caption_updates = []
    for i in range(MAX_IMAGES):
        if i < len(captions) and captions[i]:  # Only set value if we have a valid caption
            caption_updates.append(gr.update(value=captions[i]))
        else:
            caption_updates.append(gr.update(value=""))
    
    print(f"Returning {len(caption_updates)} caption updates")
    return caption_updates + [status]

def update_batch_setting(value):
    """Update the batch by category setting"""
    return value

def create_zip_from_ui(image_paths, *captions_list):
    """Create a zip file from the current images and captions in the UI"""
    # Filter out empty captions for non-existent images
    valid_captions = [cap for i, cap in enumerate(captions_list) if i < len(image_paths) and cap]
    valid_image_paths = image_paths[:len(valid_captions)]
    
    if not valid_image_paths:
        gr.Warning("No images to download")
        return None
    
    # Create zip file
    zip_data = create_download_file(valid_image_paths, valid_captions)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    # Create a temporary file to store the zip
    temp_dir = tempfile.gettempdir()
    zip_filename = f"image_captions_{timestamp}.zip"
    zip_path = os.path.join(temp_dir, zip_filename)
    
    # Write the zip data to the temporary file
    with open(zip_path, "wb") as f:
        f.write(zip_data)
    
    # Return the path to the temporary file
    return zip_path

def process_upload(files, image_rows, image_components, caption_components):
    """Process uploaded files and update UI components"""
    # First get paths and visibility updates
    image_paths, captioning_update, caption_btn_update, download_btn_update, download_output_update, status_update, *row_updates = load_captioning(files)
    
    # Then get image updates
    image_updates = update_images(image_paths)
    
    # Update caption labels with filenames
    caption_label_updates = update_caption_labels(image_paths)
    
    # Return all updates together
    return [image_paths, captioning_update, caption_btn_update, download_btn_update, download_output_update, status_update] + row_updates + image_updates + caption_label_updates

def on_captioning_start():
    """Update UI when captioning starts"""
    return gr.update(value="⏳ Processing captions... please wait"), gr.update(interactive=False)

def on_captioning_complete():
    """Update UI when captioning completes"""
    return gr.update(value="✅ Captioning complete"), gr.update(interactive=True), gr.update(interactive=True)

# ------- UI Style Definitions -------

def get_css_styles():
    """Return CSS styles for the UI"""
    return """
    <style>
    /* Unified styling for the two-column layout */
    #left-column, #right-column {
        padding: 10px;
        align-self: flex-start;
    }
    
    /* Force columns to align at the top */
    .gradio-row {
        align-items: flex-start !important;
    }
    
    /* File upload styling */
    .file-types-info {
        margin-top: -10px;
        font-size: 0.9em;
        color: #666;
    }
    
    .file-upload-container {
        width: 100%;
        max-width: 100%;
    }
    
    .file-upload-container .file-preview {
        max-height: 180px;
        overflow-y: auto;
    }
    
    /* Image and caption rows styling */
    .image-caption-row {
        margin-bottom: 10px;
        padding: 5px;
        border-bottom: 1px solid #eee;
    }
    
    /* Make thumbnails same size */
    .image-thumbnail {
        height: 200px;
        width: 200px;
        object-fit: cover;
    }
    
    /* Center the image thumbnails */
    #left-column, .image-caption-row > div:first-child {
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    /* Ensure the image container itself is centered */
    .image-thumbnail img, .image-thumbnail > div {
        margin: 0 auto;
    }
    
    /* Caption text areas */
    .caption-area {
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    
    /* Download section */
    .download-section {
        margin-top: 10px;
    }
    
    /* Category info */
    .category-info {
        font-size: 0.9em;
        color: #555;
        background-color: #f8f9fa;
        padding: 8px;
        border-radius: 4px;
        margin-bottom: 10px;
        border-left: 3px solid #4CAF50;
    }
    </style>
    """

# ------- UI Component Creation -------

def create_upload_area():
    """Create the upload area components"""
    # Left column for images/upload
    with gr.Column(scale=1, elem_id="left-column") as upload_column:
        # Upload area
        gr.Markdown("### Upload your images", elem_id="upload-heading")
        gr.Markdown("Only .png, .jpg, .jpeg, and .webp files are supported", elem_id="file-types-info", elem_classes="file-types-info")
        image_upload = gr.File(
            file_count="multiple", 
            label="Drop your files here", 
            file_types=["image"],
            type="filepath",
            height=220,
            elem_classes="file-upload-container",
        )
    
    return upload_column, image_upload

def create_config_area():
    """Create the configuration area components"""
    # Right column for configuration and captions
    with gr.Column(scale=1.5, elem_id="right-column") as config_column:
        # Configuration area
        gr.Markdown("### Configuration")
        batch_category_checkbox = gr.Checkbox(
            label="Batch process by category", 
            value=False,
            info="Caption similar images together"
        )
        
        gr.Markdown("""
        **Note about categorization:**
        - Images are grouped by the part of the filename before the last underscore
        - For example: "character_pose_01.png" and "character_pose_02.png" share the category "character_pose"
        - When using "Batch by category", similar images are captioned together for more consistent results
        """, elem_classes=["category-info"])
        
        caption_btn = gr.Button("Caption Images", variant="primary", interactive=False)
        download_btn = gr.Button("Download Images + Captions", variant="secondary", interactive=False)
        download_output = gr.File(label="Download Zip", visible=False)
        status_text = gr.Markdown("Upload images to begin", visible=True)
    
    return config_column, batch_category_checkbox, caption_btn, download_btn, download_output, status_text

def create_captioning_area():
    """Create the captioning area components"""
    with gr.Column(visible=False) as captioning_area:
        # Replace the single heading with a row containing two headings
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Your Images", elem_id="images-heading")
            with gr.Column(scale=1.5):
                gr.Markdown("### Your Captions", elem_id="captions-heading")
        
        # Create individual image and caption rows
        image_rows = []
        image_components = []
        caption_components = []
        
        for i in range(MAX_IMAGES):
            with gr.Row(visible=False, elem_classes=["image-caption-row"]) as img_row:
                image_rows.append(img_row)
                
                # Left column for image
                with gr.Column(scale=1):
                    img = gr.Image(
                        label=f"Image {i+1}",
                        type="filepath",
                        show_label=False, 
                        height=200,
                        width=200,
                        elem_classes=["image-thumbnail"]
                    )
                    image_components.append(img)
                
                # Right column for caption
                with gr.Column(scale=1.5):
                    caption = gr.Textbox(
                        label=f"Caption {i+1}",
                        lines=3,
                        elem_classes=["caption-area"]
                    )
                    caption_components.append(caption)
    
    return captioning_area, image_rows, image_components, caption_components

def setup_event_handlers(
    image_upload, stored_image_paths, captioning_area, caption_btn, download_btn, 
    download_output, status_text, image_rows, image_components, caption_components,
    batch_category_checkbox, batch_by_category
):
    """Set up all event handlers for the UI"""
    # Combined outputs for the upload function
    upload_outputs = [
        stored_image_paths,
        captioning_area,
        caption_btn,
        download_btn,
        download_output,
        status_text,
        *image_rows
    ]
    
    combined_outputs = upload_outputs + image_components + caption_components
    
    # Set up upload handler
    image_upload.change(
        lambda files: process_upload(files, image_rows, image_components, caption_components),
        inputs=[image_upload],
        outputs=combined_outputs
    )
    
    # Set up batch category checkbox
    batch_category_checkbox.change(
        update_batch_setting,
        inputs=[batch_category_checkbox],
        outputs=[batch_by_category]
    )
    
    # Set up captioning button
    caption_btn.click(
        on_captioning_start,
        inputs=None,
        outputs=[status_text, caption_btn]
    ).success(
        run_captioning,
        inputs=[stored_image_paths, batch_by_category],
        outputs=caption_components + [status_text]
    ).success(
        on_captioning_complete,
        inputs=None,
        outputs=[status_text, caption_btn, download_btn]
    )
    
    # Set up download button
    download_btn.click(
        create_zip_from_ui,
        inputs=[stored_image_paths] + caption_components,
        outputs=[download_output]
    ).then(
        lambda: gr.update(visible=True, elem_classes=["download-section"]),
        inputs=None,
        outputs=[download_output]
    ).then(
        lambda: gr.Info("Click the Download button that appeared to save your zip file"),
        inputs=None,
        outputs=None
    )

# ------- Main Application -------

def build_ui():
    """Build and return the Gradio interface"""
    with gr.Blocks() as demo:
        gr.Markdown("# Image Auto-captioner for LoRA Training")
        
        # Store uploaded images
        stored_image_paths = gr.State([])
        batch_by_category = gr.State(False)  # State to track if batch by category is enabled
        
        # Create a two-column layout for the entire interface
        with gr.Row():
            # Create upload area in left column
            _, image_upload = create_upload_area()
            
            # Create config area in right column
            _, batch_category_checkbox, caption_btn, download_btn, download_output, status_text = create_config_area()
        
        # Add CSS styling
        gr.HTML(get_css_styles())
        
        # Create captioning area (initially hidden)
        captioning_area, image_rows, image_components, caption_components = create_captioning_area()
        
        # Set up event handlers
        setup_event_handlers(
            image_upload, stored_image_paths, captioning_area, caption_btn, download_btn,
            download_output, status_text, image_rows, image_components, caption_components,
            batch_category_checkbox, batch_by_category
        )
    
    return demo

# Launch the app when run directly
if __name__ == "__main__":
    demo = build_ui()
    demo.launch(share=True)
