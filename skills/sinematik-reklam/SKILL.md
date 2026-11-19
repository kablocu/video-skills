---
name: sinematik-reklam
description: Kullanıcıya adım adım sorular sorarak sinematik kısa reklam videosunu (ürün, marka, hizmet, etkinlik tanıtımı) planlar ve görüntü, tipografi, ışık, film efektleri, müzik ve ses efektleri dahil tamamen kod yazarak MP4 olarak üretir. "Reklam videosu yap", "ürün tanıtım videosu", "sinematik reklam", "teaser", "fragman tarzı tanıtım", "cinematic ad" isteklerinde kullan.
---

# Sinematik Reklam

Bu skill, kullanıcının tarif ettiği reklamı **sorularla netleştirir**, **sahne sahne planlar**
ve **kodla üretir**. Hazır video ya da görsel üretim servisi kullanılmaz: her kare, her ışık,
her nota kodla oluşturulur. Bu yüzden çıktı telifsizdir ve her ayrıntı değiştirilebilir.

Akış beş aşamadır. Bir aşama bitmeden sonrakine geçme.

```
1. Sorular  →  2. Yaratıcı plan (onay)  →  3. Teknoloji seçimi  →  4. Üretim  →  5. Teslim
```

---

## 1. Sorular: isteği netleştir

Kullanıcı her şeyi baştan söylediyse ilgili soruları atla. Eksik olanları **en fazla 4
soruluk turlar** halinde sor. Seçmeli soru aracı varsa (AskUserQuestion gibi) onu kullan ve
her soruya hazır seçenekler koy; kullanıcı her zaman kendi cevabını da yazabilir.

**1. tur: Temel**
- **Ne tanıtılıyor?** Ürün, marka, hizmet, etkinlik, uygulama... Adı tam yazımıyla
  (büyük/küçük harf, Türkçe karakterler).
- **Hedef kitle ve platform:** Kimler izleyecek, nerede yayınlanacak?
- **Süre ve format:** Her seferinde sor. Seçenekler: 6 sn (bumper), 15 sn, 30 sn, 60 sn;
  9:16 dikey (Reels/Shorts/TikTok), 16:9 yatay (YouTube/web), 1:1 kare, 4:5 akış.
- **Tek cümlelik ana mesaj:** İzleyici videodan sonra neyi hatırlamalı?

**2. tur: Stil**
- **Duygu / ton:** Lüks ve gizemli · Epik ve güçlü · Sıcak ve duygusal · Enerjik ve modern ·
  Minimal ve temiz · Nostaljik.
- **Renkler:** Marka renkleri var mı? (HEX kodu varsa iste.) Yoksa tona göre öner.
- **Metinler:** Slogan, ekranda geçecek cümleler, kapanış yazısı/CTA (ör. "Şimdi keşfet",
  web adresi). Metinleri birebir kullanıcıdan al, kendin uydurma; öneri yapacaksan onaya sun.
- **Ses:** Kodla üretilmiş müzik + ses efekti (varsayılan) · Kullanıcının kendi müziği
  (WAV dosyası) · Sessiz.

**3. tur: Varlıklar (gerekirse)**
- Logo, ürün fotoğrafı, video ya da font dosyası var mı? Varsa iste ve kullan.
  Ürün fotoğrafları kodla canlandırılabilir (yavaş yaklaşma, ışık geçişi, renk düzenleme).

> **Dürüst ol:** Kodla üretim; motion design, tipografi, ışık, partikül, soyut ve stilize
> ürün çizimi gibi işlerde çok güçlüdür. **Fotogerçekçi insan, yüz, gerçek mekân çekimi ya da
> birebir gerçek ürün görüntüsü kodla üretilemez.** Kullanıcı bunu istiyorsa açıkça söyle ve
> iki yol öner: (a) kendi fotoğraf/videosunu versin, kod onları sinematik hale getirsin,
> (b) stilize/soyut bir anlatımla devam edilsin.
>
> Gerçek markaların logolarını, karakterlerini ya da tasarımlarını kullanıcı kendi dosyası
> olarak vermedikçe çizme; ona ait olduğunu belirttiği markalar için de logoyu dosyadan al.

---

## 2. Yaratıcı plan: storyboard ve onay

Cevaplardan sonra kısa bir plan sun ve **onay almadan üretime geçme**:

1. **Konsept:** Tek paragraf. Fikir ne, izleyici ne hissedecek?
2. **Sahne tablosu:**

| # | Süre | Görüntü | Kamera / hareket | Ekrandaki metin | Ses |
|---|------|---------|------------------|-----------------|-----|
| 1 | 0-3 sn | Karanlık, ışık huzmeleri, toz | Yavaş yaklaşma | "Bazı anlar" | Derin zemin sesi |
| ... | | | | | |

3. **Görsel dil:** Renk düzenleme (ör. sıcak altın), fontlar, efektler (grain, vinyet, bloom).

Sahne kurgusunda klasik reklam yapısını temel al (ayrıntı: `referanslar/sinematik-dil.md`):
**Kanca (ilk 1-2 sn) → Gerilim/merak → Doruk/ürünün ortaya çıkışı → Logo + mesaj + CTA.**
Dikey sosyal medya videolarında ilk 1 saniyede hareket ya da güçlü bir görüntü olmalı.

Kullanıcı değişiklik isterse planı güncelle ve tekrar onay al.

---

## 3. Teknoloji seçimi

Kararı sen ver; kullanıcıya bir cümleyle hangisini neden seçtiğini söyle.
Ayrıntılı karşılaştırma: `referanslar/teknoloji-secimi.md`.

- **Varsayılan: Python + Pillow + NumPy + ffmpeg** (`scripts/cinematic.py`). 2D motion design,
  tipografi, ışık, partikül, ürün çizimi, fotoğraf canlandırma ve ses sentezi için en
  taşınabilir ve en güvenilir yol. Reklamların büyük çoğunluğu buna uygundur.
- **HTML/Canvas/WebGL (Three.js) + tarayıcıdan kare yakalama:** Gerçek 3D sahne, dönen 3D
  ürün, yoğun partikül sistemleri ya da CSS ile çok kolay olan arayüz animasyonları
  gerektiğinde. Ortamda başsız tarayıcı (Playwright/Chromium) varsa kullan.
- Önce ortamı kontrol et: `python -c "import PIL, numpy"`, `ffmpeg -version`,
  gerekirse `python -c "import playwright"`. Eksik varsa kullanıcıya ne gerektiğini söyle.

---

## 4. Üretim

### Dosya düzeni
Her proje için repo kökünde `cikti/<proje-adi>/` klasörü aç (bu klasör `.gitignore`'da,
GitHub'a gitmez). Kod dosyasını `cikti/<proje-adi>/reklam.py` olarak yaz.

### Kütüphane
`scripts/cinematic.py` dosyasını import et; tekerleği yeniden icat etme. Başlıca araçlar:

| Araç | Ne işe yarar |
|------|--------------|
| `FORMATS["9:16"]` | Format → piksel boyutu |
| `prog`, `ease_in_out`, `ease_out`, `fade_window` | Zamanlama ve yumuşak hareket |
| `font("display"/"light"/"serif"/"black", boyut)` | Türkçe destekli font bulur |
| `text_layer`, `reveal_text`, `place` | Tipografi, odak açılarak giriş, ışıma |
| `radial_gradient`, `linear_gradient`, `light_rays`, `light_sweep` | Zemin ve ışık |
| `Particles` | Toz, bokeh, kıvılcım |
| `camera`, `ken_burns`, `shake` | Sanal kamera, yaklaşma, sarsıntı |
| `finish` | Renk düzenleme (`GRADES`), bloom, vinyet, grain, letterbox, karartma |
| `render_scene`, `preview_frames`, `concat`, `share_copy` | Render ve teslim |
| `Soundtrack` | `drone`, `pad`, `riser`, `whoosh`, `impact`, `hit`, `pulse`, `shimmer`, `add_file` |

Tam çalışan örnek: `ornekler/ornek_parfum_reklami.py`. Yeni reklama başlarken bu dosyanın
yapısını kopyala, içeriği plana göre yeniden yaz.

### Kurallar
- **Her sahne ayrı bir fonksiyon** (`sahne(t, i) -> PIL Image`), her sahne ayrı bir mp4.
  Sahneler `concat` ile yeniden kodlanmadan birleştirilir, ses en sonda eklenir.
- **Geçişleri sahnenin içinde yap** (karartma, parlama, `blend` ile karışım). Bitmiş
  dosyalar arasında geçiş yapmak her şeyi iki kez kodlar.
- Ağır şeyleri (zemin, ışık huzmeleri, çizilmiş ürün, bulanık kopyalar) **bir kez** üret,
  her karede yeniden hesaplama.
- **30 fps** ve hedef çözünürlükte çiz. Metinleri ekran kenarından en az %8 içeride tut
  (dikey videoda alt %20'yi platform arayüzü kapatır).
- Ekrandaki her metin ekranda **okunabilecek kadar** kalmalı: kabaca kelime başına 0,3 sn,
  en az 1,2 sn.

### Kontrol: tam render'dan önce
1. `preview_frames` ile her sahnenin en kalabalık anlarından 2-3 kare çıkar.
2. **Karelere bak** (görüntüyü oku). Metin taşıyor mu, Türkçe karakterler doğru mu, kontrast
   yeterli mi, ürün kadrajda mı, renkler tona uyuyor mu?
3. Sorunları düzelt, sonra tam render al. Hedef: istek başına **tek** tam render.

### Render sonrası
- `ffprobe` ile süre, çözünürlük ve ses akışını doğrula.
- Bitmiş videodan 3-4 kare çıkarıp tekrar bak.
- `share_copy` ile paylaşım kopyası üret (ana dosyanın genelde 1/3'ü ile 1/4'ü boyutunda).

---

## 5. Teslim

- Paylaşım kopyasını kullanıcıya gönder; ana dosyanın yerini söyle.
- Bir cümleyle neyin üretildiğini anlat (süre, format, sahne sayısı).
- Değişiklik isterse **sadece etkilenen sahneyi** yeniden render et, sonra `concat` ile
  birleştir. Sadece ses değişecekse görüntüyü yeniden üretme.
- Projeyi saklamak isterse `cikti/` yerine `projeler/<ad>/reklam.py` olarak kaydetmeyi öner;
  mp4 dosyaları GitHub'a gönderilmez, kod gönderilir (video her zaman koddan yeniden üretilebilir).
