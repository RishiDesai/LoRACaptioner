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

<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; max-width: 520px; margin: 20px auto;">
  <img src="examples/sukuna_4.png" alt="Sukuna example 4" style="width: 100%; height: auto;">
  <img src="examples/sukuna_5.png" alt="Sukuna example 5" style="width: 100%; height: auto;">
  <img src="examples/sukuna_6.png" alt="Sukuna example 6" style="width: 100%; height: auto;">
  <img src="examples/sukuna_7.png" alt="Sukuna example 7" style="width: 100%; height: auto;">
</div>

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

<div class="examples-grid">
  <div class="example-container">
    <h5>User Prompt:</h5>
    <p class="simple-prompt">holding a bow and arrow in a dense forest</p>
    
    <h5>Optimized Prompt:</h5>
    <p class="optimized-prompt">tr1gg3r anime-style, pink spiky hair and black markings on face, shirtless with dark arm bands, holding bow and arrow, focused expression, dense forest, soft dappled lighting, three-quarter view</p>
    
    <div class="example-image">
      <img src="examples/sukuna_1.png" alt="Sukuna with bow and arrow">
    </div>
  </div>
  
  <div class="example-container">
    <h5>User Prompt:</h5>
    <p class="simple-prompt">drinking coffee in a san francisco cafe, white cloak, side view</p>
    
    <h5>Optimized Prompt:</h5>
    <p class="optimized-prompt">tr1gg3r anime-style, spiky pink hair and facial markings, white cloak, sitting with cup in hand, neutral expression, cafe interior with san francisco view, soft natural lighting, side profile</p>
    
    <div class="example-image">
      <img src="examples/sukuna_2.png" alt="Sukuna drinking coffee">
    </div>
  </div>
  
  <div class="example-container">
    <h5>User Prompt:</h5>
    <p class="simple-prompt">playing pick-up basketball on a sunny day</p>
    
    <h5>Optimized Prompt:</h5>
    <p class="optimized-prompt">tr1gg3r photorealistic, athletic build, sleeveless basketball jersey and shorts, jumping with ball, focused expression, outdoor basketball court with spectators, bright sunlight, low-angle view</p>
    
    <div class="example-image">
      <img src="examples/sukuna_3.png" alt="Sukuna playing basketball">
    </div>
  </div>
</div>


<div class="examples-grid">
  <div class="example-container">
    <h5>User Prompt:</h5>
    <p class="simple-prompt">riding a horse on a prairie during sunset</p>
    
    <h5>Optimized Prompt:</h5>
    <p class="optimized-prompt">tr1gger photorealistic, curly shoulder-length hair, floral button-up shirt, riding a horse, neutral expression, prairie during sunset, warm directional lighting, three-quarter view</p>
    
    <div class="example-image">
      <img src="examples/woman_1.png" alt="Woman riding a horse">
    </div>
  </div>
  
  <div class="example-container">
    <h5>User Prompt:</h5>
    <p class="simple-prompt">painting on a canvas in an art studio, side-view</p>
    
    <h5>Optimized Prompt:</h5>
    <p class="optimized-prompt">tr1gg3r photorealistic, curly shoulder-length hair, floral button-up shirt, standing at an angle with brush in hand, neutral expression, art studio with canvas and paints, soft natural lighting, right side profile</p>
    
    <div class="example-image">
      <img src="examples/woman_2.png" alt="Woman painting in studio">
    </div>
  </div>
  
  <div class="example-container">
    <h5>User Prompt:</h5>
    <p class="simple-prompt">standing on a skyscraper in a dense city, dramatic stormy lighting, rear view</p>
    
    <h5>Optimized Prompt:</h5>
    <p class="optimized-prompt">tr1gg3r photorealistic, curly shoulder-length hair, floral button-up shirt, standing upright, neutral expression, skyscraper rooftop in dense city, dramatic stormy lighting, back view</p>
    
    <div class="example-image">
      <img src="examples/woman_3.png" alt="Woman on skyscraper">
    </div>
  </div>
</div>

## License

[MIT License](LICENSE)

<style>
.examples-grid {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin: 1rem 0;
}

.example-container {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 1rem;
  background-color: #f9f9f9;
}

.example-container h5 {
  margin-top: 0;
  margin-bottom: 0.25rem;
  color: #333;
}

.simple-prompt {
  font-weight: bold;
  margin-bottom: 0.5rem;
}

.optimized-prompt {
  font-family: monospace;
  background-color: #f0f0f0;
  padding: 0.5rem;
  border-radius: 4px;
  white-space: pre-wrap;
  word-break: break-word;
  margin-bottom: 0.75rem;
}

.example-image img {
  width: 100%;
  max-width: 400px;
  border-radius: 4px;
  display: block;
  margin: 0 auto;
}

@media (min-width: 768px) {
  .examples-grid {
    gap: 1.5rem;
  }

  .example-container {
    padding: 1.25rem;
  }
}
</style>
