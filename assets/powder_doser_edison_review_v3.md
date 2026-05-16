# Edison Scientific design review v2 — powder doser v3 (focus: solenoid reach + ERM placement)

> **Source**: Edison Scientific platform, `ANALYSIS` agent.
> Wall time: 776 s. Query: 38.4 k chars. Answer: 5937 chars.
> **Inputs**: v3 `powder_doser_chassis.py`, `powder_doser_auger.py`,
> `powder_doser_pauses.json`, full PR conversation history including the user's
> cross-section screenshot showing the solenoid-cutout-not-reaching-bore
> concern.
> Specifically asked: (A) ensure the solenoid actuator reaches the auger
> without breaking it; (B) should the ERM stay embedded or use a "plunger of
> sorts" to keep it fixed; (C) any other P0/P1 issues in v3.

---

### A. Solenoid Reach Analysis & Concrete Fix

**The Problem:**
You correctly spotted that the solenoid slot does not functionally reach the auger tube. Your P0 concerns are entirely valid and break down into two specific geometric failures:
1. **Slot Height (Z) is too short:** The `solenoid_slot_h` is set to 2.5 mm, but the JF-0530B plunger is ~Ø4 mm. The plunger physically cannot pass through the slot; it will jam against the top and bottom.
2. **Missing Strike Chamber & Recess (X):** The JF-0530B body length is 22 mm. The pocket (`solenoid_pocket_x = 22.2`) spans from the chassis exterior face (X = -35.0 mm) to X = -12.8 mm. This leaves exactly 0.0 mm of travel room within the pocket for the plunger tip at rest (which protrudes ~4–5 mm). Furthermore, the outer wall of the rotating auger tube is at X = -12.5 mm. If the plunger was properly assembled, its resting tip would theoretically be embedded deep inside the rotating tube wall at X ≈ -7.8 mm, causing a physical collision.

**The Concrete Fix:**
To give the solenoid 5 mm of travel and ensure the plunger correctly strikes the rotating auger tube OD directly, you must increase the chassis depth on the -X face (creating an external boss) to accommodate the body plus the travel distance, open up the slot, and recess the pocket:

*   **Strike Target:** The plunger should directly strike the outside wall of the rotating PLA auger tube. A 2.0 mm PLA wall can withstand this 1 mJ tap, though over thousands of cycles it will become a wear part (acceptable for an FDM part).
*   **Code adjustments (`powder_doser_chassis.py`):**
    *   Change `solenoid_slot_h` from `2.5` to `5.0` (to clear the Ø4 plunger).
    *   Create a local external boss on the -X face: `solenoid_boss_x = 5.0` (extend the chassis face from X = -35 to X = -40 locally around Z=15).
    *   Shift the pocket origin deeper: Move the pocket's inner face from X = -12.8 back to X = -17.5. This creates a 5.0 mm "strike chamber" between the resting plunger face and the auger tube OD (at X = -12.5).
    *   Set the slot length to extend from X = -17.5 to X = -12.0. This ensures it fully bridges the strike chamber, cuts through the 0.2 mm air gap/sleeve wall, and gives the plunger an unobstructed flight path to the auger OD.

### B. ERM Placement Alternatives

Your suspicion that the PLA kills the vibration is correct. The impedance mismatch of the 0.2 mm air gap between the chassis bore sleeve and the rotating auger tube OD creates a ~40-60 dB structural-to-acoustic attenuation. By the time 0.8 G of vibration crosses the PLA and the air gap, <2 mG reaches the powder—nowhere near the 0.5–2.0 G needed for fluidization.

Here is the evaluation of your alternatives in priority order:

1. **Option (E): Skip ERM entirely; rely on the solenoid tap.**
    *   *Coupling:* High (>>1 G instantaneous tap).
    *   *Practicality:* Best. The solenoid imparts a sharp shockwave (impulse) that efficiently bridges the air gap when striking the tube OD directly. ERMs are meant for continuous fluidization, but since rotating electronics are off the table, the ERM cannot couple well enough to act as a primary declogger. 
2. **Option (B): Surface-mount on the OUTSIDE of the chassis with a hard clamp.**
    *   *Coupling:* ~0.5–5 mG.
    *   *Practicality:* High. You skip the deep PLA transmission path, but you *still* have the fundamental decoupler: the air gap between the chassis and the rotating tube. Better than embedding, but likely still insufficient for powder fluidization.
3. **Option (C/D): Hard plunger/pin pressed against the bore wall/tube OD.**
    *   *Coupling:* ~0.4–0.8 G at contact point.
    *   *Practicality:* Very Low. If the pin touches the rotating tube OD directly, it acts as a constant mechanical brake, causing wear and loading the stepper. You would have to spring-load the pin to retract during rotation and deploy only when stopped, adding massive mechanical complexity.
4. **Option (A): Keep embedded in PLA (current).**
    *   *Coupling:* <2 mG.
    *   *Practicality:* Functionally dead weight.

**Recommendation:** Go with **Option (E)**. Remove the ERM entirely and let the solenoid tap act as the sole declog mechanism.

### C. Other P0/P1 Issues in v3

**1. Servo Bracket "Both-Sided" Horn Support is Non-Physical (P0)**
The v3 design moves the servo to an external bracket on the +Y face and adds a Ø3.2 bushing socket on the -Y face (60 mm away) for "both-sided support." Standard servo horns (like those on the HD-1810MG) are only ~5–10 mm tall. The horn will not span a 60 mm gap to reach the -Y bushing. Unless you plan to glue a custom Ø3 × 65 mm steel dowel pin to your servo horn, that -Y bushing is useless, and the horn will cantilever in the Ø8 hole exactly as it did before.

**2. E-Bay Lid Heat-Set Flange Blow-out Risk (P1)**
The e-bay lid opening was shrunk to create an 8.5 mm flange, and `ebay_lid_inset = 6.0`. This places the *center* of the Ø4.0 mm hole (for M3 inserts) 6.0 mm from the outer edge, meaning it is 2.5 mm from the inner lid opening edge. Since the hole radius is 2.0 mm, there is only **0.5 mm** of PLA wall between the heat-set hole and the lid opening. The wall will melt and blow out when inserting the brass thread.
*Fix:* Change `ebay_lid_inset = 4.25` to center the hole perfectly in the 8.5 mm flange, yielding a safe 2.25 mm wall on both sides.

**3. Auger Ø5 mm Cantilever Spindle (P1)**
The auger now bridges the gap with a Ø5 × 24 mm PLA spindle to reach the coupler. While safe from torsional shear stress (~3.6 MPa vs. PLA's ~30 MPa strength), it is at severe risk from bending stress if there is any misalignment or grub-screw preload from the metal ST-FC01 coupler. A 20 N transverse load will induce ~39 MPa of bending stress, right at the failure point for Z-axis FDM layer lines.
*Fix:* Increase the spindle and chassis pass-through to Ø7 mm or embed a metal rod down the center of the PLA spindle.
