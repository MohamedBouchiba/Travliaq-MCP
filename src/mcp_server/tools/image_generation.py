# mcp_images_supabase.py
import io, os, time, uuid, re, mimetypes
from pathlib import Path
from typing import Iterable, Optional, Literal, Dict, Any, Tuple
import requests
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "TRIPS")
STABLE_BASE = "https://api.stability.ai/v2beta/stable-image/generate"
STABLE_ULTRA = f"{STABLE_BASE}/ultra"
STABLE_CORE = f"{STABLE_BASE}/core"


def _require_env():
    if not STABILITY_API_KEY:
        raise RuntimeError("STABILITY_API_KEY missing")
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
    if xs is None: return ""
    return xs if isinstance(xs, str) else ", ".join([s for s in xs if s])


NEG_COMMON = "ai artifacts, cgi, illustration, painting, blurry, soft focus, lowres, overprocessed hdr, heavy vignette, banding, color fringing, oversaturated, posterized, watermark, text, logo, frame, over/underexposed, distortion"


def build_hero_prompt(city: str, country: str, theme_keywords: Iterable[str] | str | None = None) -> Tuple[str, str]:
    tk = _join(theme_keywords)
    p = f"{city} {country}, cinematic wide travel hero, immersive sense of escape, sweeping vista, {tk}, authentic local life hints, rich textures, natural color grading, golden hour soft light, RAW photo, full-frame DSLR, 24–35mm wide-angle, f/5.6, ISO 100, 1/250s, daylight WB, rule of thirds, leading lines, balanced composition, photorealistic, high dynamic range, travel magazine"
    return p, NEG_COMMON


def build_background_prompt(activity: str, city: str, country: str, mood_keywords: Iterable[str] | str | None = None) -> \
Tuple[str, str]:
    mk = _join(mood_keywords)
    p = f"{activity} in {city} {country}, background to match the trip hero palette, immersive but uncluttered, {mk}, soft depth of field, gentle contrast, clean edges, natural colors, consistent lighting with hero, RAW photo, full-frame DSLR, 35–50mm, f/4, ISO 200, 1/160s, photorealistic, editorial travel style"
    n = "busy clutter, harsh lighting, signage dominance, oversaturated, extreme bokeh, motion blur, noise, ai artifacts"
    return p, n


def build_slider_prompt(subject: str, place: str, city: str, country: str) -> Tuple[str, str]:
    p = f"close-up of {subject} at {place} in {city} {country}, tactile textures, precise details, clean background separation, natural color, soft directional museum lighting, RAW photo, full-frame DSLR, 90–105mm macro, f/4, ISO 400, 1/125s, tripod, minimal reflections, polarizing filter effect, photorealistic editorial detail shot"
    n = "glare, fingerprints, glass reflections, noisy shadows, text overlay, overprocessed hdr, ai artifacts, lowres, blur"
    return p, n


def _stability_post(url: str, fields: Dict[str, Any]) -> bytes:
    h = {"Authorization": f"Bearer {STABILITY_API_KEY}", "Accept": "image/*"}
    files = {k: (None, str(v)) for k, v in fields.items() if v is not None}
    r = requests.post(url, headers=h, files=files, timeout=180)
    if r.status_code == 200:
        return r.content
    try:
        raise RuntimeError(f"{r.status_code} {r.json()}")
    except Exception:
        raise RuntimeError(f"{r.status_code} {r.text[:800]}")


def _ultra_16x9(prompt: str, negative: str, seed: int = 0) -> bytes:
    return _stability_post(STABLE_ULTRA, {"prompt": prompt, "negative_prompt": negative, "aspect_ratio": "16:9",
                                          "output_format": "jpeg", "seed": seed})


def _core_aspect(prompt: str, negative: str, aspect_ratio: str, fmt: Literal["jpeg", "webp"], seed: int = 0,
                 style_preset: str = "photographic") -> bytes:
    return _stability_post(STABLE_CORE, {"prompt": prompt, "negative_prompt": negative, "aspect_ratio": aspect_ratio,
                                         "output_format": fmt, "style_preset": style_preset, "seed": seed})


def _cover_resize(img: Image.Image, w: int, h: int) -> Image.Image:
    iw, ih = img.size
    s = max(w / iw, h / ih)
    nw, nh = int(iw * s), int(ih * s)
    img2 = img.resize((nw, nh), Image.LANCZOS)
    l, t = (nw - w) // 2, (nh - h) // 2
    return img2.crop((l, t, l + w, t + h))


def _encode(img: Image.Image, fmt: Literal["JPEG", "WEBP"], max_kb: int, q: int) -> bytes:
    last = None
    while q >= 50:
        bio = io.BytesIO()
        if fmt == "JPEG":
            img.save(bio, format="JPEG", quality=q, optimize=True, progressive=True)
        else:
            img.save(bio, format="WEBP", quality=q, method=6)
        b = bio.getvalue()
        if len(b) / 1024 <= max_kb:
            return b
        last = b
        q -= 5
    return last or b


def _supabase_upload(data: bytes, key: str, content_type: str,
                     cache_control: str = "public, max-age=31536000, immutable") -> str:
    url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{key}"
    h = {"Authorization": f"Bearer {SUPABASE_SERVICE_KEY}", "apikey": SUPABASE_SERVICE_KEY,
         "Content-Type": content_type, "x-upsert": "true", "Cache-Control": cache_control}
    r = requests.put(url, headers=h, data=data, timeout=180)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"Supabase upload {r.status_code} {r.text[:200]}")
    return f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{key}"


def _choose_best(variants: list[bytes]) -> bytes:
    return max(variants, key=len)


def _build_key(folder: str, filename: str) -> str:
    return f"{folder.strip('/')}/{filename}"


def tool_generate_hero(city: str, country: str, theme_keywords: Iterable[str] | str | None = None,
                       trip_name: Optional[str] = None, trip_folder: Optional[str] = None, width: int = 1920,
                       height: int = 1080, fmt: Literal["JPEG", "WEBP"] = "JPEG", max_kb: int = 500, quality: int = 85,
                       shots: int = 1, seed: int = 0) -> str:
    _require_env()
    folder = _build_folder(trip_name, trip_folder)
    p, n = build_hero_prompt(city, country, theme_keywords)
    outs = []
    for _ in range(max(1, shots)):
        b = _ultra_16x9(p, n, seed=seed if seed else 0)
        outs.append(b)
    raw = _choose_best(outs)
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    img = _cover_resize(img, width, height)
    ext = ".jpg" if fmt == "JPEG" else ".webp"
    data = _encode(img, fmt, max_kb, quality)
    ctype = "image/jpeg" if fmt == "JPEG" else "image/webp"
    key = _build_key(folder, f"hero_{int(time.time())}{ext}")
    return _supabase_upload(data, key, ctype)


def tool_generate_background(activity: str, city: str, country: str, mood_keywords: Iterable[str] | str | None = None,
                             trip_name: Optional[str] = None, trip_folder: Optional[str] = None, width: int = 1920,
                             height: int = 1080, fmt: Literal["JPEG", "WEBP"] = "JPEG", max_kb: int = 400,
                             quality: int = 80, shots: int = 1, seed: int = 0,
                             style_preset: str = "photographic") -> str:
    _require_env()
    folder = _build_folder(trip_name, trip_folder)
    p, n = build_background_prompt(activity, city, country, mood_keywords)
    outs = []
    for _ in range(max(1, shots)):
        b = _core_aspect(p, n, "16:9", "jpeg" if fmt == "JPEG" else "webp", seed=seed if seed else 0,
                         style_preset=style_preset)
        outs.append(b)
    raw = _choose_best(outs)
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    img = _cover_resize(img, width, height)
    ext = ".jpg" if fmt == "JPEG" else ".webp"
    data = _encode(img, fmt if fmt in ("JPEG", "WEBP") else "JPEG", max_kb, quality)
    ctype = "image/jpeg" if fmt == "JPEG" else "image/webp"
    key = _build_key(folder, f"background_{int(time.time())}{ext}")
    return _supabase_upload(data, key, ctype)


def tool_generate_slider(subject: str, place: str, city: str, country: str, trip_name: Optional[str] = None,
                         trip_folder: Optional[str] = None, width: int = 800, height: int = 600,
                         fmt: Literal["WEBP", "JPEG"] = "WEBP", max_kb: int = 150, quality: int = 80, shots: int = 1,
                         seed: int = 0, style_preset: str = "photographic") -> str:
    _require_env()
    folder = _build_folder(trip_name, trip_folder)
    p, n = build_slider_prompt(subject, place, city, country)
    outs = []
    for _ in range(max(1, shots)):
        b = _core_aspect(p, n, "5:4", "webp" if fmt == "WEBP" else "jpeg", seed=seed if seed else 0,
                         style_preset=style_preset)
        outs.append(b)
    raw = _choose_best(outs)
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    img = _cover_resize(img, width, height)
    ext = ".webp" if fmt == "WEBP" else ".jpg"
    data = _encode(img, "WEBP" if fmt == "WEBP" else "JPEG", max_kb, quality)
    ctype = "image/webp" if fmt == "WEBP" else "image/jpeg"
    key = _build_key(folder, f"slider_{int(time.time())}{ext}")
    return _supabase_upload(data, key, ctype)
