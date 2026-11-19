"""
cinematic.py - Kodla sinematik reklam üretmek için yardımcı kütüphane.

Gereken: Python 3.9+, Pillow, NumPy, ffmpeg (PATH'te).
Kullanım: Örnek için ../ornekler/ornek_parfum_reklami.py dosyasına bak.

Bölümler:
  1. Format ve zaman yardımcıları (easing)
  2. Fontlar ve tipografi
  3. Arka planlar, ışık ve partiküller
  4. Kamera hareketi (Ken Burns / push-in)
  5. Film görünümü (renk düzenleme, vinyet, grain, letterbox)
  6. Render (sahne -> mp4, birleştirme, ses ekleme)
  7. Ses sentezi (drone, pad, riser, whoosh, impact, pulse)
"""
from __future__ import annotations

import math
import os
import shutil
import subprocess
import wave
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------------------------------------------------------------------------
# 1. Format ve zaman
# ---------------------------------------------------------------------------

FORMATS = {
    "9:16": (1080, 1920),  # Reels, Shorts, TikTok
    "16:9": (1920, 1080),  # YouTube, web, TV
    "1:1": (1080, 1080),   # Kare gönderi
    "4:5": (1080, 1350),   # Instagram akış
}
FPS = 30


def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def lerp(a, b, p):
    return a + (b - a) * p


def ease_in_out(p):
    p = clamp(p)
    return 4 * p ** 3 if p < 0.5 else 1 - (-2 * p + 2) ** 3 / 2


def ease_out(p):
    return 1 - (1 - clamp(p)) ** 3


def ease_in(p):
    return clamp(p) ** 3


def ease_out_expo(p):
    p = clamp(p)
    return 1.0 if p >= 1 else 1 - 2 ** (-10 * p)


def linear(p):
    return clamp(p)


def prog(t, start, end, ease=ease_in_out):
    """t anının [start, end] aralığındaki ilerlemesi (0..1), easing uygulanmış."""
    if end <= start:
        return 1.0 if t >= end else 0.0
    return ease((t - start) / (end - start))


def fade_window(t, start, end, fade_in=0.5, fade_out=0.5):
    """Bir öğenin start-end arasında görünür olması için 0..1 opaklık."""
    a = prog(t, start, start + fade_in, ease_out) if fade_in > 0 else float(t >= start)
    b = 1 - prog(t, end - fade_out, end, ease_in) if fade_out > 0 else float(t <= end)
    return clamp(min(a, b))


# ---------------------------------------------------------------------------
# 2. Fontlar ve tipografi
# ---------------------------------------------------------------------------

FONT_DIRS = [
    "/usr/share/fonts", "/usr/local/share/fonts", os.path.expanduser("~/.fonts"),
    "/Library/Fonts", "/System/Library/Fonts", os.path.expanduser("~/Library/Fonts"),
    r"C:\Windows\Fonts",
]

# Rol -> tercih sırasıyla dosya adı parçaları (küçük harf). Hepsi Türkçe karakter destekler.
FONT_ROLES = {
    "display": ["interdisplay-bold", "inter-bold", "montserrat[wght]", "arialbd", "segoeuib", "dejavusans-bold"],
    "black": ["interdisplay-black", "inter-black", "anton-regular", "ariblk", "dejavusans-bold"],
    "light": ["interdisplay-light", "inter-light", "segoeuil", "arial", "dejavusans-extralight"],
    "thin": ["interdisplay-thin", "inter-thin", "interdisplay-extralight", "segoeuisl", "dejavusans-extralight"],
    "regular": ["inter-regular", "segoeui", "arial", "dejavusans"],
    "serif": ["cardo-regular", "crimsontext-regular", "gelasio", "georgia", "times", "dejavuserif"],
    "serif_bold": ["cardo-bold", "crimsontext-bold", "gelasio", "georgiab", "timesbd", "dejavuserif-bold"],
    "condensed": ["anton-regular", "impact", "oswald", "dejavusanscondensed-bold"],
}


@lru_cache(maxsize=1)
def _font_index():
    index = {}
    for d in FONT_DIRS:
        if not os.path.isdir(d):
            continue
        for root, _, files in os.walk(d):
            for f in files:
                if f.lower().endswith((".ttf", ".otf", ".ttc")):
                    stem = os.path.splitext(f)[0].lower()
                    index.setdefault(stem, os.path.join(root, f))
    return index


@lru_cache(maxsize=None)
def font(role="display", size=80, path=None):
    """Rol adıyla ('display', 'light', 'serif'...) ya da dosya yoluyla font yükler."""
    if path:
        return ImageFont.truetype(path, size)
    idx = _font_index()
    for cand in FONT_ROLES.get(role, [role]):
        for stem, p in idx.items():
            if stem == cand or stem.startswith(cand):
                f = ImageFont.truetype(p, size)
                if "[wght]" in stem:  # değişken font: kalınlık ayarla
                    try:
                        f.set_variation_by_axes([700 if role in ("display", "black") else 300])
                    except Exception:
                        pass
                return f
    return ImageFont.load_default(size)


def text_layer(text, fnt, fill=(255, 255, 255), tracking=0.0, line_spacing=1.2, align="center"):
    """Metni şeffaf RGBA katman olarak çizer. tracking: harf arası boşluk (font boyutunun oranı)."""
    lines = text.split("\n")
    size = fnt.size
    gap = tracking * size
    widths = []
    for line in lines:
        w = sum(fnt.getlength(ch) for ch in line) + gap * max(len(line) - 1, 0)
        widths.append(w)
    asc, desc = fnt.getmetrics()
    lh = int((asc + desc) * line_spacing)
    pad = int(size * 0.3)
    W = int(max(widths) + 2 * pad) + 1
    H = int(lh * (len(lines) - 1) + asc + desc + 2 * pad)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    fill = tuple(fill) + ((255,) if len(fill) == 3 else ())
    for i, line in enumerate(lines):
        if align == "center":
            x = (W - widths[i]) / 2
        elif align == "right":
            x = W - pad - widths[i]
        else:
            x = pad
        y = pad + i * lh
        if gap == 0:
            d.text((x, y), line, font=fnt, fill=fill)
        else:
            for ch in line:
                d.text((x, y), ch, font=fnt, fill=fill)
                x += fnt.getlength(ch) + gap
    return layer


def place(canvas, layer, cx, cy, alpha=1.0, scale=1.0, blur=0.0, glow=0.0, glow_color=None):
    """Katmanı canvas üzerine merkezi (cx, cy) olacak şekilde yerleştirir.
    blur: odak açma efekti (piksel), glow: ışıma yarıçapı (piksel)."""
    if alpha <= 0.002:
        return canvas
    lay = layer
    if abs(scale - 1.0) > 1e-3:
        lay = lay.resize((max(1, int(lay.width * scale)), max(1, int(lay.height * scale))), Image.LANCZOS)
    if blur > 0.3:
        b = int(blur * 2) + 4
        big = Image.new("RGBA", (lay.width + 2 * b, lay.height + 2 * b), (0, 0, 0, 0))
        big.paste(lay, (b, b))
        lay = big.filter(ImageFilter.GaussianBlur(blur))
    if glow > 0:
        g = int(glow * 2) + 4
        base = Image.new("RGBA", (lay.width + 2 * g, lay.height + 2 * g), (0, 0, 0, 0))
        base.paste(lay, (g, g))
        halo = base.filter(ImageFilter.GaussianBlur(glow))
        if glow_color is not None:
            tint = Image.new("RGBA", halo.size, tuple(glow_color) + (255,))
            tint.putalpha(halo.getchannel("A"))
            halo = tint
        halo.putalpha(halo.getchannel("A").point(lambda v: int(v * 0.9)))
        lay = Image.alpha_composite(halo, base)
    if alpha < 1.0:
        a = lay.getchannel("A").point(lambda v: int(v * alpha))
        lay = lay.copy()
        lay.putalpha(a)
    x = int(round(cx - lay.width / 2))
    y = int(round(cy - lay.height / 2))
    canvas.alpha_composite(lay, (max(x, 0), max(y, 0)), (max(-x, 0), max(-y, 0)))
    return canvas


def reveal_text(canvas, text, fnt, cx, cy, t, start, dur=1.2, end=None, out=0.6,
                fill=(255, 255, 255), tracking=0.15, track_to=None, rise=40, focus=12, glow=0):
    """Sinematik metin girişi: odak açılması + hafif yükselme + (isteğe bağlı) harf aralığı açılması."""
    end = end if end is not None else 1e9
    a = fade_window(t, start, end, dur, out)
    if a <= 0:
        return canvas
    p = prog(t, start, start + dur, ease_out)
    trk = lerp(tracking, track_to, prog(t, start, end, linear)) if track_to is not None else tracking
    lay = text_layer(text, fnt, fill, tracking=trk)
    return place(canvas, lay, cx, cy + (1 - p) * rise, alpha=a, blur=(1 - p) * focus, glow=glow)


# ---------------------------------------------------------------------------
# 3. Arka plan, ışık ve partiküller
# ---------------------------------------------------------------------------

@lru_cache(maxsize=16)
def _radial(W, H, cx, cy, radius):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt((xx - cx * W) ** 2 + (yy - cy * H) ** 2) / (radius * max(W, H))
    return np.clip(d, 0, 1)


def radial_gradient(size, inner=(40, 30, 20), outer=(0, 0, 0), center=(0.5, 0.45), radius=0.75, power=1.6):
    """Ortası aydınlık, kenarları karanlık zemin. RGBA PIL döndürür."""
    W, H = size
    d = _radial(W, H, round(center[0], 3), round(center[1], 3), round(radius, 3)) ** power
    inner = np.array(inner, np.float32)
    outer = np.array(outer, np.float32)
    img = inner * (1 - d[..., None]) + outer * d[..., None]
    return Image.fromarray(img.astype(np.uint8), "RGB").convert("RGBA")


def linear_gradient(size, top=(10, 10, 20), bottom=(0, 0, 0)):
    W, H = size
    p = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    img = np.array(top, np.float32) * (1 - p) + np.array(bottom, np.float32) * p
    img = np.repeat(img, W, axis=1)
    return Image.fromarray(img.astype(np.uint8), "RGB").convert("RGBA")


def light_sweep(canvas, p, angle=25, width=0.18, strength=0.55, color=(255, 240, 220), mask=None):
    """Görüntü üzerinden geçen yumuşak ışık bandı (ürün parlaması). p: 0..1 konum.
    mask: verilirse (L modunda) ışık sadece o alanda görünür."""
    W, H = canvas.size
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    a = math.radians(angle)
    proj = (xx * math.cos(a) + yy * math.sin(a)) / (W * math.cos(a) + H * math.sin(a))
    pos = lerp(-width, 1 + width, p)
    band = np.exp(-((proj - pos) / width) ** 2 * 4) * strength
    if mask is not None:
        band *= np.asarray(mask, np.float32) / 255.0
    arr = np.asarray(canvas, np.float32)
    rgb = arr[..., :3] + band[..., None] * (np.array(color, np.float32) - arr[..., :3] * 0.3)
    arr[..., :3] = np.clip(rgb, 0, 255)
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def light_rays(size, origin=(0.5, -0.1), n=7, spread=50, color=(255, 230, 190), strength=90, seed=3, blur=40):
    """Volumetrik ışık huzmeleri katmanı (RGBA). Bir kez üretip her karede place ile kullan."""
    W, H = size
    rng = np.random.default_rng(seed)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    ox, oy = origin[0] * W, origin[1] * H
    L = math.hypot(W, H) * 1.5
    for _ in range(n):
        ang = math.radians(90 + rng.uniform(-spread / 2, spread / 2))
        w = math.radians(rng.uniform(1.5, 4.5))
        pts = [(ox, oy),
               (ox + L * math.cos(ang - w), oy + L * math.sin(ang - w)),
               (ox + L * math.cos(ang + w), oy + L * math.sin(ang + w))]
        d.polygon(pts, fill=tuple(color) + (int(strength * rng.uniform(0.4, 1.0)),))
    lay = lay.filter(ImageFilter.GaussianBlur(blur))
    # aşağı doğru sönümlenme
    fall = np.linspace(1, 0.15, H, dtype=np.float32)[:, None]
    a = np.asarray(lay.getchannel("A"), np.float32) * fall
    lay.putalpha(Image.fromarray(a.astype(np.uint8), "L"))
    return lay


@lru_cache(maxsize=32)
def _bokeh_sprite(r, color, softness):
    s = int(r * 2 + softness * 4 + 4)
    spr = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(spr).ellipse([s / 2 - r, s / 2 - r, s / 2 + r, s / 2 + r], fill=tuple(color) + (255,))
    return spr.filter(ImageFilter.GaussianBlur(softness)) if softness > 0 else spr


class Particles:
    """Havada süzülen toz / bokeh ışıkları. draw(canvas, t) ile her karede çizilir."""

    def __init__(self, size, n=60, seed=1, color=(255, 220, 170), r=(2, 9), speed=(5, 25),
                 alpha=(0.15, 0.7), softness=(1, 6), drift=(0, -1)):
        W, H = size
        rng = np.random.default_rng(seed)
        self.size = size
        self.x = rng.uniform(0, W, n)
        self.y = rng.uniform(0, H, n)
        self.r = rng.uniform(*r, n)
        self.v = rng.uniform(*speed, n)
        self.a = rng.uniform(*alpha, n)
        self.soft = rng.uniform(*softness, n)
        self.ph = rng.uniform(0, 2 * math.pi, n)
        self.color = tuple(color)
        self.drift = drift

    def draw(self, canvas, t, opacity=1.0):
        W, H = self.size
        for i in range(len(self.x)):
            x = (self.x[i] + self.drift[0] * self.v[i] * t + 12 * math.sin(t * 0.7 + self.ph[i])) % W
            y = (self.y[i] + self.drift[1] * self.v[i] * t) % H
            a = self.a[i] * opacity * (0.6 + 0.4 * math.sin(t * 1.3 + self.ph[i]))
            spr = _bokeh_sprite(int(round(float(self.r[i]))), self.color, int(round(float(self.soft[i]))))
            place(canvas, spr, x, y, alpha=clamp(a))
        return canvas


# ---------------------------------------------------------------------------
# 4. Kamera
# ---------------------------------------------------------------------------

def camera(img, out_size, zoom=1.0, center=(0.5, 0.5), rotate=0.0):
    """Görüntüyü sanal kamerayla çerçeveler. zoom>1 yaklaşır; center 0..1 bakış noktası.
    Alt-piksel hassasiyetli olduğu için yavaş hareketlerde titreme yapmaz."""
    W, H = out_size
    iw, ih = img.size
    base = max(W / iw, H / ih)  # görüntüyü kadrajı dolduracak şekilde ölçekle
    vw, vh = W / (base * zoom), H / (base * zoom)
    cx = clamp(center[0] * iw, vw / 2, iw - vw / 2)
    cy = clamp(center[1] * ih, vh / 2, ih - vh / 2)
    src = img
    if rotate:
        src = img.rotate(rotate, resample=Image.BICUBIC, center=(cx, cy))
    return src.resize((W, H), Image.BICUBIC, box=(cx - vw / 2, cy - vh / 2, cx + vw / 2, cy + vh / 2))


def ken_burns(img, out_size, p, zoom=(1.0, 1.12), center_from=(0.5, 0.5), center_to=(0.5, 0.5)):
    """Yavaş yaklaşma + kaydırma. p: 0..1 (genelde prog(t, 0, sure, linear) ya da ease_in_out)."""
    z = lerp(zoom[0], zoom[1], p)
    c = (lerp(center_from[0], center_to[0], p), lerp(center_from[1], center_to[1], p))
    return camera(img, out_size, z, c)


def shake(t, amount=6.0, freq=9.0, seed=0):
    """El kamerası / darbe sarsıntısı için (dx, dy) ofseti."""
    return (amount * math.sin(t * freq * 1.3 + seed) * math.sin(t * freq * 0.7 + 1.7 * seed),
            amount * math.sin(t * freq * 1.1 + 2.1 + seed) * math.cos(t * freq * 0.5 + seed))


# ---------------------------------------------------------------------------
# 5. Film görünümü
# ---------------------------------------------------------------------------

GRADES = {
    # gölge tonu, parlak ton, kontrast, doygunluk
    "teal_orange": ((-0.03, 0.02, 0.06), (0.06, 0.02, -0.04), 1.12, 1.05),
    "warm_gold":   ((0.02, 0.0, -0.03), (0.07, 0.04, -0.03), 1.08, 1.0),
    "cold_blue":   ((-0.03, 0.0, 0.06), (-0.02, 0.02, 0.05), 1.1, 0.9),
    "noir":        ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0), 1.25, 0.0),
    "vintage":     ((0.04, 0.02, 0.0), (0.05, 0.03, -0.05), 0.92, 0.75),
    "neon":        ((0.03, -0.02, 0.08), (0.04, -0.01, 0.06), 1.15, 1.3),
    "none":        ((0, 0, 0), (0, 0, 0), 1.0, 1.0),
}


@lru_cache(maxsize=8)
def _vignette(W, H, strength):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / math.sqrt(2)
    return (1 - strength * np.clip(d, 0, 1) ** 2.2)[..., None]


@lru_cache(maxsize=4)
def _grain_bank(W, H, n=6, seed=7):
    # Yarım çözünürlükte üretilip büyütülür: hem gerçek film tanesine benzer
    # hem de video kodlayıcıyı şişirmez (tam çözünürlüklü gürültü dosyayı 10 kat büyütür).
    rng = np.random.default_rng(seed)
    bank = []
    for _ in range(n):
        g = rng.normal(0, 1, ((H + 1) // 2, (W + 1) // 2)).astype(np.float32)
        g = np.asarray(Image.fromarray(g, "F").resize((W, H), Image.BILINEAR), np.float32)
        bank.append(g[..., None])
    return bank


def finish(img, frame=0, grade="teal_orange", vignette=0.45, grain=0.035, letterbox=None,
           fade=1.0, bloom=0.0):
    """Son katman: renk düzenleme + bloom + vinyet + film grain + letterbox + karartma.
    letterbox: örn. 2.39 (sinemaskop bant). fade: 0 siyah, 1 normal. Dönüş: RGB PIL."""
    rgb = img.convert("RGB")
    if bloom > 0:
        glow = rgb.filter(ImageFilter.GaussianBlur(max(rgb.size) / 60))
        x = np.asarray(rgb, np.float32) / 255
        g = np.asarray(glow, np.float32) / 255
        x = 1 - (1 - x) * (1 - g * bloom)  # screen karışımı
    else:
        x = np.asarray(rgb, np.float32) / 255
    H, W = x.shape[:2]
    sh, hi, con, sat = GRADES.get(grade, GRADES["none"])
    lum = x.mean(axis=2, keepdims=True)
    x = x + np.array(sh, np.float32) * (1 - lum) ** 2 + np.array(hi, np.float32) * lum ** 2
    lum = x.mean(axis=2, keepdims=True)
    x = lum + (x - lum) * sat
    x = 0.5 + (x - 0.5) * con
    if vignette:
        x = x * _vignette(W, H, vignette)
    if grain:
        bank = _grain_bank(W, H)
        g = bank[frame % len(bank)]
        sh_y, sh_x = (frame * 37) % H, (frame * 91) % W
        g = np.roll(g, (sh_y, sh_x), axis=(0, 1))
        x = x + g * grain * (0.6 + 0.4 * (1 - x.mean(axis=2, keepdims=True)))
    x = np.clip(x * fade, 0, 1)
    out = (x * 255).astype(np.uint8)
    if letterbox:
        bar = int(max(0, (H - W / letterbox) / 2))
        if bar > 0:
            out[:bar] = 0
            out[H - bar:] = 0
    return Image.fromarray(out, "RGB")


def blend(a, b, p):
    """İki kareyi karıştırır (sahne içi crossfade için)."""
    return Image.blend(a.convert("RGB"), b.convert("RGB"), clamp(p))


# ---------------------------------------------------------------------------
# 6. Render
# ---------------------------------------------------------------------------

def _ffmpeg():
    exe = shutil.which("ffmpeg")
    if not exe:
        raise RuntimeError("ffmpeg bulunamadı. Kurup PATH'e ekle: https://ffmpeg.org/download.html")
    return exe


def render_scene(path, duration, draw, size, fps=FPS, crf=21, preset="veryfast"):
    """draw(t, i) -> PIL Image (size boyutunda). Sahneyi tek bir mp4 olarak kaydeder.
    Yarım kalan render geçerli dosya gibi görünmesin diye geçici isimle yazılır."""
    W, H = size
    n = int(round(duration * fps))
    tmp = path[:-4] + ".part.mp4"
    cmd = [_ffmpeg(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
           "-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-tune", "film", "-pix_fmt", "yuv420p",
           "-r", str(fps), "-movflags", "+faststart", tmp]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for i in range(n):
            frame = draw(i / fps, i)
            if frame.size != (W, H):
                raise ValueError(f"Kare boyutu {frame.size}, beklenen {(W, H)}")
            proc.stdin.write(frame.convert("RGB").tobytes())
        proc.stdin.close()
        if proc.wait() != 0:
            raise RuntimeError("ffmpeg sahneyi kodlayamadı")
    except BaseException:
        proc.kill()
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
    os.replace(tmp, path)
    return path


def preview_frames(draw, times, size, out_dir, prefix="onizleme"):
    """Tam render öncesi kontrol için belirli anlardan PNG kareler kaydeder."""
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for t in times:
        p = os.path.join(out_dir, f"{prefix}_{t:05.2f}s.png")
        draw(t, int(t * FPS)).convert("RGB").save(p)
        paths.append(p)
    return paths


def concat(scene_paths, out_path, audio_path=None):
    """Sahneleri yeniden kodlamadan birleştirir, varsa sesi ekler."""
    ff = _ffmpeg()
    out_dir = os.path.dirname(os.path.abspath(out_path))
    lst = os.path.join(out_dir, "_sahneler.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for p in scene_paths:
            f.write("file '%s'\n" % os.path.abspath(p).replace("\\", "/").replace("'", r"'\''"))
    silent = out_path[:-4] + ".sessiz.mp4"
    subprocess.run([ff, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c", "copy", silent], check=True)
    os.remove(lst)
    if not audio_path:
        os.replace(silent, out_path)
        return out_path
    tmp = out_path[:-4] + ".part.mp4"
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", silent, "-i", audio_path,
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", tmp], check=True)
    os.remove(silent)
    os.replace(tmp, out_path)
    return out_path


def share_copy(src, dst, crf=26):
    """Sosyal medyaya yüklemek için küçük boyutlu kopya (görüntü farkı neredeyse fark edilmez).
    Kalite ana dosyada kalır; bu kopya genelde 4-5 kat küçüktür."""
    tmp = dst[:-4] + ".part.mp4"
    subprocess.run([_ffmpeg(), "-y", "-loglevel", "error", "-i", src, "-c:v", "libx264",
                    "-preset", "medium", "-crf", str(crf), "-tune", "film", "-pix_fmt", "yuv420p",
                    "-c:a", "copy", "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, dst)
    return dst


# ---------------------------------------------------------------------------
# 7. Ses sentezi (telifsiz, tamamen kodla üretilir)
# ---------------------------------------------------------------------------

SR = 48000


def note(name):
    """'A2', 'C#3', 'Eb4' gibi nota adını frekansa çevirir."""
    names = {"C": -9, "D": -7, "E": -5, "F": -4, "G": -2, "A": 0, "B": 2}
    n = names[name[0].upper()]
    rest = name[1:]
    if rest and rest[0] in "#b":
        n += 1 if rest[0] == "#" else -1
        rest = rest[1:]
    octave = int(rest)
    return 440.0 * 2 ** ((n + (octave - 4) * 12) / 12)


def _smooth(x, k):
    """Basit alçak geçiren filtre (hareketli ortalama)."""
    k = max(1, int(k))
    if k == 1:
        return x
    ker = np.ones(k, np.float32) / k
    return np.convolve(x, ker, mode="same")


class Soundtrack:
    """Fragman tarzı ses tasarımı. Örnek:
        s = Soundtrack(12)
        s.drone(0, 12, 'A1'); s.pad(0, 12, ['A2','C3','E3']); s.riser(7, 9.5); s.impact(9.5)
        s.save('ses.wav')
    """

    def __init__(self, duration):
        self.n = int(duration * SR)
        self.buf = np.zeros((self.n, 2), np.float32)
        self.rng = np.random.default_rng(11)

    def _add(self, start, sig, pan=0.0, vol=1.0):
        i0 = int(start * SR)
        if i0 >= self.n:
            return
        sig = sig[: self.n - i0] * vol
        l, r = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
        if sig.ndim == 1:
            self.buf[i0:i0 + len(sig), 0] += sig * l * 1.414
            self.buf[i0:i0 + len(sig), 1] += sig * r * 1.414
        else:
            self.buf[i0:i0 + len(sig)] += sig

    @staticmethod
    def _env(n, attack, release):
        e = np.ones(n, np.float32)
        a, r = int(attack * SR), int(release * SR)
        if a:
            e[:a] = np.linspace(0, 1, a) ** 2
        if r:
            e[-r:] *= np.linspace(1, 0, r) ** 2
        return e

    def drone(self, start, end, root="A1", vol=0.22, attack=2.0, release=2.0):
        """Derin, karanlık zemin sesi."""
        n = int((end - start) * SR)
        t = np.arange(n) / SR
        f = note(root)
        lfo = 0.75 + 0.25 * np.sin(2 * np.pi * 0.15 * t)
        sig = np.zeros((n, 2), np.float32)
        for mul, a in ((1, 1.0), (2, 0.35), (1.5, 0.2), (3, 0.08)):
            for ch, det in ((0, -0.15), (1, 0.15)):
                sig[:, ch] += a * np.sin(2 * np.pi * (f * mul + det) * t)
        sig *= (lfo * self._env(n, attack, release))[:, None]
        self._add(start, sig / 1.6, vol=vol)

    def pad(self, start, end, notes=("A2", "C3", "E3"), vol=0.12, attack=2.5, release=2.5, bright=0.3):
        """Yumuşak akor dokusu (duygu katmanı)."""
        n = int((end - start) * SR)
        t = np.arange(n) / SR
        sig = np.zeros((n, 2), np.float32)
        for nm in notes:
            f = note(nm)
            for ch, det in ((0, -0.6), (1, 0.6)):
                ph = self.rng.uniform(0, 6.28)
                s = np.sin(2 * np.pi * (f + det) * t + ph)
                s += bright * np.sin(2 * np.pi * 2 * (f + det) * t + ph) * 0.5
                sig[:, ch] += s
        sig *= self._env(n, attack, release)[:, None] / (len(notes) * 1.3)
        self._add(start, self._reverb(sig), vol=vol)

    def riser(self, start, end, vol=0.35, f0=150, f1=1800):
        """Gerilim yükselişi: yükselen ton + gürültü, darbeye doğru tırmanır."""
        n = int((end - start) * SR)
        t = np.arange(n) / SR
        p = t / max(t[-1], 1e-6)
        freq = f0 * (f1 / f0) ** (p ** 1.5)
        phase = 2 * np.pi * np.cumsum(freq) / SR
        tone = np.sin(phase) * 0.5 + np.sin(phase * 1.01) * 0.5
        noise = self.rng.normal(0, 1, n).astype(np.float32)
        noise = noise - _smooth(noise, 30)  # tiz ağırlıklı
        env = p ** 2.2
        sig = (tone * 0.5 + noise * 0.35 * p) * env
        stereo = np.stack([sig, np.roll(sig, 240)], 1)
        self._add(start, stereo, vol=vol)

    def whoosh(self, at, dur=1.2, vol=0.35, pan_from=-0.8, pan_to=0.8):
        """Geçiş sesi. 'at' anında en yüksek noktaya ulaşır."""
        n = int(dur * SR)
        t = np.linspace(0, 1, n)
        noise = self.rng.normal(0, 1, n).astype(np.float32)
        lo = _smooth(noise, 18)
        hi = noise - _smooth(noise, 4)
        env = np.exp(-((t - 0.6) / 0.22) ** 2)
        mix = (lo * (1 - t) + hi * 0.3 * t) * env * 2.5
        pan = np.linspace(pan_from, pan_to, n)
        l = np.cos((pan + 1) * np.pi / 4)
        r = np.sin((pan + 1) * np.pi / 4)
        self._add(at - dur * 0.6, np.stack([mix * l, mix * r], 1).astype(np.float32), vol=vol)

    def impact(self, at, vol=0.8, tail=3.0):
        """Fragman 'BOOM' darbesi: düşen alt bas + gürültü patlaması + yankı."""
        n = int(tail * SR)
        t = np.arange(n) / SR
        f = 30 + 70 * np.exp(-t * 18)
        sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.6)
        noise = self.rng.normal(0, 1, n).astype(np.float32)
        crack = _smooth(noise, 6) * np.exp(-t * 14) * 1.2
        body = _smooth(noise, 60) * np.exp(-t * 3) * 2.0
        sig = np.tanh((sub * 1.4 + crack + body) * 1.3)
        stereo = np.stack([sig, sig], 1).astype(np.float32)
        self._add(at, self._reverb(stereo, wet=0.35), vol=vol)

    def hit(self, at, vol=0.4):
        """Daha küçük vuruş (metin girişleri, kesmeler için)."""
        n = int(0.8 * SR)
        t = np.arange(n) / SR
        f = 45 + 60 * np.exp(-t * 30)
        sig = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6)
        self._add(at, sig.astype(np.float32), vol=vol)

    def pulse(self, start, end, bpm=70, vol=0.35):
        """Kalp atışı benzeri ritmik alt bas (gerilim)."""
        beat = 60 / bpm
        t = start
        while t < end:
            self.hit(t, vol)
            self.hit(t + beat * 0.28, vol * 0.6)
            t += beat

    def shimmer(self, at, dur=2.5, vol=0.12, base="E5"):
        """Parıltı sesi (logo, ürün parlaması)."""
        n = int(dur * SR)
        t = np.arange(n) / SR
        sig = np.zeros(n, np.float32)
        f = note(base)
        for k, m in enumerate((1, 1.5, 2, 3)):
            sig += np.sin(2 * np.pi * f * m * t + k) * np.exp(-t * (1.5 + k))
        stereo = np.stack([sig, np.roll(sig, 600)], 1) / 3
        self._add(at, self._reverb(stereo.astype(np.float32), wet=0.5), vol=vol)

    def add_file(self, path, start=0.0, vol=1.0):
        """Kullanıcının verdiği WAV dosyasını (16-bit) karışıma ekler."""
        with wave.open(path, "rb") as w:
            ch, sr = w.getnchannels(), w.getframerate()
            data = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
        data = data.reshape(-1, ch)
        if ch == 1:
            data = np.repeat(data, 2, 1)
        if sr != SR:
            idx = np.linspace(0, len(data) - 1, int(len(data) * SR / sr))
            data = np.stack([np.interp(idx, np.arange(len(data)), data[:, c]) for c in range(2)], 1)
        self._add(start, data[:, :2].astype(np.float32), vol=vol)

    def _reverb(self, sig, wet=0.3):
        out = sig.copy()
        for d, g in ((0.031, 0.5), (0.047, 0.42), (0.073, 0.35), (0.11, 0.28), (0.17, 0.2), (0.23, 0.14)):
            k = int(d * SR)
            if k < len(sig):
                out[k:, 0] += sig[:-k, 0] * g * wet
                out[k:, 1] += sig[:-k, 1] * g * wet * 0.95
        return out

    def save(self, path, fade_in=0.05, fade_out=1.5, peak=0.89):
        buf = self.buf.copy()
        buf *= self._env(self.n, fade_in, fade_out)[:, None]
        buf = np.tanh(buf * 1.1)  # yumuşak limiter
        m = np.abs(buf).max()
        if m > 0:
            buf *= peak / m
        pcm = (buf * 32767).astype(np.int16)
        with wave.open(path, "wb") as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(pcm.tobytes())
        return path
