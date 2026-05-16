# Edison Scientific design review — powder doser v2

> **Source**: Edison Scientific platform, `ANALYSIS` agent, run via
> `edison-client` Python SDK using the `EDISON_API_KEY` Copilot agent secret.
> Wall time ≈ 519 s, 19 notebook cells.
> **Inputs**: full conversation context from this PR + the CADSmith-generated
> `powder_doser_chassis.py`, the hand-coded `powder_doser_auger.py`, and
> `powder_doser_pauses.json`.
> Companion notebook: [`powder_doser_edison_notebook.ipynb`](powder_doser_edison_notebook.ipynb)
> Run metadata: [`powder_doser_edison_meta.json`](powder_doser_edison_meta.json)

The review is verbatim from Edison; we have not yet acted on any of these
findings. P0 items in particular look like genuine bugs in the current
CADSmith-generated chassis + auger and should drive the next design pass.

---

Based on a rigorous, holistic analysis of the CAD geometry, physics, and electromechanical architecture of the `powder_doser` assembly, there are multiple critical failures that will prevent the design from functioning—or even assembling—as intended. The CAD generation agent conflated several mechanical paradigms (housing vs. rotor, pivoting structures vs. monoliths) and produced geometries that overlap in empty space.

Here is the ranked list of design and workflow issues, separated by severity.

### P0: Fatal Design Errors (Will fail outright on the first print)

**1. Auger Architecture Conflation (No Relative Motion)**
- **Issue:** The `powder_doser_auger.py` fallback models the auger as a Ø25.0 mm rotating tube (outer diameter) containing an internal bore with a helical fin, rather than a solid shaft with external fins. This Ø25.0 mm rotating tube is dropped directly into the Ø25.4 mm stationary chassis bore.
- **Physics Claim Check:** This fundamentally violates the Archimedes screw principle. The fin and its outer boundary wall are fused into a single rotating part. With no relative motion between the helical fin and the "bore wall" it rides against, powder will rotate as a rigid body but will not be metered downward.
- **Fix:** Rewrite the auger script so the part is a central shaft (e.g. Ø6 mm) with external helical fins extending out to a Ø25.0 mm swept diameter, moving powder against the *chassis* bore.

**2. Auger-to-Coupler Spindle Gap**
- **Issue:** The chassis top plate has a Ø22 mm pilot pass-through at Z=300, and the coupler chamber is at Z=274–300. The auger top sits at Z=250. However, the `powder_doser_auger.py` script fails to extrude an M3 spindle (or any structure) above Z=250. 
- **Fix:** There is a 24 mm gap between the top of the auger and the bottom of the coupler. A spindle must be extruded from Z=250 to at least Z=285 to engage the ST-FC01 coupler.

**3. Servo Kinematics Claim is Non-Physical**
- **Issue:** The user claims the servo will "pivot the dispense point to keep the spout stationary." The `powder_doser_chassis.py` script accommodates this by cutting a 6×8 mm horn slot through the +Y pocket directly into the bore.
- **Physics Claim Check:** The chassis is a monolithic FDM block with no hinged parts, flexures, or separate nozzle. The horn will simply plunge through the slot and collide with the rotating auger fin, jamming the system. There is no "dispense point" that can pivot.
- **Fix:** Either split the chassis and add a flexure-hinged lower nozzle section for the servo to drive, or remove the servo feature entirely. 

**4. E-Bay Lid Insert Points Drill Into Empty Space**
- **Issue:** The electronics bay cavity cuts the entire -Y outer wall away (the `ebay_lid_opening` removes the material between Z=53.5 and 126.5, X=-31.5 and 31.5). The four M3 heat-set insert holes meant to secure the lid are placed at X=±31.0 and Z=54.0/126.0, extruded backward 5.5 mm. 
- **Fix:** These holes sit inside the 63 mm-wide opening cutout, meaning they drill entirely into air. Reduce the `ebay_lid_opening_w` width so a flange of wall remains to accept the heat-sets.

**5. Solenoid Pocket Axis Misalignment**
- **Issue:** The JF-0530B push-pull solenoid body is 9.6 × 19 × 22 mm, where 22 mm is the plunger axis. The chassis script carves a pocket `(x=9.8, y=19.2, z=22.2)`. 
- **Fix:** The Z=22.2 dimension forces the solenoid to be mounted vertically. However, the slot meant to connect the plunger to the bore is cut radially along the X-axis. Rotate the solenoid pocket 90° so its 22.2 mm dimension is aligned with X.

**6. Stepper Wire Grommet Disconnection**
- **Issue:** The Ø5 mm grommet is cut 3.5 mm deep into the -Y chassis face at Z=122. However, the e-bay cavity starts at Y=-92.5. 
- **Fix:** There is ~59 mm of solid PLA between the end of the grommet dimple and the bay cavity. The stepper wires cannot pass through. Remodel the wire routing to properly pierce the chassis wall into the e-bay.

---

### P1: Architectural Physics and Reliability Risks

**7. ERM Vibration Coupling through PLA Monolith**
- **Issue:** The ERM is printed and fully encapsulated 19.4 mm away from the bore.
- **Physics Claim Check:** An Adafruit #1201 ERM (0.9 g) produces ~9 mN of excitation force. Encapsulated rigidly in a ~600 g PLA structure, the coupled acceleration at the bore wall will be less than 2 mG (0.002 G), well below the 0.5–2 G required to effectively fluidize powder. 
- **Fix:** The "damping to nothing" concern is highly valid. Redesign the ERM mount to be bonded to a thin wall directly adjacent to the bore or floating in an internal compliant pocket to avoid treating the entire chassis as the inertial mass.

**8. Print-Pause Entombment and Bridging Failure**
- **Issue:** The ERM pocket (Z=125) is a radially-oriented cylinder. Pausing exactly at Z=125 stops the print at the *midpoint* of the cylinder, leaving a U-shaped channel. The flat coin will sit poorly on the curved bottom. Even worse, the upper half of the pocket will demand a 5.15 mm un-supported FDM bridge over the coin upon resume. 
- **Fix:** Change the ERM pocket to a rectangular slot and set the print-pause schedule to `Z=130.15` (top of pocket) so the coin drops in cleanly and the next layer encapsulates it immediately. Furthermore, print-embedding active electronics with no rework path makes the entire ~15-hour FDM print disposable if an ERM lead snaps.

**9. Powder Leakage at Overlapping Bore Breaches**
- **Issue:** Near the dispense end, the servo horn slot breaches the bore at Z=21–29. The solenoid slot breaches the bore at Z=27–33. 
- **Fix:** The bore wall is thus open on both sides simultaneously in the Z=27–29 region. Powder will leak into the servo pocket and the solenoid housing and jam both actuators. 

**10. Solenoid Thermal Limit Exceeded**
- **Issue:** The encapsulated JF-0530B solenoid draws ~5.5W continuously. With no convective cooling in a PLA tomb, a continuous-on fault state will raise the local temperature by hundreds of degrees, softening the PLA (Tg ~ 55–60°C) and destroying the chassis. 
- **Fix:** This is only acceptable if strictly enforced by software duty-cycling (e.g. 1% tap). A thermal fuse is recommended. 

**11. Workflow Failure Mode (CADSmith Helix Collapse)**
- **Issue:** The orchestrator (CADSmith Opus 4.7) failed across 6 iterations to boolean-fuse the helical fin. The fallback `.py` script ships the fin as a separate `cq.Compound`. 
- **Fix:** This warns that generating swept helices in `CadQuery` with `isFrenet=True` combined with OCCT boolean operations is geometrically brittle. If the compound overlaps the main body without a true topological boolean fusion, standard slicers may suffer from Z-fighting or hollow shell errors on the fin mesh. For future workflows, parameterising helices in OpenSCAD or isolating the auger into a separate artifact generation step is a more robust pattern.

---

### P2: Peripheral Adjustments (Nice-to-Haves)

**12. Auger Cantilever Whip:** A 250 mm unsupported PLA auger has a low natural frequency (~22 Hz) and high compliance (2.3 mm deflection at the tip with 0.1 N of lateral force). Whirl onset is mathematically marginal for 1200+ RPM. Although direct stepping (60–300 RPM) is safe, dragging forces will likely induce bore rubbing. Add a lower self-lubricating bushing at Z=15.
**13. Z-Height Restraint:** The assembled vertical CAD requires a Z print height of 300 mm. Most consumer FDMs (Prusa MK4: 220 mm; Bambu X1: 256 mm) cannot print this without splitting the part. 
**14. I2C Bus Clarity:** The Pololu Tic 500 default connects via I2C, but the Adafruit Stepper Bonnet physically occupies the entire Pi GPIO header. The Tic 500 must be routed via a separate USB data cable or the I2C pins must be manually broken out prior to stacking.

***

### Analytical Decisions
- Modeled the chassis structural profile simplistically with a ~40% volumetric void fraction (due to the bore and bay cavity) to bound an order-of-magnitude estimate on ERM transmissibility and chassis natural frequencies.
- Evaluated the thermal dissipation of the solenoid assuming standard still-air convective limits (5 W/m²K) acting against a solid PLA block boundary, validating the need for aggressive duty-cycling.
- Verified physical fit tolerances strictly against provided Cartesian boundaries without anticipating slicer shrink/expansion factors, meaning identified clashes represent absolute mathematical overlapping volumes.
- Excluded the DRV8825 thermal dissipation from analysis, as it is positioned internally inside the bay and categorized as a fallback component by the user schema.