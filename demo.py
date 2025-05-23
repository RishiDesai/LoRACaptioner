import gradio as gr
import os
import zipfile
from io import BytesIO
import time
import tempfile
from pathlib import Path
import shutil

from main import process_images
from prompt import optimize_prompt

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

def process_uploaded_images(image_paths):
    """Process uploaded images using main.py's functions"""
    # Create temporary directories for input and output
    with tempfile.TemporaryDirectory() as temp_input_dir, tempfile.TemporaryDirectory() as temp_output_dir:
        # Copy all images to the temporary input directory
        temp_input_path = Path(temp_input_dir)
        temp_output_path = Path(temp_output_dir)
        
        # Map of original paths to filenames in temp dir
        path_mapping = {}
        
        for i, path in enumerate(image_paths):
            # Keep original filename to preserve categorization
            filename = os.path.basename(path)
            temp_path = temp_input_path / filename
            
            # Copy file to temp directory
            shutil.copy2(path, temp_path)
            path_mapping[str(temp_path)] = str(path)
            
        # Process the images using main.py's function
        process_images(temp_input_dir, temp_output_dir)
        
        # Collect the captions from the output directory
        captions = []
        for orig_path in image_paths:
            # Get the base filename without extension
            base_name = os.path.splitext(os.path.basename(orig_path))[0]
            caption_filename = f"{base_name}.txt"
            caption_path = temp_output_path / caption_filename
            
            # If caption file exists, read it; otherwise use empty string
            if os.path.exists(caption_path):
                with open(caption_path, 'r', encoding='utf-8') as f:
                    caption = f.read()
                captions.append(caption)
            else:
                captions.append("")
        
        return captions

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

def run_captioning(image_paths):
    """Generate captions for the images using the main.py functions"""
    if not image_paths:
        return [gr.update(value="") for _ in range(MAX_IMAGES)] + [gr.update(value="No images to process")]
            
    try:
        print(f"Starting captioning for {len(image_paths)} images")
        captions = process_uploaded_images(image_paths)
        
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
        margin-top: 0px;
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
        height: 100%;
        width: 100%;
        object-fit: contain;
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
    
    /* Tab styling */
    .tabs {
        margin-top: 20px;
    }
    
    /* Prompt optimization tab styling */
    .optimization-status {
        margin-top: 10px;
        padding: 8px;
        border-radius: 4px;
        background-color: #f8f9fa;
    }
    
    /* Input/output boxes for prompt optimization */
    .prompt-box {
        margin-bottom: 15px;
    }
    
    /* Make optimize button stand out */
    .optimize-btn {
        margin-top: 10px;
        margin-bottom: 15px;
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
        
        caption_btn = gr.Button("Caption Images", variant="primary", interactive=False)
        download_btn = gr.Button("Download Images + Captions", variant="secondary", interactive=False)
        download_output = gr.File(label="Download Zip", visible=False)
        status_text = gr.Markdown("Upload images to begin", visible=True)
    
    return config_column, caption_btn, download_btn, download_output, status_text

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
    shared_captions=None
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
    
    # Set up captioning button chain
    caption_chain = caption_btn.click(
        on_captioning_start,
        inputs=None,
        outputs=[status_text, caption_btn]
    ).success(
        run_captioning,
        inputs=[stored_image_paths],
        outputs=caption_components + [status_text]
    ).success(
        on_captioning_complete,
        inputs=None,
        outputs=[status_text, caption_btn, download_btn]
    )
    
    # If shared_captions is provided, add an additional handler to update it
    if shared_captions is not None:
        def extract_valid_captions(*caption_values):
            return [c for c in caption_values if c and c.strip()]
        
        caption_chain.success(
            extract_valid_captions,
            inputs=caption_components,
            outputs=[shared_captions]
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

# ------- Prompt Optimization UI -------

def create_prompt_optimization_ui():
    """Create UI components for prompt optimization tab"""
    with gr.Column(scale=1) as left_column:
        # Left side for caption input
        gr.Markdown("### Upload Captions")
        gr.Markdown("Upload caption files (.txt) or enter captions manually", elem_classes="file-types-info")
        
        captions_upload = gr.File(
            file_count="multiple", 
            label="Upload caption files", 
            file_types=[".txt"],
            type="filepath",
            elem_classes="file-upload-container",
            height=220
        )
        
        manual_captions = gr.Textbox(
            label="Or enter captions manually",
            lines=5,
            placeholder="Enter captions here, one per line",
            elem_classes="prompt-box"
        )
        
        # Add button to use captions from image captioning tab
        use_generated_captions = gr.Button("Use Captions from Manual Entry", variant="secondary")
    
    with gr.Column(scale=1) as right_column:
        # Right side for prompt input and output
        gr.Markdown("### Optimize Prompt")
        gr.Markdown("\n- Craft prompts that match the style of your training captions\n- Enter a simple prompt and receive an optimized version\n", elem_classes=["category-info"])
        
        user_prompt = gr.Textbox(
            label="Enter your prompt",
            lines=3,
            placeholder="Enter the prompt you want to optimize",
            elem_classes="prompt-box"
        )
        
        optimize_btn = gr.Button("Optimize Prompt", variant="primary", elem_classes="optimize-btn")
        
        optimized_prompt = gr.Textbox(
            label="Optimized Prompt",
            lines=5,
            placeholder="Optimized prompt will appear here",
            elem_classes="prompt-box"
        )
        
        optimization_status = gr.Markdown("Enter a prompt and upload captions to begin", elem_classes="optimization-status")
    
    # Return components but NOT info_md (will create it separately in build_ui)
    return (
        left_column, right_column, captions_upload, manual_captions, 
        use_generated_captions, user_prompt, optimize_btn, 
        optimized_prompt, optimization_status
    )

def run_optimization(prompt, caption_files, manual_caption_text):
    """Handle the prompt optimization logic"""
    if not prompt or prompt.strip() == "":
        return "", "Please enter a prompt to optimize"
    
    # Handle different input sources for captions
    caption_list = []
    
    if manual_caption_text and manual_caption_text.strip():
        # Use manually entered captions
        caption_list = [line.strip() for line in manual_caption_text.split("\n") if line.strip()]
    
    elif caption_files and len(caption_files) > 0:
        # Read captions from uploaded files
        for file_path in caption_files:
            if os.path.exists(file_path) and file_path.lower().endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        caption_list.append(content)
    
    if not caption_list:
        return "", "Please upload caption files or enter captions manually"
    
    try:
        # Call the optimize_prompt function from prompt.py
        result = optimize_prompt(prompt, captions_list=caption_list)
        return result, "✅ Prompt optimization complete"
    except Exception as e:
        return "", f"❌ Error optimizing prompt: {str(e)}"

def setup_prompt_optimization_handlers(
    captions_upload, manual_captions, use_generated_captions, 
    user_prompt, optimize_btn, optimized_prompt, 
    optimization_status, shared_captions
):
    """Set up event handlers for prompt optimization tab"""
    # Function to update manual captions with shared ones
    def fill_with_shared_captions(captions_list):
        if not captions_list or len(captions_list) == 0:
            return "No captions available. Generate captions in the Image Captioning tab first."
        return "\n".join(captions_list)
    
    # Connect button to fill manual captions area
    use_generated_captions.click(
        fill_with_shared_captions,
        inputs=[shared_captions],
        outputs=[manual_captions]
    )
    
    # Connect the optimize button to the optimization function
    optimize_btn.click(
        run_optimization,
        inputs=[user_prompt, captions_upload, manual_captions],
        outputs=[optimized_prompt, optimization_status]
    )

# ------- Main Application -------

def build_ui():
    """Build and return the Gradio interface"""
    with gr.Blocks() as demo:
        gr.Markdown("# Image Auto-captioner for LoRA Training")

        gr.Markdown("""Check out the [code](https://github.com/RishiDesai/LoRACaptioner)
                    and see my [blog post](https://rishidesai.github.io/posts/character-lora/) for more information.""")
        
        # Store generated captions for sharing between tabs
        shared_captions = gr.State([])
        
        # Create tabs for different functionality
        with gr.Tabs() as tabs:
            with gr.TabItem("Image Captioning") as captioning_tab:
                # Store uploaded images
                stored_image_paths = gr.State([])
                
                # Create a two-column layout for the entire interface
                with gr.Row():
                    # Create upload area in left column
                    _, image_upload = create_upload_area()
                    
                    # Create config area in right column
                    _, caption_btn, download_btn, download_output, status_text = create_config_area()
                
                # Create captioning area (initially hidden)
                captioning_area, image_rows, image_components, caption_components = create_captioning_area()
                
                # Set up event handlers with shared captions
                setup_event_handlers(
                    image_upload, stored_image_paths, captioning_area, caption_btn, download_btn,
                    download_output, status_text, image_rows, image_components, caption_components,
                    shared_captions
                )
            
            with gr.TabItem("Prompt Optimization") as prompt_tab:
                with gr.Row():
                    # Create prompt optimization UI components
                    (
                        left_column, right_column, captions_upload, manual_captions,
                        use_generated_captions, user_prompt, optimize_btn,
                        optimized_prompt, optimization_status
                    ) = create_prompt_optimization_ui()
                
                # Set up prompt optimization event handlers
                setup_prompt_optimization_handlers(
                    captions_upload, manual_captions, use_generated_captions,
                    user_prompt, optimize_btn, optimized_prompt,
                    optimization_status, shared_captions
                )
        
        # Add CSS styling
        gr.HTML(get_css_styles())
    
    return demo

# Launch the app when run directly
if __name__ == "__main__":
    demo = build_ui()
    demo.launch(share=True)
