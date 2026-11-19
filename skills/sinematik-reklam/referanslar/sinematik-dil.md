# Sinematik Dil Rehberi

Kodla üretilen bir videoyu "sinematik" yapan şeyler: yavaş ve bilinçli hareket, ışık,
derinlik, renk düzenleme, iyi tipografi, ses tasarımı ve tempo.

## Reklam yapısı

| Bölüm | Oran | Amaç |
|-------|------|------|
| Kanca | ilk %10-15 | Durdur: hareket, ışık patlaması, merak uyandıran cümle |
| Gerilim | %30-40 | Atmosfer kur, sorunu ya da arzuyu hissettir |
| Doruk | %25-30 | Ürünün/fikrin ortaya çıkışı, ışık geçişi, darbe sesi |
| Kapanış | son %20 | Logo + slogan + CTA, sessizleşme veya karartma |

Süreye göre sahne sayısı: 6 sn → 2 · 15 sn → 3-4 · 30 sn → 5-7 · 60 sn → 8-12.

## Kamera hareketleri (kodla)

| Hareket | Nasıl | Ne hissettirir |
|---------|-------|----------------|
| Push-in (yaklaşma) | `ken_burns` zoom 1.0 → 1.1, `ease_out` | Önem, yakınlık |
| Pull-out (uzaklaşma) | zoom 1.15 → 1.0 | Açılış, büyüklük |
| Kaydırma (pan) | `center_from` → `center_to` | Keşif |
| Parallax | Katmanları farklı hızda kaydır (ön plan hızlı) | Derinlik |
| Sarsıntı | `shake`, darbe anında, hızla söner | Güç, etki |
| Odak açma | `reveal_text(..., focus=15)` ya da bulanıklıktan netliğe | Gizem, açılış |

Kural: Hareketler **yavaş** olsun. 3 saniyelik bir sahnede %8-12 yakınlaşma yeterli.
Doğrusal hareket mekanik görünür; easing kullan.

## Işık
- **Karanlık zemin + tek güçlü ışık kaynağı** = lüks ve dram (`radial_gradient`).
- **Işık huzmeleri** (`light_rays`): yukarıdan, hafif açılı.
- **Işık geçişi** (`light_sweep`): ürün ya da logo üzerinden kayan parlama; doruk anı için.
- **Bloom** (`finish(..., bloom=0.3)`): parlak alanlara yumuşak ışıma.
- **Parlama geçişi:** `finish(fade=1 + flaş*1.5)` ile beyaza patlama, sonra yeni sahne.

## Renk düzenleme (`GRADES`)

| Ad | Ton | Uygun olduğu işler |
|----|-----|--------------------|
| `warm_gold` | Sıcak altın | Parfüm, kahve, mücevher, lüks |
| `teal_orange` | Turkuaz gölge, turuncu ten | Aksiyon, otomobil, spor, film havası |
| `cold_blue` | Soğuk mavi | Teknoloji, temizlik, kış, gece |
| `noir` | Siyah-beyaz yüksek kontrast | Moda, dram, gizem |
| `vintage` | Soluk, sıcak | Nostalji, el yapımı, yerel marka |
| `neon` | Doygun mor-mavi | Gece hayatı, oyun, müzik |

Palet: 1 baskın renk + 1 vurgu rengi + nötrler. Marka rengi varsa vurgu rengi o olsun.

## Tipografi
- **En fazla iki font ailesi:** biri başlık (serif ya da kalın sans), biri ince yardımcı.
- Lüks hissi: ince font + geniş harf aralığı (`tracking=0.3-0.6`) + büyük harf.
- Duygusal cümleler: serif, büyük boy, kısa satırlar.
- Enerjik: kalın/condensed (`font("black")`), hızlı girişler, `hit` sesiyle eşzamanlı.
- Ekranda aynı anda en fazla 6-7 kelime.
- Türkçe karakterleri (ı, İ, ş, ğ, ü, ö, ç) önizleme karesinde mutlaka kontrol et.

## Film dokusu
- Grain: 0.02-0.04 · Vinyet: 0.3-0.5 · Letterbox `2.39`: yalnızca yatay videolarda.
- Hepsi ince olmalı; fark edilmemeli, hissedilmeli.

## Ses tasarımı (`Soundtrack`)
- **Zemin:** `drone` (bütün video boyunca) + `pad` (duygu).
- **Geçiş:** sahne değişiminde `whoosh`.
- **Gerilim:** `pulse` (kalp atışı) + `riser` (darbeye kadar yükselir).
- **Doruk:** `impact` tam olarak görsel patlamanın/logonun geldiği karede.
- **Parıltı:** `shimmer` ürün parlaması ve logo için.
- Akor önerileri: hüzünlü/lüks `A2 C3 E3 B3` (Am9) · umutlu `C3 E3 G3 D4` (Cadd9) ·
  gizemli `D2 A2 F3 E4` · epik `D2 A2 D3 F3`.
- Ses ve görüntü **aynı zaman çizelgesinden** gelsin: darbe, metin ve kesme saniyeleri aynı sayılar.
