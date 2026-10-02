# VEH_TT92_Racing_Car — Profesyonel Boyama: Materyal Listesi ve AI Prompt Paketi

> **Durum (2026-10-01):** albedolar üretildi ve uygulandı. Setler `material/TT92_<Ad>_1K-PNG/` altında
> (bkz. `material/README.md`), materyaller `paint.py` içinde (master + 14 instance), build aşaması `stage5_paint.py`.
> Aşağıdaki plan ve prompt'lar referans olarak duruyor; M09 deri için albedo henüz yok (kütüphane seti kullanılıyor).

Hedef: aracın her parçasına gerçekçi bir PBR materyal (albedo + roughness + metallic + normal)
atamak. UV çalışması yok: build'deki `mesh.box_uv` zaten her parçaya **metre bazlı kutu projeksiyon UV**
veriyor, dokular tile (tekrar) ederek kaplanır. Bu yüzden **tüm dokular seamless (dikişsiz) ve
gerçek dünya ölçeğinde** olmalı. Her materyalin yanındaki `tile_m` = dokunun bir tekrarının gerçek
boyutu (metre).

---

## 1. Materyal özeti (14 materyal)

| # | Materyal adı | Nerede kullanılıyor | Kaynak | tile_m |
|---|--------------|---------------------|--------|--------|
| M01 | `MAT_PAINT_RED` | gövde kabuğu, kaput panjurları, ayna kafaları, arka yaylar, hava filtresi, motor yuvası ve kokpit kenar lipleri | **AI** (özgün) | 0.50 |
| M02 | `MAT_PAINT_CREAM` | burundan motor yuvasına iki krem şerit | **AI** | 0.25 |
| M03 | `MAT_CHROME` | ızgara çıtaları ve halkası, far gövdeleri, ayna sapı/camı, blower, hız boruları, kam kapakları, jant göbeği ve spinner, afterburner kovanı, süspansiyon boruları, doldurma kapakları | **Web** + AI roughness | 0.20 |
| M04 | `MAT_ALUMINIUM_CAST` | motor bloğu, karter, yağ teknesi, zamanlama kapağı, volan kovanı, emme manifoldu | **Hibrit** | 0.25 |
| M05 | `MAT_BLACK_COATED` | jant ve teller, fren kampanaları, aks taşıyıcılar, damperlar, kasnaklar, burun ağzı içi, kokpit tüpü, gösterge paneli, direksiyon mili, afterburner bantları ve dişleri, panel çizgileri | **Hibrit** | 0.25 |
| M06 | `MAT_STAINLESS_HEAT` | header'lar, egzoz boruları, motor port stub'ları, afterburner iç petalleri | **AI** (ısı rengi özgün) | 0.30 |
| M07 | `MAT_EXHAUST_WRAP` | egzozdaki ısı sargısı | **Web** + AI | 0.10 |
| M08 | `MAT_TYRE_RUBBER` | 4 lastik, motor kayışı | **Web** (+ AI yan duvar) | 0.30 |
| M09 | `MAT_LEATHER_SEAT` | koltuk minderi ve sırtlığı, kokpit ön yastık (cowl pad) | **Web** + AI | 0.35 |
| M10 | `MAT_WOOD_WHEEL` | direksiyon simidi (ahşap kenar; şu an deri, değişecek) | **Web** | 0.30 |
| M11 | `MAT_SMOKED_LENS` | far "gözleri" (füme plaka) ve lamba camları | **AI** (çizik/roughness) | 0.20 |
| M12 | `MAT_CARBON` | alt spoiler, afterburner dış petalleri | **Web** | 0.12 |
| M13 | `MAT_AB_GLOW` | afterburner iç astarı (emissive) | **AI** | 0.30 |
| M14 | `MAT_STEEL_BRUSHED` | perçinler, cıvatalar | **Web** | 0.10 |

**Parça bazlı detay haritası** (object adı → materyal):

| Parça grubu (object adı) | Materyal |
|--------------------------|----------|
| `BODY_Shell` dış yüz | M01 |
| `BODY_Shell` kesik iç yüzler (kokpit, motor yuvası, burun ağzı içi) | M05 |
| `BODY_Louvres`, `BODY_MirrorHead_*`, `ENGINE_AirFilter_L`, `SUSP_Rear_Spring_*`, `BODY_BayLip`, `COCKPIT_RimLip` | M01 |
| `BODY_Stripes` | M02 |
| `NOSE_Ring`, `NOSE_Grille`, `NOSE_Emblem`, `NOSE_TowRing` | M03 |
| `BODY_Eye_*` | M11 (plaka) |
| `BODY_EyeTrim_*`, `BODY_EyeLamp_*`, `BODY_MirrorStalk_*`, `BODY_MirrorGlass_*`, `BODY_FillerCap_*` | M03 |
| `AERO_ChinSpoiler` | M12 |
| `BODY_PanelLines` | M05 |
| `WHEEL_*_Tire_*` | M08 |
| `WHEEL_*_Rim_*`, `WHEEL_*_Spokes_*`, `BRAKE_Drum_*` | M05 |
| `WHEEL_*_Hub_*`, `WHEEL_*_Spinner_*` | M03 |
| `SUSP_Front_*` boruları, `SUSP_Rear_Link/Axle/Rod/DamperBody` | M03 |
| `SUSP_*_Damper`, `SUSP_Rear_HubCarrier_*` | M05 |
| `ENG_OilPan`, `ENG_Crankcase`, `ENG_TimingCover`, `ENG_Bellhousing`, `ENG_Bank_*`, `ENG_Intake` | M04 |
| `ENG_CamCover_*`, `ENG_Blower`, `ENG_BlowerRib_*`, `ENG_Stack_*`, `ENG_OilCap_*`, `ENG_CrankSnout`, `ENG_BlowerDriveShaft` | M03 |
| `ENG_CrankPulley`, `ENG_BlowerPulley` | M05 |
| `ENG_Belt` | M08 |
| `ENG_Port_*`, `EXHAUST_Header_*`, `EXHAUST_Pipe_*` | M06 |
| `EXHAUST_Wrap_*`, `EXHAUST_WrapCore_*` | M07 |
| `EXHAUST_AB_Can` | M03 |
| `EXHAUST_AB_Band_*`, `EXHAUST_AB_Teeth`, `EXHAUST_AB_Slots`, `EXHAUST_AB_FlameHolder`, `EXHAUST_AB_Inlet_*`, `EXHAUST_AB_PetalsOuter` | M05 (PetalsOuter: M12) |
| `EXHAUST_AB_PetalsInner` | M06 |
| `EXHAUST_AB_Glow` | M13 |
| `COCKPIT_Seat_*`, `COCKPIT_CowlPad` | M09 |
| `COCKPIT_SteeringWheel` | M10 |
| `COCKPIT_SteeringSpokes` | M03 |
| `COCKPIT_SteeringColumn`, `COCKPIT_Dash` | M05 |
| `FASTENER_*` | M14 |

> **Bütçe notu:** `docs/02` araç başına 8 materyal bütçesi öneriyor (kontrol U10, sadece WARN). 14 materyal
> bu bütçeyi aşar; render ve vitrin için sorun değil, oyun motoruna çıkacaksa M14→M03, M10→M09,
> M02→M01 birleştirilebilir. Geometri değişmez; materyal bölme/birleştirme `parts.py` palette'inde
> ve builder'lardaki materyal adlarında yapılır (bunu ben yaparım, doku gelince söyle).

---

## 2. Doku üretim kuralları (hepsi için geçerli)

**Çıktı seti (klasör):** `downloaded_resources/materials/<Ad>_2K-PNG/` altına, `docs/11` tanıdığı adlarla:
`<Ad>_Color.png` · `<Ad>_Roughness.png` · `<Ad>_Metalness.png` · `<Ad>_NormalGL.png` (opsiyonel `_Displacement.png`, `_Emission.png`).
Örnek: `PaintRed_2K-PNG/PaintRed_Color.png`. Kullanımı: `dict(pbr="PaintRed", tile_m=0.5)`.

**Boyut:** 2048×2048 (kare). Sadece albedo (renk) doku sRGB, diğerleri Non-Color / gri.

**ChatGPT (gpt-image) ile üretim — en iyi pratikler**
1. **Tek iş, tek görsel:** prompt "bir doku örneği (texture swatch)" istesin; araç, sahne, nesne yok.
2. **Kamera:** "straight top-down, orthographic, flat, no perspective, no vignette". Kenara kadar doldur, kenarlık yok.
3. **Işık:** "even diffuse lighting, no cast shadows, no specular hotspots, no baked reflections" → albedo "de-lit" olmalı; parlama/yansıma doku içine pişmemeli.
4. **Seamless:** "seamlessly tileable, edges match" yaz ama **%100 garanti vermez**: sonra Photoshop/GIMP `Offset %50` + clone, ya da Blender/Materialize/Substance Sampler "Make Seamless" ile dikişi temizle. Tekrar fark edilmesin diye tek bir belirgin leke/çizik bırakma ("no single dominant feature, uniform distribution").
5. **Yasaklar:** "no text, no logos, no watermark, no border, no frame, no people, no objects".
6. **Ölçek ipucu:** "macro photograph of about 20 cm of surface" gibi gerçek boyutu söyle; grain boyutu doğru çıkar.
7. **Yüksek kalite:** "photorealistic material scan, PBR albedo, 2K, sharp, no blur".
8. **Tutarlı harita seti için:** önce **albedo**'yu üret. Sonra **aynı görseli ChatGPT'ye yükleyip** (görsel düzenleme) şunu iste: *"Convert this exact image into a greyscale height map, same framing, same size, no new details."* Roughness için: *"…into a greyscale roughness map: white = rough, black = glossy…"*. Yeniden "sıfırdan üret" dersen detaylar kayar ve haritalar birbirini tutmaz.
9. **Normal map:** AI'dan doğrudan **isteme**; height map'ten türet: Materialize (ücretsiz), Substance Sampler, ya da Blender (Bump→Normal bake). DirectX çıktısıysa green kanalı çevirmeye gerek yok, `NormalDX` adını kullan; build otomatik çevirir.
10. **Metallic:** çoğu materyalde sabit değer (0 veya 1). Gri tonlu harita üretmeye gerek yok; sabit ver.
11. **Varyasyon:** her materyal için A ve B prompt'u aynı yapıdadır; iki sonucu yan yana Blender'da dene, hangisi iyi duruyorsa onu seç.

**Ortak prompt iskeleti** (aşağıdaki prompt'lar bunu kullanır):

> `[MATERYAL ve YÜZEY TARİFİ]. Seamlessly tileable PBR albedo texture, straight top-down orthographic view, flat even diffuse lighting, no shadows, no specular highlights, no reflections baked in, uniform detail across the whole image, edges match when tiled, macro photograph of about [BOYUT] of surface, sharp photorealistic material scan, square 1:1, 2048x2048. No text, no logos, no watermark, no border, no objects.`

Aşağıda her prompt bu iskeletin kısaltılmış değil **tam** halidir; doğrudan kopyala-yapıştır yapabilirsin.

**İnternetten bulma kaynakları (CC0):** ambientCG.com · polyhaven.com/textures · 3dtextures.me · cgbookcase.com · sharetextures.com. Lisansı (CC0/CC-BY) `project.md`'ye not edin.

---

## 3. Materyaller ve prompt'lar

Her materyal: **rol → hedef görünüm → hazır set arama anahtar kelimeleri → harita notları → Prompt A / Prompt B.**

### M01 — `MAT_PAINT_RED` · Gövde boyası (özgün, AI)
**Hedef:** derin, koyu "candy apple" kırmızı, ince metal flake'li, 1960'lar yarış arabası ama gösterişli. Tüm aracın karakteri bu materyal.
**Haritalar:** Color (düz ama çok hafif ton değişimli), Roughness (0.18–0.30 arası, hafif portakal kabuğu), Normal (çok hafif orange-peel + flake), Metallic sabit 0.3–0.5.
**Web arama:** "candy red metallic car paint", "automotive paint flake" (ambientCG `Paint`, `Metal` kategorileri).

**Prompt A — taze, parlak candy kırmızı**
```
Deep candy apple red automotive paint with a very fine metallic flake suspended under a thick clear coat, the red is saturated and dark with subtle lighter and darker cloudy variation, tiny uniformly scattered gold-red metal flakes catching the light, a very subtle orange-peel micro-texture. Seamlessly tileable PBR albedo texture, straight top-down orthographic view, flat even diffuse lighting, no shadows, no specular highlights, no reflections baked in, uniform detail across the whole image, edges match when tiled, macro photograph of about 10 cm of painted surface, sharp photorealistic material scan, square 1:1, 2048x2048. No text, no logos, no watermark, no border, no objects, no scratches.
```
**Prompt B — yaşlanmış, satin hot-rod kırmızısı**
```
Aged satin oxblood-red hot rod paint, slightly sun-faded and chalky in broad soft patches, faint hairline scratches and fine micro-swirls, a few barely visible tiny chips showing dark primer, thin dusty patina, the red is warm and deep with lighter faded areas, overall wear is evenly distributed with no single dominant mark. Seamlessly tileable PBR albedo texture, straight top-down orthographic view, flat even diffuse lighting, no shadows, no specular highlights, no reflections baked in, uniform detail across the whole image, edges match when tiled, macro photograph of about 20 cm of painted metal, sharp photorealistic material scan, square 1:1, 2048x2048. No text, no logos, no watermark, no border, no objects, no rust streaks.
```

### M02 — `MAT_PAINT_CREAM` · Krem şerit boyası (AI)
**Hedef:** vintage krem/fildişi, hafif sararmış emaye. Şeritler ince (8 cm) → doku ince ve düzgün.
**Haritalar:** Color, Roughness (0.3–0.45), Normal çok hafif. Metallic 0.
**Web arama:** "cream enamel paint", "ivory lacquer".

**Prompt A — taze fildişi emaye**
```
Fresh warm cream ivory enamel paint, smooth and slightly glossy, extremely subtle brush-free sprayed finish with a barely visible orange-peel texture, the colour is a soft off-white cream with a faint warm yellow tint, completely clean surface, tiny uniform micro-variation in tone. Seamlessly tileable PBR albedo texture, straight top-down orthographic view, flat even diffuse lighting, no shadows, no specular highlights, no reflections baked in, uniform detail across the whole image, edges match when tiled, macro photograph of about 10 cm of painted surface, sharp photorealistic material scan, square 1:1, 2048x2048. No text, no logos, no watermark, no border, no objects.
```
**Prompt B — yıpranmış, sararmış krem**
```
Aged vintage cream enamel paint, yellowed and slightly tobacco-stained in soft cloudy patches, fine craquelure hairline cracks barely visible, a few tiny edge-style chips revealing dark grey primer, light dust and faint scuff marks, warm ivory base colour with uneven aging, wear spread evenly with no dominant mark. Seamlessly tileable PBR albedo texture, straight top-down orthographic view, flat even diffuse lighting, no shadows, no specular highlights, no reflections baked in, uniform detail across the whole image, edges match when tiled, macro photograph of about 15 cm of painted surface, sharp photorealistic material scan, square 1:1, 2048x2048. No text, no logos, no watermark, no border, no objects.
```

### M03 — `MAT_CHROME` · Parlak krom (Web ağırlıklı)
**Hedef:** ayna krom. Albedo neredeyse sabit açık gri; asıl iş **roughness haritası** (parmak izi, mikro çizik, hafif sis). Metallic = 1.
**Web arama:** "chrome roughness", "polished metal scratches", ambientCG `Metal` (Metal049A vb. — `wb.py pbr preview --filter Metal` ile önizle).
**AI:** sadece **roughness varyasyonu** için (gri tonlu).

**Prompt A — ayna krom, mikro çizikli roughness**
```
Greyscale roughness map of a polished mirror chrome surface: mostly very dark near-black (glossy), with extremely fine random micro-scratches and faint swirl marks as slightly lighter grey, a few soft fingerprint-like smudges as very subtle mid-grey clouds, no strong features. Seamlessly tileable greyscale texture, straight top-down orthographic view, flat, uniform detail across the whole image, edges match when tiled, macro view of about 15 cm of surface, sharp, square 1:1, 2048x2048. Pure greyscale only, no colour, no text, no logos, no watermark, no border, no objects.
```
**Prompt B — yaşlanmış, puslu krom**
```
Greyscale roughness map of aged hazy chrome plating: dark grey base with soft milky haze clouds in lighter grey, scattered tiny pitting dots as small bright-grey specks, faint hairline scratches in random directions, slightly uneven wear, no single dominant feature. Seamlessly tileable greyscale texture, straight top-down orthographic view, flat, uniform detail across the whole image, edges match when tiled, macro view of about 15 cm of surface, sharp, square 1:1, 2048x2048. Pure greyscale only, no colour, no text, no logos, no watermark, no border, no objects.
```

### M04 — `MAT_ALUMINIUM_CAST` · Dökme alüminyum motor (Hibrit)
**Hedef:** motor bloğu/karter: kumlu döküm alüminyum, hafif yağ lekeli. Metallic 1, roughness 0.45–0.6.
**Web arama:** "cast aluminium", "sand cast metal", "bead blasted aluminium" (Metal/Rock-Metal).

**Prompt A — ham kum dökümü alüminyum**
```
Raw sand-cast aluminium engine casting surface: fine granular pitted grain, subtly irregular mottled grey-silver tone with slightly darker oxidised patches, tiny porosity pinholes, soft uneven micro-roughness, a faint dull satin finish, clean and unpainted. Seamlessly tileable PBR albedo texture, straight top-down orthographic view, flat even diffuse lighting, no shadows, no specular highlights, no reflections baked in, uniform detail across the whole image, edges match when tiled, macro photograph of about 15 cm of surface, sharp photorealistic material scan, square 1:1, 2048x2048. No text, no logos, no watermark, no border, no objects.
```
**Prompt B — kumlama (bead-blast) satin + yağ izi**
```
Bead-blasted satin aluminium engine casing, uniform fine peened matte texture in light silver-grey, with faint darker oil-film smudges and soft heat discolouration clouds in pale grey-brown, very subtle tool-free surface, wear evenly spread, no single dominant mark. Seamlessly tileable PBR albedo texture, straight top-down orthographic view, flat even diffuse lighting, no shadows, no specular highlights, no reflections baked in, uniform detail across the whole image, edges match when tiled, macro photograph of about 15 cm of surface, sharp photorealistic material scan, square 1:1, 2048x2048. No text, no logos, no watermark, no border, no objects.
```

### M05 — `MAT_BLACK_COATED` · Siyah kaplamalı çelik (Hibrit)
**Hedef:** jant, tel, fren kampanası, kokpit içi: mat/saten siyah toz boya, kenarda aşınma. Metallic 0.6–0.8 (aşınan yerler metalik), roughness 0.45–0.7.
**Web arama:** "black powder coat", "wrinkle finish paint", "black painted metal".

**Prompt A — mat siyah toz boya**
```
Matte black powder-coated steel surface, very fine uniform stippled orange-peel texture, deep near-black with barely perceptible dark-grey variation, tiny dust specks, no scratches, no gloss. Seamlessly tileable PBR albedo texture, straight top-down orthographic view, flat even diffuse lighting, no shadows, no specular highlights, no reflections baked in, uniform detail across the whole image, edges match when tiled, macro photograph of about 15 cm of surface, sharp photorealistic material scan, square 1:1, 2048x2048. No text, no logos, no watermark, no border, no objects.
```
**Prompt B — buruşuk (wrinkle) siyah + çıplak çelik aşınma**
```
Satin black crackle wrinkle-finish paint on steel, fine regular wrinkled ripple texture, with many tiny worn spots where bare grey steel shows through, light dusty grey wear, very dark charcoal base, wear distributed evenly across the surface with no dominant scratch. Seamlessly tileable PBR albedo texture, straight top-down orthographic view, flat even diffuse lighting, no shadows, no specular highlights, no reflections baked in, uniform detail across the whole image, edges match when tiled, macro photograph of about 15 cm of surface, sharp photorealistic material scan, square 1:1, 2048x2048. No text, no logos, no watermark, no border, no objects.
```

### M06 — `MAT_STAINLESS_HEAT` · Isıdan renklenmiş paslanmaz egzoz (özgün, AI)
**Hedef:** header'larda altın→mor→mavi ısı renkleri, boru boyunca kaynak izleri (Bugatti P900 / jet nozul referansları).
**Haritalar:** Color (ısı gradyanı — AI'nın en çok değer kattığı yer), Roughness 0.3–0.5, Metallic 1.
**Web arama:** "heat tinted stainless exhaust", "burnt titanium", "brushed stainless steel".

**Prompt A — fırçalı paslanmaz, saman-altın-mavi ısı geçişi**
```
Brushed stainless steel exhaust metal with horizontal fine brushing lines, heat-tinted in soft cloudy bands that flow from straw-gold to bronze to deep violet to electric blue, the colour bands are subtle and translucent over the silver metal, faint weld discolouration. Seamlessly tileable PBR albedo texture, straight top-down orthographic view, flat even diffuse lighting, no shadows, no specular highlights, no reflections baked in, uniform detail across the whole image, edges match when tiled, macro photograph of about 30 cm of surface, sharp photorealistic material scan, square 1:1, 2048x2048. No text, no logos, no watermark, no border, no objects.
```
**Prompt B — yanmış titanyum, iridescent kaynak**
```
Burnt titanium exhaust surface with iridescent oil-slick heat colours, patches of purple, blue, teal and gold blending smoothly, dull satin grey-silver metal underneath, faint darker soot and dull carbon dusting in soft areas, fine brushed grain, subtle weld-bead discolouration lines. Seamlessly tileable PBR albedo texture, straight top-down orthographic view, flat even diffuse lighting, no shadows, no specular highlights, no reflections baked in, uniform detail across the whole image, edges match when tiled, macro photograph of about 30 cm of surface, sharp photorealistic material scan, square 1:1, 2048x2048. No text, no logos, no watermark, no border, no objects.
```

### M07 — `MAT_EXHAUST_WRAP` · Isı sargısı (Web + AI)
**Hedef:** dokuma fiberglas/bazalt sargı, krem-bej, uçlarda kirlenmiş. Metallic 0, roughness 0.85–0.95, **normal map önemli** (dokuma kabarıklığı).
**Web arama:** "woven fabric", "basalt fabric", "canvas rough weave" (ambientCG `Fabric` serisi).

**Prompt A — temiz, bej dokuma sargı**
```
Woven fibreglass exhaust heat-wrap cloth, coarse regular plain weave with clearly visible threads, warm beige-cream colour with slightly lighter and darker thread variation, fuzzy loose fibres, matte, clean. Seamlessly tileable PBR albedo texture, straight top-down orthographic view, flat even diffuse lighting, no shadows, no specular highlights, uniform detail across the whole image, edges match when tiled, macro photograph of about 6 cm of fabric, sharp photorealistic material scan, square 1:1, 2048x2048. No text, no logos, no watermark, no border, no objects.
```
**Prompt B — kurumlu, yanık sargı**
```
Heat-stained exhaust wrap cloth, woven basalt fibre with coarse visible weave, scorched tan-brown and grey-black soot discolouration in soft cloudy patches, slight oily dark staining, dusty matte surface, individual fuzzy threads, uneven wear spread evenly across the image. Seamlessly tileable PBR albedo texture, straight top-down orthographic view, flat even diffuse lighting, no shadows, no specular highlights, uniform detail across the whole image, edges match when tiled, macro photograph of about 6 cm of fabric, sharp photorealistic material scan, square 1:1, 2048x2048. No text, no logos, no watermark, no border, no objects.
```

### M08 — `MAT_TYRE_RUBBER` · Lastik kauçuğu (Web + AI yan duvar)
**Hedef:** mat siyah kauçuk, ince kalıp dokusu, çok hafif yıpranma. Metallic 0, roughness 0.8–0.9. Desen (tread) bu dokuda yok; yan duvar yazısı ve tread **sonra ayrı bir decal / normal olarak** eklenecek.
**Web arama:** "rubber", "tyre rubber", "rubber sheet fine grain".

**Prompt A — yeni lastik, kalıp dokusu**
```
New matte black tyre rubber with a very fine uniform moulded micro-grain, tiny mould-release speckle, subtle faint fine radial lines from the mould, deep charcoal black with minimal tonal variation, completely clean. Seamlessly tileable PBR albedo texture, straight top-down orthographic view, flat even diffuse lighting, no shadows, no specular highlights, uniform detail across the whole image, edges match when tiled, macro photograph of about 15 cm of rubber, sharp photorealistic material scan, square 1:1, 2048x2048. No text, no logos, no watermark, no border, no objects, no tread pattern.
```
**Prompt B — yol görmüş, gri tozlu lastik**
```
Used road tyre rubber, dark grey-black with a dusty brown-grey oxidised bloom, fine scuff marks and tiny hairline cracks, slightly polished smooth patches, grit specks, matte, wear spread evenly with no dominant mark. Seamlessly tileable PBR albedo texture, straight top-down orthographic view, flat even diffuse lighting, no shadows, no specular highlights, uniform detail across the whole image, edges match when tiled, macro photograph of about 20 cm of rubber, sharp photorealistic material scan, square 1:1, 2048x2048. No text, no logos, no watermark, no border, no objects, no tread pattern.
```

### M09 — `MAT_LEATHER_SEAT` · Koltuk derisi (Web + AI)
**Hedef:** koltuk ve cowl pad: vintage naturel (tan) deri, belirgin tane, yıpranmış kenarlar. Metallic 0, roughness 0.5–0.65.
**Web arama:** "tan leather", "saddle leather", mevcut: `Leather037` (tan), `Leather009` (siyah) — `wb.py pbr preview --filter Leather`.

**Prompt A — naturel saddle (tan) deri**
```
Natural tan saddle leather, fine pebbled grain with soft irregular creases, warm caramel-brown colour with subtle lighter and darker tonal variation, a gentle hand-burnished patina, no stitching, no seams, clean. Seamlessly tileable PBR albedo texture, straight top-down orthographic view, flat even diffuse lighting, no shadows, no specular highlights, uniform detail across the whole image, edges match when tiled, macro photograph of about 20 cm of leather, sharp photorealistic material scan, square 1:1, 2048x2048. No text, no logos, no watermark, no border, no objects.
```
**Prompt B — koyu bordo, kullanılmış deri**
```
Dark oxblood burgundy leather seat hide, worn and softly creased with a satin patina, finer grain, slightly lighter rubbed highlights on raised areas and darker oily recesses, light surface cracking in tiny hairlines, no stitching, no seams. Seamlessly tileable PBR albedo texture, straight top-down orthographic view, flat even diffuse lighting, no shadows, no specular highlights, uniform detail across the whole image, edges match when tiled, macro photograph of about 20 cm of leather, sharp photorealistic material scan, square 1:1, 2048x2048. No text, no logos, no watermark, no border, no objects.
```

### M10 — `MAT_WOOD_WHEEL` · Ahşap direksiyon (Web)
**Hedef:** vintage Nardi stili maun/ceviz çember. Lake vernikli, metalik değil, roughness 0.25–0.4.
**Web arama:** "walnut wood", "mahogany", "varnished wood" (`Wood` kategorisi; damar yönü direksiyon çevresine denk gelsin diye dokuyu 90° döndürmen gerekebilir).

**Prompt A — koyu maun, derin vernik**
```
Dark varnished mahogany wood grain, straight fine parallel grain lines running horizontally, rich reddish-brown colour with subtle darker figure streaks and a few fine pores, clear gloss lacquer depth (but no reflections painted in), no knots, no cracks. Seamlessly tileable PBR albedo texture, straight top-down orthographic view, flat even diffuse lighting, no shadows, no specular highlights, uniform detail across the whole image, edges match when tiled, macro photograph of about 25 cm of wood, sharp photorealistic material scan, square 1:1, 2048x2048. No text, no logos, no watermark, no border, no objects.
```
**Prompt B — açık ceviz, yaşlanmış**
```
Aged walnut wood with a warm honey-brown tone, horizontal grain lines with visible pores and gentle cathedral figure, slightly worn satin lacquer, very faint hairline cracks in the finish and lighter rubbed patina, no knots. Seamlessly tileable PBR albedo texture, straight top-down orthographic view, flat even diffuse lighting, no shadows, no specular highlights, uniform detail across the whole image, edges match when tiled, macro photograph of about 25 cm of wood, sharp photorealistic material scan, square 1:1, 2048x2048. No text, no logos, no watermark, no border, no objects.
```

### M11 — `MAT_SMOKED_LENS` · Füme lens/plaka (AI, roughness + albedo)
**Hedef:** far gözlerinde koyu füme akrilik. Metallic 0, roughness çok düşük (0.05–0.2), çizik haritası önemli. Gerekirse sonradan kısmi alpha.
**Web arama:** "smoked acrylic", "tinted glass scratches".

**Prompt A — koyu füme akrilik**
```
Dark smoked tinted acrylic lens surface, near-black translucent charcoal with very subtle brown-grey tint variation, extremely fine micro-scratches in random directions, faint dust specks, very smooth. Seamlessly tileable PBR albedo texture, straight top-down orthographic view, flat even diffuse lighting, no shadows, no reflections baked in, uniform detail across the whole image, edges match when tiled, macro photograph of about 10 cm of surface, sharp photorealistic material scan, square 1:1, 2048x2048. No text, no logos, no watermark, no border, no objects.
```
**Prompt B — kehribar-füme, ince damarlı lens**
```
Amber-smoked tinted lens plastic, dark brown-black with faint warm amber glow variation, extremely fine concentric polishing swirl marks and light hazing near random areas, small dust specks, otherwise smooth. Seamlessly tileable PBR albedo texture, straight top-down orthographic view, flat even diffuse lighting, no shadows, no reflections baked in, uniform detail across the whole image, edges match when tiled, macro photograph of about 10 cm of surface, sharp photorealistic material scan, square 1:1, 2048x2048. No text, no logos, no watermark, no border, no objects.
```

### M12 — `MAT_CARBON` · Karbon fiber (Web)
**Hedef:** alt spoiler ve afterburner dış petalleri. 2×2 twill, vernikli. Metallic 0, roughness 0.2–0.35.
**Web arama:** `Fabric004` (projede zaten var, "carbon weave"), "carbon fibre twill", "forged carbon".

**Prompt A — klasik 2×2 twill**
```
Glossy 2x2 twill carbon fibre weave under clear lacquer, regular diagonal weave pattern with fine individual tows, deep black with subtle dark-grey weave contrast, perfectly straight pattern aligned to the image axes. Seamlessly tileable PBR albedo texture, straight top-down orthographic view, flat even diffuse lighting, no shadows, no specular highlights, no reflections baked in, uniform detail across the whole image, edges match when tiled, macro photograph of about 6 cm of surface, sharp photorealistic material scan, square 1:1, 2048x2048. No text, no logos, no watermark, no border, no objects.
```
**Prompt B — forged (mermer) karbon**
```
Forged carbon composite with randomly oriented chopped carbon fibre flakes forming a marbled pattern, black and dark-grey angular flake shapes with fine edge detail, no regular weave, matte-satin lacquer, uniform distribution. Seamlessly tileable PBR albedo texture, straight top-down orthographic view, flat even diffuse lighting, no shadows, no specular highlights, no reflections baked in, uniform detail across the whole image, edges match when tiled, macro photograph of about 10 cm of surface, sharp photorealistic material scan, square 1:1, 2048x2048. No text, no logos, no watermark, no border, no objects.
```

### M13 — `MAT_AB_GLOW` · Afterburner parlaması (emissive, özgün, AI)
**Hedef:** referans jet nozulundaki gibi içte parlayan sıcak astar. Bu doku **Emission** olarak kullanılır (şu an sabit turuncu). Metallic 0.
**Not:** rengi turuncu→beyaz (sıcak) ya da mavi→mor (jet referansı).

**Prompt A — turuncu-beyaz sıcak metal**
```
Glowing red-hot incandescent metal surface seen from above, brightest near-white yellow cores fading to saturated orange and deep red in soft organic cloudy gradients, faint vertical streaky heat shimmer lines, no shapes or objects, pure self-illuminated emissive texture. Seamlessly tileable emissive texture, straight top-down view, completely flat, uniform detail across the whole image, edges match when tiled, square 1:1, 2048x2048. No text, no logos, no watermark, no border, no objects, no sparks, no smoke, no background.
```
**Prompt B — mavi-mor jet alevi**
```
Glowing afterburner plasma surface, electric blue and violet streaks blending into hot pink-orange cores, long soft horizontal motion streaks like jet exhaust shock diamonds, smooth luminous gradients, no shapes or objects, pure self-illuminated emissive texture. Seamlessly tileable emissive texture, straight top-down view, completely flat, uniform detail across the whole image, edges match when tiled horizontally and vertically, square 1:1, 2048x2048. No text, no logos, no watermark, no border, no objects, no sparks, no smoke, no background.
```

### M14 — `MAT_STEEL_BRUSHED` · Fırçalı çelik perçin/cıvata (Web)
**Hedef:** perçinler ve cıvatalar: hafif fırçalı, mat çelik. Çok küçük parçalar; detaya fazla yatırım gerekmez. Metallic 1, roughness 0.35–0.5.
**Web arama:** "brushed steel", "galvanized steel", "zinc plated".

**Prompt A — fırçalı çelik**
```
Brushed raw steel, very fine parallel horizontal brushing lines, neutral cool silver-grey with subtle lighter and darker streak variation, a few extremely fine random scratches, clean. Seamlessly tileable PBR albedo texture, straight top-down orthographic view, flat even diffuse lighting, no shadows, no specular highlights, no reflections baked in, uniform detail across the whole image, edges match when tiled, macro photograph of about 10 cm of surface, sharp photorealistic material scan, square 1:1, 2048x2048. No text, no logos, no watermark, no border, no objects.
```
**Prompt B — çinko kaplı, mat**
```
Dull zinc-plated steel fastener metal, matte blue-grey with a soft mottled crystalline "spangle" texture, tiny dark pin-prick spots and light oxidation haze, no brushing lines, uniform distribution of detail. Seamlessly tileable PBR albedo texture, straight top-down orthographic view, flat even diffuse lighting, no shadows, no specular highlights, no reflections baked in, uniform detail across the whole image, edges match when tiled, macro photograph of about 10 cm of surface, sharp photorealistic material scan, square 1:1, 2048x2048. No text, no logos, no watermark, no border, no objects.
```

---

## 4. Çalışma sırası (öneri)

1. Önce **önizleme**: `python wb.py pbr list` ve `python wb.py pbr preview --filter Metal` ile projedeki hazır setlere bak (Fabric004 karbon, Leather037/009 deri zaten var).
2. **Aracın kimliğini veren üç doku önce:** M01 (gövde boyası), M06 (egzoz ısı rengi), M13 (afterburner parlaması). Gerisi hazır setlerle de iyi görünür.
3. Her AI görseli: albedo → seamless'a çevir → ChatGPT'ye geri yükleyip height + roughness üret → Materialize ile normal map türet → klasöre koy → bana yaz.
4. Ben `parts.py` palette'ini 14 materyale genişletirim, builder'lardaki materyal adlarını yukarıdaki haritaya göre ayarlarım, `box_uv` ölçeğine göre `tile_m` değerlerini ayarlarım ve build + render alırım.

> Not: bu aşamada **hiçbir geometri veya kod değişmedi**; mevcut 8 düz materyal duruyor. Sadece planlama.
