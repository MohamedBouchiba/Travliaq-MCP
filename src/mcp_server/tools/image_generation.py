import base64
import io
import os
import re
import time
import uuid
from typing import Any, Dict, Iterable, Literal, Optional, Tuple

import requests
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "TRIPS")
OPENROUTER_IMAGE_URL = "https://openrouter.ai/api/v1/images"
DEFAULT_MODEL = os.getenv("OPENROUTER_IMAGE_MODEL", "google/nanobanana-mini-flash")
OPENROUTER_SITE = os.getenv("OPENROUTER_SITE", "https://travliaq.local")


def _require_env():
    if not OPENROUTER_KEY:
        raise RuntimeError("OPENROUTER_KEY missing")
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise RuntimeError("SUPABASE_URL or SUPABASE_SERVICE_KEY missing")


def _slugify(x: str) -> str:
    x = re.sub(r"[^\w\s-]", "", x, flags=re.U).strip().lower()
    x = re.sub(r"[-\s]+", "-", x, flags=re.U)
    return x[:80] if x else "trip"


def _unique_id() -> str:
    return uuid.uuid4().hex[:10]


def _build_folder(trip_name: Optional[str], trip_folder: Optional[str]) -> str:
    if trip_folder:
        return trip_folder.strip().strip("/")
    base = _slugify(trip_name or "trip")
    return f"{base}-{_unique_id()}"


def _join(xs: Iterable[str] | str | None) -> str:
    if xs is None:
        return ""
    return xs if isinstance(xs, str) else ", ".join([s for s in xs if s])


NEG_COMMON = (
    "ai artifacts, cgi, illustration, painting, blurry, soft focus, lowres, overprocessed hdr, "
    "heavy vignette, banding, color fringing, oversaturated, posterized, watermark, text, logo, frame, "
    "over/underexposed, distortion"
)


def build_hero_prompt(city: str, country: str, theme_keywords: Iterable[str] | str | None = None) -> Tuple[str, str]:
    tk = _join(theme_keywords)
    p = (
        f"{city} {country}, cinematic wide travel hero, immersive sense of escape, sweeping vista, {tk}, "
        "authentic local life hints, rich textures, natural color grading, golden hour soft light, RAW photo, "
        "full-frame DSLR, 24–35mm wide-angle, f/5.6, ISO 100, 1/250s, daylight WB, rule of thirds, leading lines, "
        "balanced composition, photorealistic, high dynamic range, travel magazine"
    )
    return p, NEG_COMMON


def build_background_prompt(
    activity: str, city: str, country: str, mood_keywords: Iterable[str] | str | None = None
) -> Tuple[str, str]:
    mk = _join(mood_keywords)
    p = (
        f"{activity} in {city} {country}, background to match the trip hero palette, immersive but uncluttered, {mk}, "
        "soft depth of field, gentle contrast, clean edges, natural colors, consistent lighting with hero, RAW photo, "
        "full-frame DSLR, 35–50mm, f/4, ISO 200, 1/160s, photorealistic, editorial travel style"
    )
    n = "busy clutter, harsh lighting, signage dominance, oversaturated, extreme bokeh, motion blur, noise, ai artifacts"
    return p, n


def build_slider_prompt(subject: str, place: str, city: str, country: str) -> Tuple[str, str]:
    p = (
        f"close-up of {subject} at {place} in {city} {country}, tactile textures, precise details, clean background "
        "separation, natural color, soft directional museum lighting, RAW photo, full-frame DSLR, 90–105mm macro, f/4, "
        "ISO 400, 1/125s, tripod, minimal reflections, polarizing filter effect, photorealistic editorial detail shot"
    )
    n = "glare, fingerprints, glass reflections, noisy shadows, text overlay, overprocessed hdr, ai artifacts, lowres, blur"
    return p, n


def _openrouter_post(
    prompt: str,
    negative: str,
    size: str,
    fmt: Literal["jpeg", "png", "webp"],
    seed: int,
    quality: Optional[int] = None,
) -> bytes:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "HTTP-Referer": OPENROUTER_SITE,
        "X-Title": "Travliaq Image Generator",
    }
    payload: Dict[str, Any] = {
        "model": DEFAULT_MODEL,
        "prompt": f"{prompt}\nNegative: {negative}" if negative else prompt,
        "size": size,
        "response_format": "b64_json",
        "n": 1,
        "output_format": fmt,
    }
    if seed:
        payload["seed"] = seed
    if quality is not None:
        payload["quality"] = quality
    r = requests.post(OPENROUTER_IMAGE_URL, headers=headers, json=payload, timeout=180)
    if r.status_code != 200:
        try:
            detail = r.json()
        except Exception:
            detail = r.text
        raise RuntimeError(f"OpenRouter image error {r.status_code}: {detail}")
    try:
        data = r.json()
    except Exception:
        raise RuntimeError(f"OpenRouter returned invalid JSON (status {r.status_code}): {r.text[:500]}")
    items = data.get("data") or []
    if not items:
        raise RuntimeError("OpenRouter image response missing data")
    b64 = items[0].get("b64_json")
    if not b64:
        raise RuntimeError("OpenRouter image response missing b64_json")
    return base64.b64decode(b64)


def _cover_resize(img: Image.Image, w: int, h: int) -> Image.Image:
    iw, ih = img.size
    s = max(w / iw, h / ih)
    nw, nh = int(iw * s), int(ih * s)
    img2 = img.resize((nw, nh), Image.LANCZOS)
    l, t = (nw - w) // 2, (nh - h) // 2
    return img2.crop((l, t, l + w, t + h))


def _encode(img: Image.Image, fmt: Literal["JPEG", "WEBP", "PNG"], max_kb: int, q: int) -> bytes:
    last = None
    while q >= 50:
        bio = io.BytesIO()
        if fmt == "JPEG":
            img.save(bio, format="JPEG", quality=q, optimize=True, progressive=True)
        elif fmt == "WEBP":
            img.save(bio, format="WEBP", quality=q, method=6)
        else:
            img.save(bio, format="PNG", optimize=True)
        b = bio.getvalue()
        if len(b) / 1024 <= max_kb:
            return b
        last = b
        q -= 5
    return last or b


def _supabase_upload(data: bytes, key: str, content_type: str,
                     cache_control: str = "public, max-age=31536000, immutable") -> str:
    url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{key}"
    h = {
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "apikey": SUPABASE_SERVICE_KEY,
        "Content-Type": content_type,
        "x-upsert": "true",
        "Cache-Control": cache_control,
    }
    r = requests.put(url, headers=h, data=data, timeout=180)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"Supabase upload {r.status_code} {r.text[:200]}")
    return f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{key}"


def _build_key(folder: str, filename: str) -> str:
    return f"{folder.strip('/')}/{filename}"


def _generate_image(
    prompt: str,
    negative: str,
    width: int,
    height: int,
    fmt: Literal["JPEG", "WEBP", "PNG"],
    seed: int,
    quality: Optional[int] = None,
) -> Image.Image:
    raw = _openrouter_post(prompt, negative, f"{width}x{height}", fmt.lower(), seed, quality)
    return Image.open(io.BytesIO(raw)).convert("RGB")


def tool_generate_hero(
    city: str,
    country: str,
    theme_keywords: Iterable[str] | str | None = None,
    style_preset: Optional[str] = None,
    trip_name: Optional[str] = None,
    trip_folder: Optional[str] = None,
    width: int = 1920,
    height: int = 1080,
    fmt: Literal["JPEG", "WEBP", "PNG"] = "JPEG",
    max_kb: int = 500,
    quality: int = 85,
    shots: int = 1,
    seed: int = 0,
) -> str:
    _require_env()
    folder = _build_folder(trip_name, trip_folder)
    p, n = build_hero_prompt(city, country, theme_keywords)
    if style_preset:
        p = f"{style_preset} style, {p}"
    imgs = []
    for _ in range(max(1, shots)):
        img = _generate_image(p, n, width, height, fmt, seed if seed else 0)
        imgs.append(img)
    img = max(imgs, key=lambda im: im.size[0] * im.size[1])
    img = _cover_resize(img, width, height)
    ext = ".jpg" if fmt == "JPEG" else ".webp" if fmt == "WEBP" else ".png"
    data = _encode(img, fmt, max_kb, quality)
    ctype = "image/jpeg" if fmt == "JPEG" else "image/webp" if fmt == "WEBP" else "image/png"
    key = _build_key(folder, f"hero_{int(time.time())}{ext}")
    return _supabase_upload(data, key, ctype)


def tool_generate_background(
    activity: str,
    city: str,
    country: str,
    mood_keywords: Iterable[str] | str | None = None,
    style_preset: Optional[str] = None,
    trip_name: Optional[str] = None,
    trip_folder: Optional[str] = None,
    width: int = 1920,
    height: int = 1080,
    fmt: Literal["JPEG", "WEBP", "PNG"] = "JPEG",
    max_kb: int = 400,
    quality: int = 80,
    shots: int = 1,
    seed: int = 0,
) -> str:
    _require_env()
    folder = _build_folder(trip_name, trip_folder)
    p, n = build_background_prompt(activity, city, country, mood_keywords)
    if style_preset:
        p = f"{style_preset} style, {p}"
    imgs = []
    for _ in range(max(1, shots)):
        img = _generate_image(p, n, width, height, fmt, seed if seed else 0)
        imgs.append(img)
    img = max(imgs, key=lambda im: im.size[0] * im.size[1])
    img = _cover_resize(img, width, height)
    ext = ".jpg" if fmt == "JPEG" else ".webp" if fmt == "WEBP" else ".png"
    data = _encode(img, fmt, max_kb, quality)
    ctype = "image/jpeg" if fmt == "JPEG" else "image/webp" if fmt == "WEBP" else "image/png"
    key = _build_key(folder, f"background_{int(time.time())}{ext}")
    return _supabase_upload(data, key, ctype)


def tool_generate_slider(
    subject: str,
    place: str,
    city: str,
    country: str,
    style_preset: Optional[str] = None,
    trip_name: Optional[str] = None,
    trip_folder: Optional[str] = None,
    width: int = 800,
    height: int = 600,
    fmt_site: Literal["WEBP", "JPEG", "PNG"] = "WEBP",
    max_kb: int = 150,
    quality: int = 80,
    shots: int = 1,
    seed: int = 0,
) -> str:
    _require_env()
    folder = _build_folder(trip_name, trip_folder)
    p, n = build_slider_prompt(subject, place, city, country)
    if style_preset:
        p = f"{style_preset} style, {p}"
    imgs = []
    for _ in range(max(1, shots)):
        img = _generate_image(p, n, width, height, fmt_site, seed if seed else 0)
        imgs.append(img)
    img = max(imgs, key=lambda im: im.size[0] * im.size[1])
    img = _cover_resize(img, width, height)
    ext = ".webp" if fmt_site == "WEBP" else ".jpg" if fmt_site == "JPEG" else ".png"
    data = _encode(img, fmt_site if fmt_site in ("WEBP", "JPEG") else "PNG", max_kb, quality)
    ctype = "image/webp" if fmt_site == "WEBP" else "image/jpeg" if fmt_site == "JPEG" else "image/png"
    key = _build_key(folder, f"slider_{int(time.time())}{ext}")
    return _supabase_upload(data, key, ctype)
