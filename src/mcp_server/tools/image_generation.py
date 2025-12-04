import base64
import io
import os
import time
import requests
from typing import Optional, Literal
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "TRIPS")

# Constants
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/images/generations"
DEFAULT_MODEL = "google/gemini-2.5-flash-image-preview" # Correct ID for NanoBanana/Gemini Flash
SITE_URL = os.getenv("OPENROUTER_SITE", "https://travliaq.local")
APP_NAME = "Travliaq Image Generator"

def _validate_env():
    if not OPENROUTER_KEY:
        raise RuntimeError("Missing OPENROUTER_KEY environment variable.")
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables.")

def _upload_to_supabase(image_data: bytes, trip_code: str, filename: str, content_type: str) -> str:
    """Uploads bytes to Supabase Storage and returns the public URL."""
    _validate_env()
    
    # Path: TRIPS/{trip_code}/{filename}
    # Ensure trip_code is clean
    clean_code = "".join(c for c in trip_code if c.isalnum() or c in "-_").strip()
    if not clean_code:
        clean_code = "uncategorized"
        
    storage_path = f"{clean_code}/{filename}"
    url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{storage_path}"
    
    headers = {
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "apikey": SUPABASE_SERVICE_KEY,
        "Content-Type": content_type,
        "x-upsert": "true",
    }
    
    try:
        response = requests.post(url, headers=headers, data=image_data, timeout=60)
        # Supabase sometimes returns 200 for updates, 201 for creates
        if response.status_code not in (200, 201):
             raise RuntimeError(f"Supabase upload failed ({response.status_code}): {response.text}")
    except Exception as e:
        raise RuntimeError(f"Failed to upload to Supabase: {str(e)}")

    # Construct Public URL
    return f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{storage_path}"

def _generate_image_openrouter(prompt: str, width: int, height: int) -> bytes:
    """Calls OpenRouter Chat API to generate an image (NanoBanana/Gemini)."""
    _validate_env()
    
    # Use Chat Completions for Gemini/NanoBanana
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "HTTP-Referer": SITE_URL,
        "X-Title": APP_NAME,
        "Content-Type": "application/json"
    }
    
    # Determine aspect ratio for the prompt
    # Supported: 1:1, 16:9, 4:3, etc.
    ratio = "16:9" if width > height else "4:3" if width < height else "1:1"
    
    payload = {
        "model": DEFAULT_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "modalities": ["image", "text"],
        "image_config": {
            "aspect_ratio": ratio
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        
        if response.status_code != 200:
            try:
                error_json = response.json()
                error_msg = error_json.get("error", {}).get("message", response.text)
            except Exception:
                error_msg = response.text
            raise RuntimeError(f"OpenRouter API Error ({response.status_code}): {error_msg}")
            
        data = response.json()
        
        # Parse response according to documentation
        # choices[0].message.images[0].image_url.url (Base64 data URL)
        
        if "choices" not in data or not data["choices"]:
             raise RuntimeError(f"OpenRouter returned no choices. Response: {data}")
             
        message = data["choices"][0]["message"]
        
        # Check for images field
        if "images" not in message or not message["images"]:
             # Fallback: sometimes models return text if they refuse or fail to generate
             content = message.get("content", "")
             raise RuntimeError(f"No images returned. Model output: {content}")
             
        image_obj = message["images"][0]
        image_url = image_obj.get("image_url", {}).get("url")
        
        if not image_url:
             raise RuntimeError("Image object missing 'url' field.")
             
        # Handle Base64 Data URL
        if image_url.startswith("data:image"):
            # Format: data:image/png;base64,iVBORw0KGgo...
            header, encoded = image_url.split(",", 1)
            return base64.b64decode(encoded)
        else:
            # Handle regular URL if returned (though docs say base64 for this model usually)
            img_response = requests.get(image_url, timeout=60)
            if img_response.status_code != 200:
                raise RuntimeError(f"Failed to download generated image from {image_url}")
            return img_response.content
        
    except requests.exceptions.JSONDecodeError:
        raise RuntimeError(f"OpenRouter returned invalid JSON (Status {response.status_code}). Raw response: {response.text[:500]}...")
    except Exception as e:
        raise RuntimeError(f"Image generation failed: {str(e)}")

def _process_and_upload(
    raw_bytes: bytes, 
    trip_code: str, 
    prefix: str, 
    target_width: int, 
    target_height: int
) -> str:
    """Resizes (if needed), converts to JPEG, and uploads."""
    try:
        img = Image.open(io.BytesIO(raw_bytes))
        
        # Ensure RGB
        if img.mode != "RGB":
            img = img.convert("RGB")
            
        # Resize if dimensions don't match exactly (OpenRouter might return nearest supported size)
        if img.size != (target_width, target_height):
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=90, optimize=True)
        jpeg_bytes = output.getvalue()
        
        filename = f"{prefix}_{int(time.time())}.jpg"
        return _upload_to_supabase(jpeg_bytes, trip_code, filename, "image/jpeg")
        
    except Exception as e:
        raise RuntimeError(f"Failed to process/upload image: {str(e)}")

# --- Public Tools ---

def generate_hero(trip_code: str, prompt: str) -> str:
    """
    Generates a high-quality Hero image (1920x1080).
    """
    width, height = 1920, 1080
    
    # Enhanced prompt for Hero quality
    enhanced_prompt = (
        f"{prompt}. "
        "Cinematic lighting, wide angle, high resolution, photorealistic, "
        "travel photography, vibrant colors, 8k, highly detailed."
    )
    
    raw_bytes = _generate_image_openrouter(enhanced_prompt, width, height)
    return _process_and_upload(raw_bytes, trip_code, "hero", width, height)

def generate_background(trip_code: str, prompt: str) -> str:
    """
    Generates a Background image (1920x1080), optimized for opacity/overlay.
    """
    width, height = 1920, 1080
    
    # Enhanced prompt for Background (softer, less busy)
    enhanced_prompt = (
        f"{prompt}. "
        "Soft focus, blurred background, atmospheric, minimal details, "
        "suitable for text overlay, muted tones, travel theme."
    )
    
    raw_bytes = _generate_image_openrouter(enhanced_prompt, width, height)
    return _process_and_upload(raw_bytes, trip_code, "background", width, height)

def generate_slider(trip_code: str, prompt: str) -> str:
    """
    Generates a Slider image (800x600).
    """
    width, height = 800, 600
    
    # Enhanced prompt for Slider (descriptive)
    enhanced_prompt = (
        f"{prompt}. "
        "Photorealistic, clear focus, beautiful composition, "
        "daylight, travel guide style."
    )
    
    raw_bytes = _generate_image_openrouter(enhanced_prompt, width, height)
    return _process_and_upload(raw_bytes, trip_code, "slider", width, height)
