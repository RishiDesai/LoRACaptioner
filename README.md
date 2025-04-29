# AutoCaptioner
A tool to automatically 
* generate detailed image captions to train higher-quality LoRA and 
* optimize your prompts during inference.

<div style="text-align: center;">
  <img src="examples/caption_example.gif" alt="Captioning Example" width="600"/>
</div>

## What is AutoCaptioner?

AutoCaptioner creates detailed, principled image captions for your LoRA dataset. These captions can be used to:
- Train more expressive LoRAs on Flux or SDXL
- Make inference easy via prompt optimization
- Save time compared to manual captioning or ignoring captioning

## Installation

### Prerequisites
- Python 3.11 or higher
- [Together API](https://together.ai/) account and API key


### Setup

1. Create the virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   python -m pip install -r requirements.txt
   ```

2. Set your Together API key: `TOGETHER_API_KEY`

3. Run inference on one set of images:

   ```bash
   python main.py --input examples/ --output output/
   ```

   <details>
   <summary>Arguments</summary>

   - `--input` (str): Directory containing images to caption.
   - `--output` (str): Directory to save images and captions (defaults to input directory).
   - `--fix_outfit` (flag): Indicate if character has one outfit (for consistent descriptions).
   - `--batch_images` (flag): Process images in batches by category.
   </details>


## Gradio Web Interface

Launch a user-friendly web interface for captioning and prompt optimization:
```bash
python demo.py
```

### Features

- High-accuracy image captioning with detailed contextual descriptions
- Consistent character descriptions when using the outfit flag
- Batch processing for large image collections
- Optimized for AI model training datasets
- Web interface for easy use

## How It Works

AutoCaptioner leverages the Llama-4-Maverick model through the Together AI platform to:
1. Analyze the visual content of your images
2. Generate detailed, structured captions
3. Save the captions as text files alongside your images

## Notes
- Images are processed individually in standard mode
- For large collections, batch processing by category is recommended
- Each caption is saved as a .txt file with the same name as the image

### Troubleshooting

- **API errors**: Ensure your Together API key is set correctly
- **Unsupported formats**: Only .png, .jpg, .jpeg, and .webp files are supported
- **Memory issues**: For very large images, try processing in smaller batches

### Examples

<table>
  <tr>
    <th>Original Image</th>
    <th>Generated Caption</th>
  </tr>
  <tr>
    <td><img src="examples/landscape.jpg" alt="Landscape" width="300"/></td>
    <td>"tr1gger photorealistic, mountain landscape, hiking gear and outdoor clothing, standing at viewpoint, awestruck, snow-capped peaks and valley, golden sunset light, wide-angle view"</td>
  </tr>
  <tr>
    <td><img src="examples/city.jpg" alt="City" width="300"/></td>
    <td>"tr1gger photorealistic, urban architecture, business suit with briefcase, walking on sidewalk, focused expression, downtown skyscrapers, evening city lights, street-level view"</td>
  </tr>
  <tr>
    <td><img src="examples/food.jpg" alt="Food" width="300"/></td>
    <td>"tr1gger photorealistic, culinary presentation, chef's uniform and hat, plating dish, concentrated, modern restaurant kitchen, soft studio lighting, overhead camera angle"</td>
  </tr>
</table>

## License

[MIT License](LICENSE)