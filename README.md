---
title: LoRACaptioner
emoji: 🤠
colorFrom: red
colorTo: green
sdk: gradio
sdk_version: 5.25.2
app_file: demo.py
pinned: false
---

# LoRACaptioner

- **Image Captioning**: Automatically generate detailed and structured captions for your LoRA dataset.
- **Prompt Optimization**: Enhance prompts during inference to achieve high-quality outputs.

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

2. Run inference on one set of images:

   ```bash
   python main.py --input examples/ --output output/
   ```

   <details>
   <summary>Arguments</summary>

   - `--input` (str): Directory containing images to caption.
   - `--output` (str): Directory to save images and captions (defaults to input directory).
   - `--batch_images` (flag): Caption images in batches by category.
   </details>


## Gradio Web Interface

Launch a user-friendly web interface for captioning and prompt optimization:
```bash
python demo.py
```

### Notes
- Images are processed individually in standard mode
- For large collections, batch processing by category is recommended
- Each caption is saved as a .txt file with the same name as the image

### Troubleshooting

- **API errors**: Ensure your Together API key is set and has funds
- **Image formats**: Only .png, .jpg, .jpeg, and .webp files are supported

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