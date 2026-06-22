<!--
PROVENANCE / HOW TO USE THIS FILE
=================================
This file is a single, self-contained CAD-generation prompt for the most
recent iteration of the Vertical Cloud Lab "Powder Doser" (a.k.a. "Powder
Excavator"). It was assembled (issue #104) by scraping every relevant
comment and CAD source in this repository, the same way the Record of
Designs (issue #73) was built. It is meant to be copy-pasted, verbatim and
in full, into Copilot, CADSmith, and zoo.dev (Text-to-CAD) so the three
tools can be compared head-to-head on identical input.

Primary sources scraped for the dimensions below:
  * PR #66  — dual-servo mounting plate + shortened baseplate
              (cad/mounting-plate-assembly/kcl/params.kcl), comments
              4721011696, 4724310328, 4724445130, review 4509355231
  * PR #49  — geared / storage / threaded Archimedes auger + pinion
              (cad/auger-geared/*.scad), comments 4712371378, 4720918755,
              4745883012, 4747154534, 4747283303
  * PR #51  — split tap collar + mount plate (design/cad/tap-collar/)
  * Issue #48 comment 4513155870 — the four nozzle variants (v4 is standard)
  * zoo.dev attachment "tapCollar3.step" (most recent tap-collar geometry;
    PR #105 comment 4771809554 — a STEP export of the same model previously
    shared as "tap collar 3.zip"/STL. Measured bbox 48.70 × 17.00 × 70.10 mm;
    its cylinders confirm the PR #51 dims: collar OD 33.5, bore Ø25.5,
    coin-motor pad Ø10, solenoid bushing Ø6.9, M3 holes Ø3.4.)

NOTE: this is a TEXT-ONLY prompt. The STEP/STL above are not pasted or
attached — they were measured only to verify the numbers written here, so the
prompt stays self-contained and tool-agnostic. Every part description below
includes a short "why it matters" note so the generating tool understands the
*function* each feature serves, not just its dimensions.

You can paste the whole document (including this comment) or, for the
cleanest test, paste everything below the "=== BEGIN PROMPT ===" line.
All dimensions are in millimetres unless stated otherwise.
-->

# Powder Doser — full assembly prompt (Copilot vs. CADSmith vs. zoo.dev)

=== BEGIN PROMPT ===

## 0. Task

Design the complete **Powder Doser** assembly: a vertically-orientable,
auger-fed, gravity-and-screw powder dispenser that meters small, repeatable
amounts of dry powder (e.g. table salt, xanthan gum) out of a single
nozzle. Produce every 3D-printed part listed below as a separate, manifold,
FDM-printable solid (PLA/PETG, 0.4 mm nozzle, ~0.2 mm layers), plus an
assembly that shows how they fit together with the off-the-shelf
(purchased) parts. Output STEP for each part and an assembly, and—if your
tool supports it—native source (SCAD / KCL / CadQuery).

Hold the tolerances in §7. Respect the part-to-part interaction rules in
§6 exactly: several clearances are deliberate running fits and one is a
deliberate interference.

## 0.1 How it works (design intent — read first)

This explains *what each subsystem is for* so you can reason about the
geometry, not just copy numbers. The device dispenses dry powder by turning
an **Archimedes screw (auger)** inside a tube: rotating the screw walks powder
along the helix and pushes a small, repeatable slug out the nozzle each
revolution — so **dose ∝ revolutions**, which is what makes it meterable.
Because the screw (not gravity) does the conveying, it keeps metering even
when aimed horizontally or uphill, where a plain gravity hopper would stall or
dump.

- **Auger + nozzle** = the metering element. The screw geometry (pitch,
  tapered v4 tip, 1/3-screw / 2/3-reservoir split) sets how much powder moves
  per turn and prevents free-flow/clogging. This is the heart of the device.
- **Stepper + pinion + auger gear (3:1 reduction)** = the actuator. A stepper
  gives open-loop, countable rotation (dose-by-steps); the 3:1 reduction
  trades speed for the torque needed to shear/convey packed powder.
- **Tap collar (vibration motor + solenoid)** = anti-bridging. Powders arch
  and stick; a buzz (coin ERM) plus a periodic hammer-tap (solenoid striking
  the tube wall) break those bridges so flow stays consistent. The collar must
  spin-float on the tube but be rotationally arrested so it can't wind up its
  own wires.
- **Tilting mounting plate + dual servos/hinge gears** = aiming. The whole
  auger tilts from horizontal to vertical-down so powder can be delivered into
  a target (vial, pan) at any angle; two servos share the lifting load and
  keep the plate from racking.
- **Baseplate, brackets, mounts** = structure. They locate every part on a
  common datum (auger axis at Z = +29.25 above the plate) and bolt the
  assembly to an external frame.
- **Optional scale (HX711 / serial)** = closed-loop dosing: weigh the output
  and stop at a target mass instead of trusting step-count alone.

## 1. Coordinate system & global layout

- The **auger long axis is +Y**. The **dispense tip is at +Y**; the
  **motor/storage end is at −Y**. **+Z is up**; dispensed powder falls in
  **−Z**. Origin: auger axis at X=0, Z chosen so the auger bore centreline
  sits at **Z = +29.25 mm above the mounting-plate top**.
- The whole auger + drive sits on a **mounting plate** ("the table") that
  **tilts** about a transverse (X-axis) hinge at the +Y (dispense) end, so
  the dispenser can be aimed anywhere from horizontal to vertical-down. The
  tilt is driven by **two servos** (one per side) through gears.
- Order of parts along the auger axis, from the hinge (+Y) toward the motor
  (−Y): **hinge → front bracket → tap collar → auger gear band (with the
  stepper motor meshing beside it) → rear bracket**.

## 2. Part list (what to design)

3D-printed parts:
1. **Archimedes auger — storage variant** (primary), with the standard
   **v4 nozzle**. Full length and a short bench-test length. *Why: this is the
   metering element — the rotating screw is what conveys and doses the powder.*
2. **Threaded sealable auger** variant + **screw-on cap** (bottle-cap style).
   *Why: lets you pre-fill, seal, store and swap a charged auger like a
   cartridge without spilling powder.*
3. **Stepper pinion** (16-tooth) for the NEMA 11. *Why: couples the motor to
   the auger gear at a 3:1 reduction for countable, high-torque dosing.*
4. **Mounting plate** ("table") — tilts, carries the auger, brackets, tap
   collar, stepper block, and the two gear-toothed hinge lobes. *Why: the
   moving "table" that aims the whole dispenser and keeps every part on one
   datum.*
5. **Baseplate** — fixed forward tab the mounting plate hinges on; carries
   the two servos. *Why: the ground reference that bolts to the frame and
   reacts the tilt load.*
6. **Hinge arms** (part of the baseplate) + shared **M5 hinge pins**. *Why:
   define the tilt axis and carry the plate's weight.*
7. **Servo pinion** (20-tooth) — one per servo, drives a mounting-plate
   hinge gear. *Why: 2:1 step-down from servo to plate for finer, stronger
   tilt control.*
8. **Auger bracket(s)** — split shaft-collar clamps that support the auger
   on the plate (front + rear). *Why: hold the spinning auger concentric and
   set its height while letting it rotate freely.*
9. **Tap collar** — independent split collar carrying a vibration motor and
   a push/pull solenoid, with a hardstop. *Why: knocks/vibrates the tube to
   stop powder bridging so dosing stays consistent.*
10. **Tap-collar mount plate** — bracket-style plate with the rotation
    hardstop. *Why: holds the collar's angular position so it can't spin with
    the auger and tangle its wires.*

Off-the-shelf parts to accommodate (model as envelopes / mounting features,
do not redesign): see §5.

## 3. Auger (PR #49 geometry)

Shared tube geometry (identical across every auger variant):
- Outer tube **OD = 25.0**, **wall = 2.0**, so **bore ID = 21.0**
  (outer radius 12.5, inner radius 10.5).
- **Full length = 250.0** (short bench-test length = 90.0; an alternate
  full-height variant is 180.0).
- **Top cap height = 6.0**, with **4 loading slots** (rectangular,
  width 4.0 × length 7.0, on a 6.5 radius bolt circle, evenly spaced) plus
  a central **M3 pilot boss**. (The threaded variant omits this 4-slot
  cover — its filling end is a smooth open cylinder closed by the cap.)
- **Bottom funnel / cap height = 12.0**, tapering to a single **exit hole
  Ø3.0** centred on the axis.

Internal Archimedean screw:
- **Central shaft Ø8.0** (radius 4.0) on the axis.
- **Single-start helical fin**, **pitch = 10.0 mm/turn**, **thickness =
  2.0** (≈5 perimeters at a 0.4 mm nozzle). The fin inner edge overlaps the
  shaft by 0.4 and the outer edge overlaps the inner tube wall by 0.2 (for
  print manifold-ness). The helix must be **continuous** end-to-end (no gap
  at the gear band).

**Standard nozzle = v4** (from issue #48): the central shaft ends in a
**conical tip** that tapers from 0.4 radius at the bottom up to the full
4.0 shaft radius over the 12 mm bottom-cap height, and the helix follows
that taper down to ~0.5 mm above the exit plane, while the bottom funnel
opens from the Ø3.0 exit hole out to the inner wall. (Context: v4 meters
small, consistent amounts in every orientation, even uphill; v1 dispenses
too fast when vertical, v2 clogs on coarse crystals, v3 can jam in its
small gap.)

External drive gear band (full-length auger only):
- **Spur gear, module 1.0, 48 teeth, 20° pressure angle, face width 10.0**.
  Pitch Ø48.0, **tip Ø50.0**, root Ø45.5.
- The band is **annular** — the Ø21 bore stays fully open straight through
  it (do NOT fill the band with a solid disc; that would seal the bore).
- Band centre is **83.33 mm from the dispense (+Y) end** (= length ÷ 3), so
  the same pinion/motor position fits the full and 180 mm variants.

**Storage variant (primary):** identical outer tube, bore, top cap, funnel
and gear band, but the **internal screw occupies only the bottom one-third**
of the length (screw top at length ÷ 3 ≈ 83.33 mm for the full part); the
**top two-thirds of the bore is left completely open as a loose-powder
reservoir**. Only the screw extent changes — the outer cylinder is
unchanged. Capacity ≈ 80 cm³ (full) / ≈ 56 cm³ (180 mm). The short
bench-test storage auger is 90 mm, no gear band, same 1/3-screw / 2/3-open
rule.

**Threaded sealable variant + cap:** add a **single-start external thread
on the top ~1 inch** of the tube and a matching screw-on cap:
- Thread length **25.4** (1 in), **pitch 4.0 mm/turn**, **depth 1.0**,
  **crest (major) radius = 12.5 (flush with the tube OD)**, **root (minor)
  radius = 11.5**, tooth half-angle 58°, right-handed.
- The thread must be **strictly external**: crests never exceed the 25 mm
  OD and roots cut inward only (so a Ø25 ring slides over the crests). Do
  **not** put the thread on the inside of the tube.
- **Cap** = a closed cup with the matching **internal** thread (same pitch /
  depth, grown radially by **0.35 mm** clearance for a hand fit), wall 3.0,
  solid top 3.0, ~3.0 clearance above the engaged threads, and a **1.5 mm ×
  45° chamfer** on the top outer edge. The cap may be larger than the auger
  OD (≈ Ø31.7 × 31 tall); only the auger thread is constrained to the OD.
  One cap fits both threaded augers.

## 4. Drive train & mounting-plate assembly (PR #66 geometry)

### 4.1 Stepper pinion (NEMA 11)
- **16 teeth, module 1.0, 20° PA, face width 10.0**. Pitch Ø16, **tip Ø18**,
  root Ø13.5.
- Mates with the 48-tooth auger band: **centre distance C = 32.0**, **ratio
  3.0 : 1** (reduction onto the auger).
- Bore **Ø5.0 + 0.2 mm radial slip-fit** for the NEMA 11 round shaft;
  **hub Ø9.0** rising 6.0 above the gear face; **M3 radial setscrew**
  (Ø2.5 pilot, axis 3.0 above the gear face) locks the pinion to the shaft.
- The NEMA 11 body clears the auger OD by ≈5.4 mm radially at C = 32.

### 4.2 Mounting plate ("the table" — tilts)
- **Thickness 6.0.** Symmetric about X=0. **X envelope ≈ ±54.1**
  (width ≈ 108.2). **Y envelope ≈ [−15, +115]** (≈130 mm, a little over
  half the earlier length — the rear was trimmed and the rear bracket moved
  forward to Y ≈ −2).
- Auger bore axis sits at **Z = +29.25 above the plate top** (set by the
  lifted 14 mm-thick brackets), so the Ø50 gear band clears the plate top by
  ≈4.25 mm — no plinths, no through-plate slot.
- Open **U-notch in the +Y edge** (width 32.0, starting 35 mm back from the
  front edge) for the auger to overhang in mid-air; this notch also splits
  the two front ramps and the two side hinges.
- Carries, on its **top surface only** (nothing hangs under it): the front +
  rear auger brackets, the tap-collar mount, the NEMA 11 motor block, two
  front triangular ramps, and **two side hinge lobe stacks**.
- **Two hinge gear bands** (one per side, mirrored about X=0): **40 teeth,
  module ≈ 0.9083, 20° PA**, pitch Ø ≈ 36.33, **tip Ø ≈ 38.15**, face width
  = the outer hinge-lobe width. The plate is lifted by **two gears, one each
  side** (dual-servo), not one.

### 4.3 Baseplate (fixed forward tab)
- **Thickness 6.0.** Rectangular forward-only tab: **X ∈ [−100, +100]**
  (200 wide) × **Y ∈ [+55, +115]** (60 deep). The **two rear corners are
  chamfered 25.0 × 45°**. Baseplate bottom at **Z = −14**. (All legs and the
  rear/trapezoidal tabletop of earlier versions are removed — this part
  bolts onto a separate frame.)
- **Four Ø5.4 (M5 clearance) mounting holes** near the four tab corners at
  **X = ±80, Y = +68 and +105** (square-ish pattern, clear of the chamfers).
- Carries the **two hinge arms** (middle layer of each hinge sandwich) and
  the **two servo porches/posts + underside flanges**.

### 4.4 Hinge (one each side of the auger gap)
- **3-layer sandwich** per side: {inner mounting-plate lobe, middle
  baseplate arm, outer mounting-plate lobe (carrying the 40T gear band)},
  sharing a single **M5 pin** per side. 0.4 mm gap between layers.
- **Hinge axis is 10 mm forward of the baseplate front edge**, at
  **Z = +29.25** (same height as the auger axis). Hinge eye **OD 18.0**,
  bore = M5 (Ø5.4).
- Hinge-post / arm depth reduced to **35 mm** so it clears the front
  bracket. The arm's −Y (motor-side) face is sloped (~58° from horizontal —
  the angle produced by a 16 mm run at the arm height, not an independently
  toleranced dimension) so the plate underside can sweep through 45° and beyond without
  hitting the arm.

### 4.5 Servos (dual MG996R) + servo pinions
- **Two MG996R servos, mirrored across X=0**, working together to drive the
  plate tilt. Each drives a 40T hinge gear through a **20-tooth servo pinion
  (module ≈ 0.9083)**, giving a **2 : 1 reduction at C = 27.25**; pinion tip
  Ø ≈ 20.2, pitch Ø ≈ 18.2, bore **Ø6 + a chordal flat** for the MG996R 25-T
  spline, with an **M3 countersink** for the spline screw.
- **MG996R body 40.0 (Y) × 20.0 (Z) × 36.8 (X, inward from the flange
  face); flange tip-to-tip 54.5; flange (ear) thickness 2.0; Ø5 mounting
  holes spread 49.5 (Y) × 10.0 (Z); spline offset 10.1 from the near body
  end.** The **spline axis sits 10.0 above the baseplate top** (= midline of
  the 20 mm-thick body).
- Servo mount per side: **two square posts** that sit **behind** the MG996R
  mounting holes, with the body protruding through the 40 mm gap between the
  posts; place the servo so the **driving-head tip overhangs the porch front
  edge by 5.0**. The +X post inboard faces sit at **X = ±59.0**; servo
  bodies occupy **X ∈ [±59.0, ±95.8]**.
- **Underside flanges + gussets** (one per servo): a 6 mm-thick flange rib at
  **X = ±79** dropping **40 mm below the baseplate bottom**, with a
  **triangular gusset** (10 thick × 20 run) right under the servo mount so it
  ties the flange to the baseplate. A **horizontal Ø5.4 (M5) hole** is
  drilled **through the gusset**, axis parallel to the auger (Y), **15 mm
  below the baseplate bottom**, so each flange is also a side-bolting point.

### 4.6 NEMA 11 motor block
- A boss on top of the plate at **X = +32** (= the gear centre distance),
  ~**36.2 × 36.2 footprint × 6 thick**, whose +Y face carries the NEMA 11
  face holes. Position it so the pinion centre lands exactly on the auger
  gear-band centre in Y (no Y offset).

### 4.7 Auger brackets
- Split shaft-collar style, flange **60 (X) × 12 (Y) × 14 (Z)** with **2 ×
  M3** clearance holes at **X = ±24**; the 14 mm-thick flange lifts the bore
  axis to **29.25** above the plate top. Collar ring OD **33.5**, with a
  clamp slot. Front and rear brackets are packed flush along Y against the
  tap collar / gear band with a 1.0 mm air gap so gravity holds the parts
  against the brackets.

## 5. Off-the-shelf parts to accommodate (don't redesign)

Model these as solid envelopes plus the mounting/interface features printed
parts must mate to. The dimensions below are transcribed from the part
datasheets so you do **not** need to look anything up — treat the explicit
numbers here as authoritative (several of these vendors block automated
lookups). All dimensions mm unless noted; they are nominal datasheet values,
so add the printed-part clearances from §7 on top.

**Quick reference**

| Item | Part | Envelope (L×W×H) | Mass |
|------|------|------------------|------|
| Stepper | NEMA 11 **11HS18-0674S** | 28.0 × 28.0 × 32.0 | ~100 g |
| Stepper driver | Pololu **Tic T500** | 25.4 × 15.2 × ~6 | ~3 g |
| Tilt servos (×2) | **MG996R** | 40.0 × 19.0 × 43.0 (incl. ears) | ~55 g ea |
| Tap solenoid | Adafruit 412 / **TAU0730TM** 12 V | 30.0 × 15.5 × 16.0 (body) | ~36 g |
| Vibration motor | **Ø10 coin ERM** | Ø10 × 3.4 | ~1 g |
| Haptic driver | **DRV2605L** breakout | 20.3 × 17.8 × ~3 | ~2 g |
| Solenoid driver | **DRV8871** breakout | 22.9 × 17.8 × ~3 | ~2 g |
| Controller | **RP2040 Pico / Pico W** | 51.0 × 21.0 × ~1 (PCB) | ~3 g |
| (Opt.) feedback | **HX711** + load cell | ~34 × 21 × ~3 (board) | ~3 g |
| Fasteners | **M3 / M5** screws + M3 setscrew | — | — |

Detailed dimensions and mounting instructions follow.

### 5.1 Stepper — NEMA 11, StepperOnline 11HS18-0674S
- **Body**: 28.0 × 28.0 mm square frame (corners chamfered ~1 mm), **length
  32.0 mm** (excluding shaft/wires). Frame is the standard NEMA 11 envelope.
- **Shaft**: **Ø5.0 mm round** (no D-flat / no keyway), protruding **18.0 mm**
  from the front face.
- **Front pilot**: raised **Ø22.0 mm × ~2.0 mm** boss centred on the shaft —
  the motor block's +Y face must clear/recess this so the body seats flat.
- **Face mounting holes**: 4 × tapped **M2.5**, on a **23.0 × 23.0 mm** square
  pattern (16.26 mm from the shaft axis on the diagonal), one per corner. (Our
  motor block uses an M3 boss pattern that overlaps these; clearance Ø3.4.)
- **Electrical (envelope only)**: bipolar **4-wire**, **1.8°/step**
  (200 full-steps/rev), **0.67 A/phase**, holding torque ≈ **6.5 N·cm**.
- Driven through the **16T pinion (§4.1)**; body must clear the auger OD by
  ≈5.4 mm at C = 32.

### 5.2 Stepper driver — Pololu Tic T500
- **PCB**: **25.4 × 15.2 mm** (1.0" × 0.6"), ~6 mm tall over components.
- **Mounting**: 2 × **Ø2.2 mm** holes (for #2 / M2 screws) on the 1.0" axis,
  set in 0.1" from the short edges along the board centreline.
- Headers on **2.54 mm (0.1") pitch**; USB micro-B on one short edge.
- Function only: USB/UART stepper controller that generates the motion ramps;
  firmware talks to it over UART (no mechanical interface to printed parts —
  mounts to the separate control board, **not** the dosing chassis).

### 5.3 Tilt servos — 2 × MG996R (see also §4.5)
- **Body** (gearbox case, excluding ears): **40.0 (L) × 19.0 (W) × 36.8 (H to
  top of case)**; **overall height ≈ 43.0** to the top of the spline boss.
- **Mounting ears**: two tabs extending the length to **tip-to-tip 54.5 mm**,
  **2.0 mm thick**, top of ears **~28.8 mm** above the case bottom; each ear
  has 2 holes → **4 × Ø4.8–5.0 mm** holes on a **49.5 (L) × 10.0 (W)** pattern.
- **Output spline**: **25-tooth (25T) Futaba-type spline**, pitch Ø ≈ 5.92,
  major Ø ≈ 6.0; centre **offset 10.1 mm** from the near (driving) body end and
  on the body centreline. Retained by a central **M3** (or self-tapping) horn
  screw → model an **M3 countersink** in the servo pinion.
- **Cable** exits the −L end. Operating **4.8–7.2 V**, stall ≈ **9.4 kgf·cm @
  4.8 V**. Mounting/clearance detail and post placement are in §4.5.

### 5.4 Tap solenoid — Adafruit 412 / Shanghai Chaocheng TAU0730TM (12 V push/pull)
- **Body**: roughly **30.0 (along plunger) × 15.5 × 16.0 mm** rectangular
  coil/frame. Treat as a box envelope around the plunger axis.
- **Mounting flange**: **2 × M3 clearance holes, diagonally opposite**, pitch
  **18.2 mm across the body × 16.0 mm along it** (the two used corners of the
  frame face). Model M3 clear Ø3.4 to match the tap-collar solenoid boss.
- **Plunger**: steel rod through a **Ø6.9 mm front bushing**; model the
  clearance bore as **Ø7.5 mm**. Stroke ≈ 10 mm; spring-returned push/pull.
- **Interface (critical)**: the **extended plunger tip reaches 3.0 mm inside
  the auger OD** to tap the auger wall — this is the one deliberate
  interference (§6). Plunger axis is **perpendicular to the auger (along X)**.
- Driven by the DRV8871 (§5.7); 12 V coil.

### 5.5 Vibration motor — Ø10 mm coin (ERM) haptic motor
- **Disc**: **Ø10.0 mm × 3.4 mm** thick (common "1034"; the thinner "1027" is
  Ø10.0 × 2.7 mm and also fits). Flat adhesive (3M) back face; two flying lead
  wires off one side.
- **Mounting**: bond into a shallow **Ø10.0 × ~1.0 mm adhesive recess** on the
  −X face of the tap collar (the 1.0 mm is just the glue pocket; the disc body
  then stands proud of the recess floor by its remaining thickness — **~2.4 mm
  for the 1034, ~1.7 mm for the 1027** — so leave at least 2.4 mm radial
  clearance to whatever sits outboard).
- Driven by the DRV2605L (§5.6).

### 5.6 Haptic driver — DRV2605L (Adafruit-style breakout)
- **PCB**: **20.3 × 17.8 mm** (0.8" × 0.7"), ~3 mm over components.
- **Mounting**: 2 × **Ø2.5 mm** holes (0.1" in from corners). Headers on
  **2.54 mm** pitch. I²C LRA/ERM haptic driver; mounts to the control board,
  not the chassis (envelope only).

### 5.7 Solenoid driver — DRV8871 (Adafruit-style breakout)
- **PCB**: **22.9 × 17.8 mm** (0.9" × 0.7"), ~3 mm over components.
- **Mounting**: 2 × **Ø2.5 mm** holes (0.1" in from corners). Headers on
  **2.54 mm** pitch. Brushed-DC / solenoid H-bridge (drives the 12 V tap
  solenoid); control-board mount only.

### 5.8 Controller — RP2040 (Raspberry Pi Pico / Pico W)
- **PCB**: **51.0 × 21.0 × ~1.0 mm**, castellated edges + **2 × 20-pin 0.1"
  (2.54 mm) headers** down the long edges (pins extend ~3 mm below).
- **Mounting**: **4 × Ø2.1 mm** holes on a **47.0 × 11.4 mm** rectangular
  pattern (2.0 mm in from each long edge, 2.0 mm from the ends). Micro-USB (or
  USB-C on some clones) on one short edge. Control-board mount only.

### 5.9 (Optional) feedback — HX711 + load cell, or A&D serial scale
- **HX711 breakout**: generic green board **~34 × 21 × ~3 mm**; SparkFun
  variant ~25.4 × 16.5 mm. 2 × Ø2.5 mounting holes, 0.1" headers. Pairs with a
  strain-gauge **load cell** (e.g. bar/single-point, M4/M5 bolt mounts) for
  closed-loop dose-by-weight. Envelope only.
- Alternatively an **A&D serial scale** over RS-232/MAX3232 (no chassis
  mounting). Either path is optional and does not change the printed parts.

### 5.10 Fasteners
- **M3** machine screws: clearance **Ø3.4**, self-tap pilot **Ø2.7**.
- **M5** machine screws (hinge pins, mount bolts): clearance **Ø5.4**.
- **M3 setscrew** (grub) for the stepper pinion: pilot **Ø2.5**.
- **M2 / M2.5** small screws for the breakout/driver boards (control board
  only). Use heat-set inserts or self-tapping into printed bosses as preferred.

## 6. Part-to-part interaction rules (read carefully)

- **Auger bore stays open**: the 48T gear band is annular — never seal the
  Ø21 bore. The internal helix is continuous through the band.
- **Pinion ↔ auger gear**: external mesh, parallel axes both along Y,
  C = 32.0, 3:1. The NEMA 11 body must clear the auger OD (≈5.4 mm gap).
- **Auger thread is EXTERNAL**, crest flush with the Ø25 OD; the **cap thread
  is INTERNAL**. They are a hand-screw pair (0.35 mm clearance). Do not swap
  these (a past iteration wrongly cut the thread inside the auger and into
  the cap wall).
- **Tap collar** wraps the auger between the front bracket and the gear band
  and must be able to **spin freely on the auger** EXCEPT that a **hardstop**
  (a bump on the tap-collar mount plate) arrests its rotation so it does not
  wind up its own wires with the turning auger. The collar must **not**
  clamp tight to the shaft (the clamp screw only sets a running fit).
- **Solenoid plunger is a deliberate INTERFERENCE**: its extended tip
  reaches **3.0 mm into the auger OD** to tap/impact the auger wall; its axis
  is **perpendicular to the auger (along X)**; plunger clearance bore Ø7.5
  (clears the Ø6.9 bushing).
- **Dual hinge/servo**: the plate is supported and lifted by **two** gear +
  servo sets, mirror-symmetric about X=0; both gears mesh at the same Z and
  the 2:1 reduction lives in the vertical (Z) centre distance C = 27.25.
- **No features hang below the mounting plate**; everything mounts on its top
  face. The baseplate, by contrast, carries the servos and the underside
  flanges.
- **Tilt clearance**: the mounting plate must sweep cleanly from 0° (flush)
  through 45° to vertical without the plate underside or its arm-clearance
  slot colliding with the baseplate hinge arms (all interference checks must
  read 0 mm³ at 0° / 45° / 90°).

## 7. Tolerances & print rules (summary)

- **Clearance/slip fits**: pinion bore Ø5 + 0.2 mm radial; auger/collar &
  bracket bore + 0.5 mm diametral running fit; printed thread + 0.35 mm
  hand fit.
- **Hole sizes**: M3 clearance Ø3.4, M5 clearance Ø5.4, M3 self-tap pilot
  Ø2.7, M3 setscrew pilot Ø2.5.
- **Gears**: 20° pressure angle throughout; ~0.15 mm backlash at pitch for
  printed teeth.
- **Deliberate interference**: solenoid tip 3.0 mm into the auger OD (only
  intentional interference in the assembly).
- **Print/manifold**: target 0.4 mm nozzle; fin/wall features ≥ 2 mm
  (≈5 perimeters); union overlaps 0.2–0.4 mm to stay manifold; print the
  auger upright (helix vertical) and gears flat (teeth in the print plane).
- All other mating faces are flush with only the 1.0 mm pack-gaps noted.

## 8. Most-recent tap-collar geometry note (zoo.dev "tapCollar3")

The latest physical tap-collar iteration was developed in zoo.dev and is
provided as **`tapCollar3.step`** (a STEP export of the same model earlier
shared as the `tap collar 3.zip`/STL — identical geometry, different file
type; PR #105 comment 4771809554). Measured bounding box **48.70 (X) ×
17.00 (Y) × 70.10 (Z) mm**. Its cylindrical faces confirm the PR #51
parametric dimensions exactly: **collar OD Ø33.5** (r 16.75), **auger bore
Ø25.5** (r 12.75 = auger OD 25 + 0.5 running fit), **coin-motor pad Ø10**
(r 5.0), **solenoid bushing Ø6.9** (r 3.45), and **M3 holes Ø3.4** (r 1.7).
So the STEP, the STL, and the PR #51 model all agree — the earlier 17-vs-24 mm
collar-depth ambiguity resolves to a **17 mm collar depth** along the auger
axis (the 24 mm figure was a superseded parametric value).

Use the functional spec in §4.7/§6 and these dimensions (bore Ø25.5 = auger OD
+ 0.5; collar OD 33.5; 2 mm clamp slot; **17 mm collar depth**; coin-motor pad
Ø10 on −X; solenoid boss on +Z with the 18.2 × 16.0 M3 pattern and Ø7.5
plunger path; +X hardstop ear) as the authoritative requirements, and treat
`tapCollar3.step` as the most recent geometric reference. *Remember why this
part exists: it both vibrates and hammer-taps the tube to stop powder
bridging, while its hardstop ear keeps it from rotating with the auger and
winding up the motor/solenoid wires — so the bore must be a free-spinning fit,
never a clamp, and the ear must positively engage the mount-plate stop.*

## 9. Deliverables

For each numbered part in §2: a manifold solid + STEP (and native source if
available). Plus one **assembly** (tilt at 0°) showing the auger, pinion,
NEMA 11 envelope, brackets, tap collar with solenoid + coin motor, mounting
plate, baseplate, dual servos and servo pinions, and the M5 hinge pins, in
their correct relative positions. Report any interference you find and
confirm the §6 clearances/interferences are met.

=== END PROMPT ===
