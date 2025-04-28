import gradio as gr
import os
import zipfile
from io import BytesIO
import PIL.Image
import time
import tempfile
from main import process_images, collect_images_by_category, write_captions  # Import the CLI functions
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Maximum number of images
MAX_IMAGES = 30

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

def process_uploaded_images(image_paths, batch_by_category=False):
    """Process uploaded images using the same code path as CLI"""
    try:
        print(f"Processing {len(image_paths)} images, batch_by_category={batch_by_category}")
        # Create a temporary directory to store the images
        with tempfile.TemporaryDirectory() as temp_dir:
            # Copy images to temp directory and maintain original order
            temp_image_paths = []
            original_to_temp = {}  # Map original paths to temp paths
            for path in image_paths:
                filename = os.path.basename(path)
                temp_path = os.path.join(temp_dir, filename)
                with open(path, 'rb') as src, open(temp_path, 'wb') as dst:
                    dst.write(src.read())
                temp_image_paths.append(temp_path)
                original_to_temp[path] = temp_path
            
            print(f"Created {len(temp_image_paths)} temporary files")
            
            # Convert temp_dir to Path object for collect_images_by_category
            temp_dir_path = Path(temp_dir)
            
            # Process images using the CLI code path
            images_by_category, image_paths_by_category = collect_images_by_category(temp_dir_path)
            print(f"Collected images into {len(images_by_category)} categories")
            
            # Get all images and paths in the correct order
            all_images = []
            all_image_paths = []
            for path in image_paths:  # Use original order
                temp_path = original_to_temp[path]
                found = False
                for category, paths in image_paths_by_category.items():
                    if temp_path in [str(p) for p in paths]:  # Convert Path objects to strings for comparison
                        idx = [str(p) for p in paths].index(temp_path)
                        all_images.append(images_by_category[category][idx])
                        all_image_paths.append(path)  # Use original path
                        found = True
                        break
                if not found:
                    print(f"Warning: Could not find image {path} in categorized data")
            
            print(f"Collected {len(all_images)} images in correct order")
            
            # Process based on batch setting
            if batch_by_category:
                # Process each category separately
                captions = [""] * len(image_paths)  # Initialize with empty strings
                for category, images in images_by_category.items():
                    category_paths = image_paths_by_category[category]
                    print(f"Processing category '{category}' with {len(images)} images")
                    # Use the same code path as CLI
                    from caption import caption_images
                    category_captions = caption_images(images, category=category, batch_mode=True)
                    print(f"Generated {len(category_captions)} captions for category '{category}'")
                    print("Category captions:", category_captions)  # Debug print category captions
                    
                    # Map captions back to original paths
                    for temp_path, caption in zip(category_paths, category_captions):
                        temp_path_str = str(temp_path)
                        for orig_path, orig_temp in original_to_temp.items():
                            if orig_temp == temp_path_str:
                                idx = image_paths.index(orig_path)
                                captions[idx] = caption
                                break
            else:
                # Process all images at once
                from caption import caption_images
                print(f"Processing all {len(all_images)} images at once")
                all_captions = caption_images(all_images, batch_mode=False)
                print(f"Generated {len(all_captions)} captions")
                print("All captions:", all_captions)  # Debug print all captions
                captions = [""] * len(image_paths)
                for path, caption in zip(all_image_paths, all_captions):
                    idx = image_paths.index(path)
                    captions[idx] = caption
            
            print(f"Returning {len(captions)} captions")
            print("Final captions:", captions)  # Debug print final captions
            return captions
            
    except Exception as e:
        print(f"Error in processing: {e}")
        raise

# Main Gradio interface
with gr.Blocks() as demo:
    gr.Markdown("# Image Autocaptioner")
    
    # Store uploaded images
    stored_image_paths = gr.State([])
    batch_by_category = gr.State(True)  # State to track if batch by category is enabled
    
    # Upload component
    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("### Upload your images")
            image_upload = gr.File(
                file_count="multiple", 
                label="Drop your files here", 
                file_types=["image"],
                type="filepath"
            )
        
        with gr.Column(scale=1):
            autocaption_btn = gr.Button("Autocaption Images", variant="primary", interactive=False)
            status_text = gr.Markdown("Upload images to begin", visible=True)
            
            # Advanced settings dropdown
            with gr.Accordion("Advanced", open=False):
                batch_category_checkbox = gr.Checkbox(
                    label="Batch by category", 
                    value=True,
                    info="Group similar images together when processing"
                )
    
    # Create a container for the captioning area (initially hidden)
    with gr.Column(visible=False) as captioning_area:
        gr.Markdown("### Your images and captions")
        
        # Create individual image and caption rows
        image_rows = []
        image_components = []
        caption_components = []
        
        for i in range(MAX_IMAGES):
            with gr.Row(visible=False) as img_row:
                image_rows.append(img_row)
                
                img = gr.Image(
                    label=f"Image {i+1}",
                    type="filepath",
                    show_label=False, 
                    height=200,
                    width=200,
                    scale=1
                )
                image_components.append(img)
                
                caption = gr.Textbox(
                    label=f"Caption {i+1}",
                    lines=3,
                    scale=2
                )
                caption_components.append(caption)
        
        # Add download button
        download_btn = gr.Button("Download Images with Captions", variant="secondary", interactive=False)
        download_output = gr.File(label="Download Zip", visible=False)

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
            gr.update(interactive=True),  # autocaption_btn
            gr.update(interactive=True),  # download_btn
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
            print(f"Starting captioning for {len(image_paths)} images")
            captions = process_uploaded_images(image_paths, batch_category)
            print(f"Generated {len(captions)} captions")
            print("Sample captions:", captions[:2])  # Debug print first two captions
            
            gr.Info("Captioning complete!")
            status = gr.update(value="✅ Captioning complete")
        except Exception as e:
            print(f"Error in captioning: {str(e)}")
            gr.Error(f"Captioning failed: {str(e)}")
            captions = [f"Error: {str(e)}" for _ in image_paths]
            status = gr.update(value=f"❌ Error: {str(e)}")
        
        # Update caption textboxes
        caption_updates = []
        for i in range(MAX_IMAGES):
            if i < len(captions):
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
    
    # Update the upload_outputs
    upload_outputs = [
        stored_image_paths,
        captioning_area,
        autocaption_btn,
        download_btn,
        download_output,
        status_text,
        *image_rows
    ]
    
    # Update both paths and images in a single flow
    def process_upload(files):
        # First get paths and visibility updates
        image_paths, captioning_update, autocaption_update, download_btn_update, download_output_update, status_update, *row_updates = load_captioning(files)
        
        # Then get image updates
        image_updates = update_images(image_paths)
        
        # Update caption labels with filenames
        caption_label_updates = update_caption_labels(image_paths)
        
        # Return all updates together
        return [image_paths, captioning_update, autocaption_update, download_btn_update, download_output_update, status_update] + row_updates + image_updates + caption_label_updates
    
    # Combined outputs for both functions
    combined_outputs = upload_outputs + image_components + caption_components
    
    image_upload.change(
        process_upload,
        inputs=[image_upload],
        outputs=combined_outputs
    )
    
    # Set up batch category checkbox
    batch_category_checkbox.change(
        update_batch_setting,
        inputs=[batch_category_checkbox],
        outputs=[batch_by_category]
    )
    
    # Manage the captioning status
    def on_captioning_start():
        return gr.update(value="⏳ Processing captions... please wait"), gr.update(interactive=False)
    
    def on_captioning_complete():
        return gr.update(value="✅ Captioning complete"), gr.update(interactive=True)
    
    # Set up captioning button
    autocaption_btn.click(
        on_captioning_start,
        inputs=None,
        outputs=[status_text, autocaption_btn]
    ).success(
        run_captioning,
        inputs=[stored_image_paths, batch_by_category],
        outputs=caption_components + [status_text]
    ).success(
        on_captioning_complete,
        inputs=None,
        outputs=[status_text, autocaption_btn]
    )
    
    # Set up download button
    download_btn.click(
        create_zip_from_ui,
        inputs=[stored_image_paths] + caption_components,
        outputs=[download_output]
    ).then(
        lambda: gr.update(visible=True),
        inputs=None,
        outputs=[download_output]
    )

if __name__ == "__main__":
    demo.launch(share=True)
