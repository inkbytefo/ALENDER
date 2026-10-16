# VEH_Sonnet_Bike

## Category
vehicle (motorcycle)

## Objective
Comprehensive redesign and hyper-roadster transformation of the custom inline-4 platform ("Sonnet Bike").
Infused with Claude Sonnet signature aesthetic: warm terracotta/copper metallic pearlescent bodywork,
forged carbon aerodynamic components, gold-anodized inverted USD suspension, dual bi-LED projector
headlight with glowing DRL halo ring, digital TFT cockpit display, transverse hydraulic steering damper,
CNC bar-end mirrors, curved high-performance oil cooler with braided AN lines, aerodynamic bellypan spoiler,
and upswept slash-cut racing exhaust.

## References
- ref/REAL_REFERENCE.png — original platform reference (inline-4 engine, chassis geometry)
- ref/MODELING_CHEATSHEET.png — mechanical decomposition

## Scale & measurements
- 400 px/m from tyres 120/70-17 (240 px) and 180/55-17 (250 px)
- cross-checks: length 820 px = 2.05 m, height 418 px = 1.045 m
- wheelbase 1.444 m; rake 22°; seat 0.80 m

## Style / budget
STYLE=realistic_game · LOW < 60k tris · HIGH < 150k tris · 8 materials

## Part breakdown
- **wheels**: 120/70-17 front & 180/55-17 rear, 5-split Y-spokes, directional sport tread sipes (S3)
- **brakes**: 320mm dual wave/petal floating front rotors with gold anodized bobbins, Brembo-style radial monobloc 4-piston calipers, rear wave disc & underslung caliper
- **frame**: steel trellis backbone, rear down tubes, central spine, CNC pivot plates with lightening pockets, subframe
- **swingarm**: box-section swingarm with cantilever upper truss, paddock spools, **carbon rear hugger & integrated chain guard**
- **rear_susp**: remote reservoir piggyback monoshock with gold canister, preload collar, Sonnet copper coil spring
- **drive**: lightened 45T rear sprocket, 16T countershaft sprocket, 525 roller chain loop
- **tank**: sculpted aerodynamic fuel tank with aggressive knee recesses, front ram-air intakes, carbon knee grip pads, flush aircraft billet cap
- **seat**: ergonomic dark Alcantara single saddle, monoposto aerodynamic tail cowl with twin venturi flow tunnels, integrated LED lightblade taillight, minimalist CNC tail tidy with micro-LED bullet indicators
- **bellypan**: sculpted aerodynamic engine chin spoiler with side winglet strakes and heat extraction vents
- **cooling**: curved multi-row racing oil cooler with protective honeycomb mesh, billet brackets, braided AN-fitting lines
- **engine**: inline-4 block, crankcase, transmission, DOHC cam cover, stator covers, sump, proud cooling fins, spark plugs & ignition wires
- **intake**: 4 racing carburetors, intake boots, turned billet aluminum velocity stacks, throttle return linkage
- **exhaust**: 4 sweeping stainless headers with CNC spigots, swivel retention springs, titanium pie-cut weld rings, 4-into-1 merged collector, upswept slash-cut racing muffler with carbon sleeve and titanium honeycomb mesh endcap
- **front**: inverted USD forks with Kashima/Öhlins gold anodizing, mirror chrome inner sliders, radial feet, dual projector headlight with glowing amber DRL Halo ring, aerodynamic carbon flyscreen, **aerodynamic carbon front fender with billet fork struts**
- **controls**: clip-on handlebars, rubber grips, weighted bar ends, **CNC billet reverse bar-end mirrors**, switch housings, adjustable racing levers, smoke fluid reservoirs, **TFT widescreen digital instrument cluster**, **transverse hydraulic steering damper**, CNC rearset footpegs & linkages
- **details**: instanced engine casing bolts, pinch bolts, caliper bolts, axle nuts, braided stainless front and rear brake lines

## Finish steps
```bash
python wb.py build VEH_Sonnet_Bike               # S1-S3 gated pipeline
python wb.py run projects/VEH_Sonnet_Bike/finish_paint.py       # master material + PBR instances
python wb.py present VEH_Sonnet_Bike --style studio_dark        # studio dark presentation sheet
python wb.py present VEH_Sonnet_Bike --style clay               # studio clay presentation sheet
```
