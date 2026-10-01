# Master prompt'lar — kullanım rehberi (TR)

Bu klasördeki prompt'lar İngilizce yazıldı çünkü görsel üretim araçları ve kodlama AI'ları
İngilizce talimatla daha tutarlı çalışıyor. Köşeli parantezli `[ALAN]`ları doldurup kopyalayın.

## Önerilen akış

```
1) Gerçek fotoğraf(lar)ı topla  ──►  2) Cheatsheet üret (görsel AI)  ──►  3) Modelleme başlat (kod AI)
   en az 1 net yan görünüş           01_CHEATSHEET_IMAGE_PROMPT.md         02_MODELING_MASTER_PROMPT.md
   (varsa ön/üst/arka)               fotoğrafı ekleyerek ver               fotoğraf + cheatsheet ekle
                                                                            ──► 4) Düzeltme turları
                                                                                03_PROMPT_PACKS.md (F, G)
```

| Dosya | Ne işe yarar | Nereye verilir |
|-------|--------------|----------------|
| `01_CHEATSHEET_IMAGE_PROMPT.md` | Gerçek görselden modelleme cheatsheet'i üretir (ortografik görünüşler, ölçüler, kesitler, parça ayrımı) | Nano Banana / Gemini, GPT-Image, Midjourney vb. (görseli ekleyerek) |
| `02_MODELING_MASTER_PROMPT.md` | Fotoğraf + cheatsheet ile aşamalı (S1 primitive → S2 lowpoly → S3 detail → S4 game) 3D modellemeyi başlatır | Claude Code (bu klasörde), diğer kodlama agent'ları |
| `03_PROMPT_PACKS.md` | Kategoriye göre kısa hazır prompt'lar (araba, motosiklet, bina, karakter, obje, animasyon/video) + düzeltme/devam prompt'ları | Kodlama agent'ı |

## İpuçları
- **Fotoğraf her zaman kazanır.** Cheatsheet AI üretimi olduğu için detaylarda hata yapar. Agent onu
  parça ayrımı ve isimlendirme için kullanır, fotoğrafla çelişirse fotoğrafa uyar.
- Tek dev cheatsheet yerine **2–3 odaklı sayfa** (ortografik + kesit/genişlik + detay) daha doğru çıkar.
  01 dosyasında A (hepsi bir arada), B (ortografik), C (kesit/genişlik), D (detay) varyantları var.
- En değerli ek girdi: **ikinci bir gerçek fotoğraf** (önden veya üstten). Genişlikleri tahminden kurtarır.
- Bilinen bir gerçek ölçüyü prompt'a yazın (lastik ebadı, kapı yüksekliği, kişinin boyu). Ölçek bundan çıkar.
- Görsel AI'ya bir ölçek çubuğu, ızgara ve tutarlı ölçekli görünüşler istetin. Ölçü yazmayı beceremezse
  agent zaten fotoğraftan ölçüyor. Önemli olan görünüşlerin **hizalı ve aynı ölçekte** olması.
