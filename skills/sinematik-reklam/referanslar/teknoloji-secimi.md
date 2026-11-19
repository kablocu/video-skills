# Teknoloji Seçimi

Kullanıcının isteğine göre en iyi sonucu verecek yolu seç. Şüphedeysen varsayılanı kullan.

| İhtiyaç | En iyi yol | Neden |
|---------|-----------|-------|
| Tipografi, ışık, partikül, soyut/lüks atmosfer | **Python** (`cinematic.py`) | Tam kontrol, her ortamda çalışır |
| Kodla çizilmiş 2D ürün (şişe, kutu, telefon, kart) | **Python** | Pillow şekilleri + degrade + ışık geçişi |
| Kullanıcının fotoğraflarını canlandırma | **Python** (`ken_burns`, `finish`) | Alt-piksel kamera, renk düzenleme |
| Gerçek 3D: dönen ürün, 3D logo, kamera uçuşu | **Three.js + tarayıcı yakalama** | Gerçek ışıklandırma ve perspektif |
| Binlerce partikül, akışkan efektler, shader | **WebGL / Canvas** | GPU hızı |
| Arayüz/uygulama tanıtımı (ekran animasyonu) | **HTML/CSS + tarayıcı yakalama** | Arayüzü HTML ile kurmak en kolayı |
| Veri/grafik animasyonu | **Python** (Pillow çizim) | Basit ve kontrollü |

## Python yolu (varsayılan)
Gerekenler: Python 3.9+, `pip install pillow numpy`, ffmpeg.
Hız: 1080×1920 karede efektlere bağlı olarak 0,2-0,5 sn/kare; 15 saniyelik reklam ≈ 2-4 dk.
Hızlandırma: Ağır katmanları önceden hazırla. Önizlemede `preview_frames` kullan, tam render'ı en sona bırak.

## Tarayıcı yolu (3D / WebGL)
1. Sahneyi tek bir HTML dosyası olarak yaz. Zamanı `window.renderAt(t)` gibi bir fonksiyonla
   dışarıdan kontrol et; `requestAnimationFrame`'e güvenme, her kare belirli bir t için çizilmeli.
2. Playwright ile sayfayı hedef boyutta aç, her kare için `renderAt(i/30)` çağır ve ekran görüntüsü
   al (JPEG kalite 92). Görüntüleri ffmpeg'e boru ile ver ya da sahne sahne mp4 yap.
3. Renk düzenleme, grain ve ses için yine `cinematic.py` kullanılabilir: her kareyi `finish`
   ile işle, sesi `Soundtrack` ile üret, `concat` ile birleştir.
4. Three.js gibi kütüphaneler internet gerektirir. Ortamda ağ yoksa yerel kopya gerekir; yoksa
   Python yoluna dön ve kullanıcıya söyle.

## Ses
- Varsayılan: `Soundtrack` ile kodla sentez (telifsiz).
- Kullanıcı müzik verirse: WAV'a çevir (`ffmpeg -i muzik.mp3 muzik.wav`), `add_file` ile ekle,
  efektleri üstüne koy. Müziğin vuruşlarına göre kesme zamanlarını ayarla.
