"""
Generates ref/REAL_REFERENCE.png and ref/REF_MASK.png for PROP_Plasma_Saber.
High-resolution 1280x720 orthographic reference schematic and pixel-accurate silhouette mask.
"""
import math
import os
from PIL import Image, ImageDraw, ImageFilter

W, H = 1280, 720
V0 = 360.0

SILHOUETTE_POLY = [
    # Emitter shroud top edge
    (1015.0, 307.5),
    (890.0, 307.5),
    # Bronze focus ring 2 & 1
    (890.0, 308.75),
    (840.0, 308.75),
    # Radiator base
    (840.0, 310.0),
    (810.0, 310.0),
    # Upper choke collar with cooling ribs
    (810.0, 320.0),
    (795.0, 320.0),
    (795.0, 312.5),
    (780.0, 312.5),
    (780.0, 320.0),
    (760.0, 320.0),
    # Crystal chamber top strut
    (760.0, 311.25),
    (680.0, 311.25),
    # Switch box housing (rises on +Z)
    (680.0, 311.25),
    (670.0, 311.25),
    (670.0, 302.5),
    (590.0, 302.5),
    (590.0, 311.25),
    (580.0, 311.25),
    # Grip choke band
    (580.0, 313.75),
    (530.0, 313.75),
    # Grip ribbed section
    (530.0, 312.5),
    (355.0, 312.5),
    (355.0, 316.25),
    (350.0, 316.25),
    # Lower clamp collar
    (350.0, 310.0),
    (325.0, 310.0),
    # Pommel cap
    (325.0, 316.25),
    (315.0, 316.25),
    (315.0, 311.25),
    (275.0, 311.25),
    (275.0, 317.5),
    (265.0, 317.5),
    # D-ring bracket and loop
    (265.0, 335.0),
    (245.0, 335.0),
    (245.0, 385.0),
    (265.0, 385.0),
    # Pommel cap bottom
    (265.0, 402.5),
    (275.0, 402.5),
    (275.0, 408.75),
    (315.0, 408.75),
    (315.0, 403.75),
    (325.0, 403.75),
    # Lower clamp collar bottom
    (325.0, 410.0),
    (350.0, 410.0),
    # Grip bottom
    (350.0, 403.75),
    (355.0, 403.75),
    (355.0, 407.5),
    (530.0, 407.5),
    (530.0, 406.25),
    (580.0, 406.25),
    # Mid collar bottom (switch box is only on +Z)
    (580.0, 408.75),
    (680.0, 408.75),
    # Crystal chamber bottom strut
    (680.0, 408.75),
    (760.0, 408.75),
    # Upper choke collar bottom
    (760.0, 400.0),
    (780.0, 400.0),
    (780.0, 407.5),
    (795.0, 407.5),
    (795.0, 400.0),
    (810.0, 400.0),
    # Radiator & focus rings bottom
    (810.0, 410.0),
    (840.0, 410.0),
    (840.0, 411.25),
    (890.0, 411.25),
    (890.0, 412.5),
    # Angled emitter shroud bottom cut
    (935.0, 412.5),
    # Diagonal cut back to top crown
]

def create_images():
    ref_dir = os.path.dirname(os.path.abspath(__file__)) + "/ref"
    os.makedirs(ref_dir, exist_ok=True)
    
    # 1. Mask image
    mask_img = Image.new("L", (W, H), 0)
    draw_mask = ImageDraw.Draw(mask_img)
    draw_mask.polygon(SILHOUETTE_POLY, fill=255)
    mask_path = os.path.join(ref_dir, "REF_MASK.png")
    mask_img.save(mask_path)
    print(f"Saved {mask_path}")
    
    # 2. Reference photo
    ref_img = Image.new("RGB", (W, H), (242, 242, 245))
    draw = ImageDraw.Draw(ref_img)
    
    # Soft shadow
    shadow_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_sh = ImageDraw.Draw(shadow_img)
    draw_sh.ellipse([230, 430, 1030, 475], fill=(30, 30, 35, 45))
    shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(12))
    ref_img.paste(shadow_img, (0, 0), shadow_img)
    draw = ImageDraw.Draw(ref_img)
    
    def draw_cylinder(u0, u1, r, base_col, highlight=0.3):
        v_top = V0 - r
        v_bot = V0 + r
        h = v_bot - v_top
        steps = 40
        for i in range(steps):
            t = i / float(steps)
            v_curr = v_top + t * h
            v_next = v_top + (i + 1) / float(steps) * h
            ang = (t - 0.5) * math.pi
            cos_factor = max(0.0, math.cos(ang))
            spec = max(0.0, math.cos((t - 0.28) * math.pi)) ** 3
            col = [
                min(255, max(0, int(base_col[c] * (0.45 + 0.55 * cos_factor + highlight * spec))))
                for c in range(3)
            ]
            draw.rectangle([u0, v_curr, u1, v_next], fill=tuple(col))
        draw.line([u0, v_top, u1, v_top], fill=(20, 20, 25), width=1)
        draw.line([u0, v_bot, u1, v_bot], fill=(20, 20, 25), width=1)
    
    DARK_TITAN = (45, 48, 52)
    CHROME = (185, 190, 195)
    BRONZE = (165, 120, 60)
    POLYMER = (28, 28, 30)
    
    # D-ring
    draw.ellipse([245, 335, 275, 385], outline=(150, 155, 160), width=6)
    draw.rectangle([260, 345, 268, 375], fill=CHROME)
    
    # Pommel
    draw_cylinder(265, 275, 42.5, DARK_TITAN)
    draw_cylinder(275, 315, 48.75, DARK_TITAN)
    for u in range(282, 312, 6):
        draw.rectangle([u, V0 - 45, u + 3, V0 + 45], fill=(20, 20, 22))
    draw_cylinder(315, 325, 43.75, CHROME)
    
    # Lower clamp collar
    draw_cylinder(325, 350, 50.0, CHROME)
    for u in [332, 342]:
        draw.line([u, V0 - 50, u, V0 + 50], fill=(70, 75, 80), width=1)
    
    # Grip assembly
    draw_cylinder(350, 530, 43.75, DARK_TITAN)
    for u in range(360, 520, 18):
        draw.rectangle([u, V0 - 47.5, u + 10, V0 + 47.5], fill=POLYMER)
        draw.line([u + 2, V0 - 46, u + 2, V0 + 46], fill=(50, 50, 55), width=1)
    # Knurled choke
    draw_cylinder(530, 580, 46.25, CHROME)
    for u in range(535, 575, 5):
        draw.line([u, V0 - 46, u + 2, V0 + 46], fill=(130, 135, 140), width=1)
    
    # Mid coupler & switch box
    draw_cylinder(580, 680, 48.75, DARK_TITAN)
    draw.rectangle([590, 302.5, 670, 311.25], fill=(35, 38, 42), outline=(15, 15, 18))
    draw.rectangle([605, 297.5, 630, 304], fill=(180, 40, 35), outline=(90, 20, 15))
    draw.rectangle([645, 299, 665, 304], fill=CHROME, outline=(60, 65, 70))
    for x in range(605, 665, 6):
        draw.rectangle([x, 306, x + 4, 310], fill=(0, 210, 255))
    
    # Crystal chamber
    draw_cylinder(680, 760, 48.75, DARK_TITAN)
    draw.rectangle([688, V0 - 32, 752, V0 + 32], fill=(200, 225, 240))
    draw.polygon([(702, V0), (720, V0 - 15), (738, V0), (720, V0 + 15)], fill=(0, 235, 255))
    draw.polygon([(710, V0), (720, V0 - 9), (730, V0), (720, V0 + 9)], fill=(220, 250, 255))
    draw.rectangle([688, V0 - 48.75, 752, V0 - 40], fill=DARK_TITAN)
    draw.rectangle([688, V0 + 40, 752, V0 + 48.75], fill=DARK_TITAN)
    
    # Upper choke collar with cooling ribs
    draw_cylinder(760, 810, 40.0, CHROME)
    draw_cylinder(780, 795, 47.5, CHROME)
    
    # Emitter assembly
    draw_cylinder(810, 840, 50.0, DARK_TITAN)
    draw_cylinder(840, 890, 51.25, BRONZE)
    
    # Angled emitter shroud
    shroud_pts = [(890, 307.5), (1015, 307.5), (935, 412.5), (890, 412.5)]
    draw.polygon(shroud_pts, fill=DARK_TITAN, outline=(25, 28, 30))
    draw.line([(890, 308.5), (1014, 308.5)], fill=(120, 125, 130), width=2)
    draw.line([(1014, 308.5), (935, 411.5)], fill=(160, 165, 170), width=2)
    for u in [910, 930, 950]:
        if u + 12 < 935 + (1015 - 935) * 0.5:
            draw.rectangle([u, V0 - 25, u + 10, V0 - 15], fill=(20, 22, 25))
    draw_cylinder(920, 960, 27.5, BRONZE)
    draw.ellipse([955, V0 - 20, 965, V0 + 20], fill=(10, 10, 12))
    
    ref_path = os.path.join(ref_dir, "REAL_REFERENCE.png")
    ref_img.save(ref_path)
    print(f"Saved {ref_path}")

if __name__ == "__main__":
    create_images()
