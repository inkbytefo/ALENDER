import os
import shutil
from pathlib import Path

BASE_DIR = Path("AssetM\u0131grat\u0131onFromPublictoUS/RawAssets")

MAPPING = {
    # Weapons_Firearms / Pistols
    "9mm-pistol.zip": "Weapons_Firearms/Pistols",
    "animated-pistol.zip": "Weapons_Firearms/Pistols",
    "colt-m1911-a1-game-ready-rigged.zip": "Weapons_Firearms/Pistols",
    "fps-pistol-animated.zip": "Weapons_Firearms/Pistols",
    "fps-pistol-animations.zip": "Weapons_Firearms/Pistols",
    "pistol-9mm-semi-auto.zip": "Weapons_Firearms/Pistols",
    "pistol-9mm.zip": "Weapons_Firearms/Pistols",
    "pistol-with-engravings.zip": "Weapons_Firearms/Pistols",

    # Weapons_Firearms / Rifles_Carbines
    "ak74u-free-animation.zip": "Weapons_Firearms/Rifles_Carbines",
    "ar-15 (1).zip": "Weapons_Firearms/Rifles_Carbines",
    "ar-15.zip": "Weapons_Firearms/Rifles_Carbines",
    "honey-badger.zip": "Weapons_Firearms/Rifles_Carbines",
    "krinkov-aks-74u.zip": "Weapons_Firearms/Rifles_Carbines",
    "old-defender-dmr.zip": "Weapons_Firearms/Rifles_Carbines",
    "old_-_defender_dmr.glb": "Weapons_Firearms/Rifles_Carbines",

    # Weapons_Firearms / Sniper_Rifles
    "l115a3.zip": "Weapons_Firearms/Sniper_Rifles",
    "low-poly-haenel-rs9.zip": "Weapons_Firearms/Sniper_Rifles",

    # Weapons_Firearms / Shotguns
    "mossberg500-shotgun-low-poly.zip": "Weapons_Firearms/Shotguns",
    "mossberg500_shotgun_low-poly.glb": "Weapons_Firearms/Shotguns",
    "shotgun-animated.zip": "Weapons_Firearms/Shotguns",

    # Weapons_Firearms / SMG
    "smg-fps-animations.zip": "Weapons_Firearms/SMG",
    "smg-gun.zip": "Weapons_Firearms/SMG",

    # Weapons_Melee
    "bowie-knife-hight-poly.zip": "Weapons_Melee",
    "cyberpunk-small-blade (1)": "Weapons_Melee",
    "cyberpunk-small-blade (1).zip": "Weapons_Melee",
    "switchknife (1).fbx": "Weapons_Melee",

    # Explosives_Grenades
    "frag-grenade-m67.zip": "Explosives_Grenades",
    "m69-frag-grenade.zip": "Explosives_Grenades",

    # Vehicles
    "2021-ducati-panigale-v4-sp.zip": "Vehicles",
    "sa342m-gazelle.zip": "Vehicles",
    "rwd-car-suspensionchassis.zip": "Vehicles",

    # Characters_Animation
    "soldier.zip": "Characters_Animation",
    "Soldier12.fbx": "Characters_Animation",
    "ARMS.rar": "Characters_Animation",
    "Walk With Rifle.fbx": "Characters_Animation",

    # Environment_Props
    "basket-ball-court-game-ready-asset.zip": "Environment_Props",
}

def main():
    print(f"Base Directory: {BASE_DIR.resolve()}")
    assert BASE_DIR.exists(), f"Directory not found: {BASE_DIR}"

    for item_name, target_rel_dir in MAPPING.items():
        src_path = BASE_DIR / item_name
        dest_dir = BASE_DIR / target_rel_dir
        dest_path = dest_dir / item_name

        if not src_path.exists():
            print(f"[SKIP] Source not found: {src_path}")
            continue

        dest_dir.mkdir(parents=True, exist_ok=True)
        print(f"[MOVE] {item_name} -> {target_rel_dir}/")
        shutil.move(str(src_path), str(dest_path))

    print("\nReorganization complete.")

if __name__ == "__main__":
    main()
