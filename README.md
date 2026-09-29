# Blender Workbench

Blender'ı arka planda (headless) çalıştırıp **kodla** 3D model, animasyon ve video üreten çalışma
tezgahı. Motor, araba, bina, karakter, obje... Her model tekrar üretilebilir Python kaynak kodudur.
`.blend`, `.glb`, render ve videolar bu koddan çıkan çıktılardır.

Asıl fark: modeller **gerçek fotoğrafa göre ölçülerek** yapılır. Fotoğraftaki pikseller metreye
çevrilir, model referans kamerasından render alınıp fotoğrafın üstüne bindirilir ve sayılarla
doğrulanır.

## Hızlı başlangıç

```bash
python wb.py doctor                                  # Blender + Pillow kontrolü
python wb.py test                                    # kütüphane testi (render + video + glb)
python wb.py build VEH_Gemini_Motorcycle             # örnek projeyi baştan üret
python wb.py new VEH_Benim_Arabam --category vehicle # yeni proje iskeleti
```

Yeni bir model için:
1. Fotoğrafı `projects/<ASSET>/ref/REAL_REFERENCE.png` olarak koy.
2. İstersen `docs/prompts/01_CHEATSHEET_IMAGE_PROMPT.md` ile görsel AI'dan bir cheatsheet üret ve
   `ref/MODELING_CHEATSHEET.png` olarak kaydet.
3. Claude Code'a (veya başka bir agent'a) `docs/prompts/02_MODELING_MASTER_PROMPT.md`'yi ver.

## Klasörler

| Klasör | İçerik |
|--------|--------|
| `workbench/` | Ortak kütüphane: foto→metre dönüşümü, mesh üreticileri, kamera, render, animasyon, rig, doğrulama, export |
| `projects/<ASSET>/` | Her modelin kaynak kodu, ölçüleri (`landmarks.py`), referansları ve raporu |
| `output/<ASSET>/` | Üretilen `.blend` kilometre taşları, `.glb`, render'lar, videolar |
| `templates/` | Yeni proje şablonu + smoke test |
| `docs/` | Süreç, standartlar, teknikler, çıkarılan dersler, örnek vaka |
| `docs/prompts/` | Kullanıcı için master prompt'lar (cheatsheet üretimi, modelleme başlatma, kategori paketleri) |
| `AGENTS.md` / `CLAUDE.md` | AI agent'lar için kurallar. `.claude/skills/blender-workbench` = Claude skill'i |

## Örnek: VEH_Gemini_Motorcycle
Tek bir yan fotoğraftan yeniden kurulan özel Honda motosiklet. Stage 1: 9.8k üçgen, Stage 2: 65k
üçgen, 8 materyal, 0 çakışma, referans kamera hatası 0 px. Anlatımı:
`docs/case_studies/VEH_Gemini_Motorcycle.md`.

## Gereksinimler
Blender 5.2 LTS (başka yerdeyse `BLENDER_EXECUTABLE` ortam değişkeni), Python 3 + `pip install pillow numpy`.
