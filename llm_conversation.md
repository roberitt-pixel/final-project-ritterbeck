How does the math work for checking a beam?

It’s a four-step chain: find the forces at the supports, then the bending moment, then the stress, then compare the stress to the material’s strength.

**1\. Reactions (what the supports push back with)**

The beam isn’t moving, so the forces and the turning effects must balance.

* Add up each load’s force × its distance from the left support (a point load acts at its position, and a uniform load acts at its center). Divide by the beam length to get the right support’s reaction.  
* The left reaction is the total load minus the right reaction.

*Example:* 1000 N at the middle of a 4 m beam gives (1000 × 2\) / 4 \= 500 N on the right, so 500 N on the left.

**2\. Bending moment (how hard the load is trying to bend the beam)**

At any spot x along the beam, the moment is the left reaction × x, minus the turning effect of every load to the left of x. The code checks many spots along the beam and keeps the largest value. That’s the critical spot, since the beam is most likely to fail there.

*Example:* at the middle, M \= 500 × 2 \= 1000 N·m.

**3\. Bending stress (how strained the material is)**

The formula is σ \= M·c / I.

* **I** is the cross-section’s resistance to bending. For a rectangle, I \= width × height³ / 12\.  
* **c** is the distance from the center to the top or bottom edge, which is height / 2\. The stress is highest at that edge.

*Example:* for a 50 × 100 mm section, 1000 N·m \= 1,000,000 N·mm, so σ \= 1,000,000 × 50 / 4,166,667 \= 12 MPa. The code converts N·m to N·mm so the answer comes out in MPa.

**4\. Safety factor and verdict**

Safety factor \= the material’s yield strength / the stress. Steel’s yield strength is about 250 MPa, so 250 / 12 ≈ 20.8. If the safety factor is 1 or more, the stress is below the yield strength and the beam is SAFE. Below 1, it’s UNSAFE.

Real engineering designs usually require a margin well above 1, but this app uses 1 as the cutoff, as your worksheet planned.

Without giving me the complete function, what would be the code required for the math of this application?

Here are the pieces, as formulas and key lines instead of full functions. In your code, `P` is a point load’s magnitude and `w` is a uniform load’s N/m.

**1\. Total force of each load, and where it acts**

python

```py
force = P                          # point load
force = w * span                   # uniform load
location = position                # point load
location = position + span / 2     # uniform load (center of the load)
```

**2\. Reactions** (loop over the loads, adding up two running totals)

python

```py
total_force = total_force + force
moment_about_left = moment_about_left + force * location
# after the loop:
right_reaction = moment_about_left / length
left_reaction = total_force - right_reaction
```

**3\. Bending moment at a spot `x` along the beam**

Start with `moment = left_reaction * x`, then subtract each load’s effect, but only the part of the load that is to the left of `x`:

python

```py
# point load at position a:
if x > a:
    moment = moment - P * (x - a)
# uniform load starting at s with length span:
covered = x - s            # then clamp it between 0 and span
moment = moment - w * covered * (x - s - covered / 2)
```

For the uniform load, the clamp means: if `covered < 0`, set it to 0, and if `covered > span`, set it to `span`.

**4\. Largest moment**

Loop over many evenly spaced `x` values from 0 to `length`, such as `x = length * step / 1000`. Compute `abs(moment)` at each one and keep the biggest, using an `if` to update a `biggest` variable.

**5\. Bending stress** (rectangle, width `b` and height `h`, both in mm)

python

```py
inertia = b * h ** 3 / 12
c = h / 2
stress_mpa = moment_nm * 1000 * c / inertia
```

The `* 1000` converts N·m to N·mm so the answer comes out in MPa.

**6\. Safety factor and verdict**

python

```py
safety_factor = yield_strength / stress_mpa
if safety_factor >= 1:
    verdict = "SAFE"
```

Add the `else` branch for “UNSAFE” yourself.

**To check your work:** a 1000 N point load in the middle of a 4 m beam should give reactions of 500 N each, a maximum moment of 1000 N·m, and, for a 50×100 mm cross-section, a stress of 12 MPa.

