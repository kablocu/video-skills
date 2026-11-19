# 🎬 Video Skills

Sinematik kısa reklamlar, sosyal medya videoları ve hikaye/belgesel videoları
planlayıp üretmek için modüler "skill"lerden oluşan açık kaynaklı bir proje.

Videolar hazır bir video servisiyle değil, **tamamen kodla** üretilir: görüntü, tipografi,
ışık, film efektleri, müzik ve ses efektleri. Bu yüzden çıktılar telifsizdir ve her ayrıntı
değiştirilebilir.

## Nasıl çalışır?
1. Nasıl bir video istediğini anlatırsın.
2. Yapay zekâ sana adım adım sorular sorarak isteğini netleştirir.
3. Sahne sahne bir plan sunar, onaylarsın.
4. Kod yazılır, video render edilir ve sana MP4 olarak teslim edilir.

## Skill'ler

| Skill | Durum | Ne yapar |
|-------|-------|----------|
| [sinematik-reklam](skills/sinematik-reklam/) | ✅ Hazır | Ürün/marka için fragman tarzı kısa reklam |
| sosyal-medya | 🔜 Planlandı | Reels / Shorts / TikTok içerikleri |
| belgesel-hikaye | 🔜 Planlandı | Anlatıcılı hikaye ve belgesel videoları |

## Kurulum

```
pip install -r requirements.txt
```

Ayrıca [ffmpeg](https://ffmpeg.org/download.html) kurulu olmalı.

Örnek reklamı üretmek için (repo klasöründe):

```
python skills/sinematik-reklam/ornekler/ornek_parfum_reklami.py
```

Video `cikti/velora/` klasörüne kaydedilir.

## Klasörler
- `skills/` → Her video türü için ayrı skill'ler
- `cikti/` → Üretilen videolar (GitHub'a gönderilmez)

## Lisans
MIT
