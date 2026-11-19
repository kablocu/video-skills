"""
Örnek: Kurgusal parfüm markası "VELORA" için 12 saniyelik dikey (9:16) sinematik reklam.

Çalıştırma (repo kök klasöründen):
    python skills/sinematik-reklam/ornekler/ornek_parfum_reklami.py             # tam render
    python skills/sinematik-reklam/ornekler/ornek_parfum_reklami.py --onizleme  # sadece kontrol kareleri

Çıktı: cikti/velora/velora_reklam.mp4

Sahne planı:
  1  0.0-3.0  Karanlıkta ışık huzmeleri, toz zerreleri, "Bazı anlar"
  2  3.0-6.5  Şişe karanlıktan doğar, yavaş yaklaşma, üzerinden ışık geçer
  3  6.5-9.5  "ışıkla başlar." odak açılarak gelir, gerilim yükselir
  4  9.5-12   Darbe + parlama, VELORA logosu, karartma
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

import cinematic as c  # noqa: E402

SIZE = c.FORMATS["9:16"]
W, H = SIZE
OUT = os.path.join("cikti", "velora")
GOLD = (226, 186, 120)
WARM = (255, 214, 160)

# --- Bir kez hazırlanan katmanlar -------------------------------------------

BG = c.radial_gradient(SIZE, inner=(46, 30, 18), outer=(3, 2, 2), center=(0.5, 0.42), radius=0.7)
RAYS = c.light_rays(SIZE, origin=(0.5, -0.08), n=9, spread=40, color=WARM, strength=70)
DUST = c.Particles(SIZE, n=70, seed=4, color=WARM, r=(1.5, 5), speed=(6, 20), alpha=(0.15, 0.6))
BOKEH = c.Particles(SIZE, n=14, seed=9, color=GOLD, r=(14, 34), speed=(4, 10),
                    alpha=(0.05, 0.18), softness=(6, 14))


def make_bottle():
    """Kodla çizilmiş parfüm şişesi (RGBA) ve ışık maskesi."""
    bw, bh = 560, 900
    lay = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    # gövde (cam)
    body = (60, 330, bw - 60, bh - 40)
    d.rounded_rectangle(body, radius=60, fill=(40, 26, 14, 235))
    # sıvı: dikey degrade
    liquid = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    ld = ImageDraw.Draw(liquid)
    for y in range(400, bh - 70):
        p = (y - 400) / (bh - 470)
        col = (int(c.lerp(214, 120, p)), int(c.lerp(142, 62, p)), int(c.lerp(60, 18, p)), 240)
        ld.line([(84, y), (bw - 84, y)], fill=col)
    mask = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(mask).rounded_rectangle((84, 400, bw - 84, bh - 66), radius=44, fill=255)
    lay.paste(liquid, (0, 0), mask)
    # cam kenar parlamaları
    hl = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hl)
    hd.rounded_rectangle(body, radius=60, outline=(255, 235, 200, 150), width=4)
    hd.line([(100, 380), (100, bh - 100)], fill=(255, 245, 225, 200), width=10)
    hd.line([(bw - 112, 420), (bw - 112, bh - 140)], fill=(255, 230, 190, 90), width=5)
    hl = hl.filter(ImageFilter.GaussianBlur(3))
    lay = Image.alpha_composite(lay, hl)
    d = ImageDraw.Draw(lay)
    # boyun ve kapak
    d.rectangle((bw / 2 - 70, 290, bw / 2 + 70, 335), fill=(180, 140, 80, 255))
    for i in range(0, 260):
        p = i / 260
        g = int(c.lerp(40, 12, abs(p - 0.35) * 1.5))
        d.line([(bw / 2 - 95, 30 + i), (bw / 2 + 95, 30 + i)], fill=(g, g - 2, g - 4, 255))
    d.rectangle((bw / 2 - 95, 30, bw / 2 + 95, 290), outline=(200, 160, 95, 255), width=3)
    d.line([(bw / 2 - 70, 50), (bw / 2 - 70, 270)], fill=(120, 110, 100, 255), width=4)
    # etiket
    label = c.text_layer("VELORA", c.font("light", 46), fill=(250, 235, 210), tracking=0.5)
    c.place(lay, label, bw / 2, 640, alpha=0.95)
    line = Image.new("RGBA", (180, 2), GOLD + (220,))
    c.place(lay, line, bw / 2, 690)
    # ışık maskesi = şişenin görünür alanı
    m = lay.getchannel("A")
    return lay, m


BOTTLE, BOTTLE_MASK = make_bottle()
BOTTLE_GLOW = BOTTLE.filter(ImageFilter.GaussianBlur(40))
BOTTLE_SOFT = BOTTLE.filter(ImageFilter.GaussianBlur(14))

# yansıma
REFL = BOTTLE.transpose(Image.FLIP_TOP_BOTTOM)
_a = np.asarray(REFL.getchannel("A"), np.float32)
_a *= 0.2 * np.clip(1 - np.linspace(0, 1, REFL.height) * 2.2, 0, 1)[:, None] ** 2  # aşağı doğru söner
REFL.putalpha(Image.fromarray(_a.astype(np.uint8), "L"))

F_LINE = c.font("light", 84)
F_BIG = c.font("serif", 150)
F_LOGO = c.font("light", 120)
F_SUB = c.font("regular", 34)


def bottle_frame(canvas, cx, cy, scale, alpha, sweep=None):
    b = BOTTLE
    if sweep is not None:
        b = c.light_sweep(BOTTLE, sweep, angle=20, width=0.24, strength=0.85, color=(255, 245, 225),
                          mask=BOTTLE_MASK)
    c.place(canvas, BOTTLE_GLOW, cx, cy, alpha=alpha * 0.55, scale=scale)
    c.place(canvas, REFL, cx, cy + BOTTLE.height * scale * 0.98, alpha=alpha, scale=scale)
    c.place(canvas, b, cx, cy, alpha=alpha, scale=scale)


# --- Sahneler (her biri kendi zaman çizelgesinde, t=0 sahne başı) -----------

def scene1(t, i):  # 3.0 sn
    cv = BG.copy()
    c.place(cv, RAYS, W / 2, H / 2, alpha=c.prog(t, 0, 2.2) * 0.9, scale=1.0 + 0.04 * t)
    BOKEH.draw(cv, t)
    DUST.draw(cv, t, opacity=c.prog(t, 0, 1.5))
    c.reveal_text(cv, "Bazı anlar", F_LINE, W / 2, H * 0.5, t, start=0.6, dur=1.4, end=2.85,
                  out=0.6, tracking=0.12, track_to=0.2, fill=(245, 230, 210))
    return c.finish(cv, i, grade="warm_gold", fade=c.prog(t, 0, 0.8), bloom=0.25)


def scene2(t, i):  # 3.5 sn
    T = 3 + t
    cv = BG.copy()
    c.place(cv, RAYS, W / 2, H / 2, alpha=0.9, scale=1.12 + 0.02 * t)
    BOKEH.draw(cv, T)
    scale = c.lerp(1.08, 1.2, c.prog(t, 0, 3.5, c.ease_out))
    sweep = c.prog(t, 1.0, 2.8, c.ease_in_out) if 1.0 <= t <= 2.8 else None
    bottle_frame(cv, W / 2, H * 0.47, scale, c.prog(t, 0, 1.4, c.ease_out), sweep)
    DUST.draw(cv, T)
    return c.finish(cv, i, grade="warm_gold", bloom=0.3)


def scene3(t, i):  # 3.0 sn
    T = 6.5 + t
    cv = BG.copy()
    c.place(cv, RAYS, W / 2, H / 2, alpha=0.9, scale=1.19 + 0.02 * t)
    BOKEH.draw(cv, T)
    # şişe arka plana çekilir, odak dışı
    c.place(cv, BOTTLE_SOFT, W / 2, H * 0.47, alpha=c.lerp(1, 0.3, c.prog(t, 0, 0.8)),
            scale=1.2 + 0.03 * t)
    DUST.draw(cv, T)
    c.reveal_text(cv, "ışıkla\nbaşlar.", F_BIG, W / 2, H * 0.5, t, start=0.3, dur=1.6,
                  end=3.1, out=0.25, tracking=0.02, fill=(255, 244, 228), focus=22, rise=60, glow=18)
    flash = c.prog(t, 2.85, 3.0, c.ease_in)
    return c.finish(cv, i, grade="warm_gold", bloom=0.3 + flash * 0.9, fade=1 + flash * 1.5)


def scene4(t, i):  # 2.5 sn
    T = 9.5 + t
    cv = BG.copy()
    c.place(cv, RAYS, W / 2, H / 2, alpha=1.0, scale=1.25 + 0.02 * t)
    BOKEH.draw(cv, T, opacity=1.2)
    DUST.draw(cv, T)
    dx, dy = c.shake(t, amount=10 * (1 - c.prog(t, 0, 0.5, c.ease_out)))
    c.reveal_text(cv, "VELORA", F_LOGO, W / 2 + dx, H * 0.47 + dy, t, start=0.0, dur=0.9,
                  tracking=0.35, track_to=0.55, fill=(252, 240, 220), focus=10, rise=0, glow=24)
    lw = int(420 * c.prog(t, 0.4, 1.3, c.ease_out))
    if lw > 2:
        c.place(cv, Image.new("RGBA", (lw, 2), GOLD + (230,)), W / 2, H * 0.47 + 110)
    c.reveal_text(cv, "EAU DE PARFUM", F_SUB, W / 2, H * 0.47 + 170, t, start=0.7, dur=0.9,
                  tracking=0.5, fill=GOLD, rise=10, focus=6)
    flash = 1 - c.prog(t, 0, 0.35, c.ease_out)
    fade = (1 + flash * 1.5) * (1 - c.prog(t, 1.8, 2.5, c.ease_in))
    return c.finish(cv, i, grade="warm_gold", bloom=0.35 + flash, fade=fade)


SCENES = [("s1", 3.0, scene1), ("s2", 3.5, scene2), ("s3", 3.0, scene3), ("s4", 2.5, scene4)]


def soundtrack(path):
    s = c.Soundtrack(12.0)
    s.drone(0, 12, "A1", vol=0.25, attack=1.5, release=1.5)
    s.pad(0.5, 9.5, ["A2", "C3", "E3", "B3"], vol=0.14, attack=2.5, release=0.8)
    s.whoosh(3.0, dur=1.4, vol=0.3)
    s.shimmer(4.0, vol=0.10)
    s.pulse(6.5, 9.3, bpm=84, vol=0.25)
    s.riser(7.2, 9.5, vol=0.3)
    s.impact(9.5, vol=0.9)
    s.pad(9.5, 12, ["A2", "E3", "A3", "C#4"], vol=0.16, attack=0.05, release=1.8)
    s.shimmer(9.6, vol=0.14, base="A5")
    return s.save(path)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if "--onizleme" in sys.argv:
        for name, dur, fn in SCENES:
            c.preview_frames(fn, [dur * 0.25, dur * 0.6, dur * 0.95], SIZE, OUT, prefix=name)
        print("Önizleme kareleri:", OUT)
        sys.exit(0)
    parts = []
    for name, dur, fn in SCENES:
        print("Render:", name)
        parts.append(c.render_scene(os.path.join(OUT, f"{name}.mp4"), dur, fn, SIZE))
    audio = soundtrack(os.path.join(OUT, "ses.wav"))
    final = c.concat(parts, os.path.join(OUT, "velora_reklam.mp4"), audio)
    small = c.share_copy(final, os.path.join(OUT, "velora_reklam_paylasim.mp4"))
    print("Hazır:", final, "| Paylaşım kopyası:", small)
