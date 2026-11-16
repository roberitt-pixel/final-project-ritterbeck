"""Beam Checker: checks if a simply supported beam is safe.

The user enters a beam (length, material, cross-section), adds point and uniform
loads, and the site finds the reactions, the largest bending moment, the largest
bending stress, and a safety factor. If the safety factor is 1 or more, the beam
is SAFE, otherwise it is UNSAFE.

All units are SI: meters (m), newtons (N), newton-meters (N*m), millimeters (mm)
for the cross-section, and megapascals (MPa) for stress.
"""
from drafter import *
from dataclasses import dataclass

set_site_information(
    author="Bobby Ritterbeck",
    description="A beam checker for students: enter a simply supported beam and its "
                "loads, and find out whether the beam is SAFE or UNSAFE.",
    sources=["Google for the engineering mathematics",
             "LLM: see the conversation file in this repository"],
    planning=["Week 10 and Week 11 worksheets are in this repository"],
    links=["https://github.com/roberitt-pixel/final-project-ritterbeck"],
)

set_website_title("Beam Checker")

# Global constants (allowed): approximate yield strengths in MPa
MATERIAL_YIELD_MPA = {"steel": 250.0, "aluminum": 275.0, "wood": 40.0}
MATERIALS = ["steel", "aluminum", "wood"]
LOAD_KINDS = ["point", "uniform"]
STEPS = 1000  # how many spots along the beam we check for the largest moment


@dataclass
class Load:
    """One load on the beam.

    kind: "point" or "uniform"
    magnitude_n: newtons for a point load, newtons per meter for a uniform load
    position_m: where the load is (the start of it, for a uniform load)
    span_m: how long a uniform load is (0.0 for a point load)
    """
    kind: str
    magnitude_n: float
    position_m: float
    span_m: float


@dataclass
class State:
    """Everything the site needs to remember between pages."""
    length_m: float
    material: str
    width_mm: float
    height_mm: float
    loads: list[Load]
    max_moment_nm: float
    max_stress_mpa: float
    safety_factor: float
    verdict: str


def new_state() -> State:
    """Return a fresh State with no beam and no loads."""
    return State(0.0, "steel", 0.0, 0.0, [], 0.0, 0.0, 0.0, "")


# ---------------------------------------------------------------------------
# Helper functions (the math and the input checking)
# ---------------------------------------------------------------------------

def is_number(text: str) -> bool:
    """Return True if text is a non-negative number such as "5" or "2.5"."""
    return text.replace(".", "", 1).isdigit()


def show_value(number: float) -> str:
    """Return number as text for a TextBox, or "" if it is still 0."""
    if number == 0:
        return ""
    return str(number)


def describe_load(load: Load) -> str:
    """Return a one-line description of a load."""
    if load.kind == "point":
        return ("Point load: " + str(load.magnitude_n) + " N at "
                + str(load.position_m) + " m")
    return ("Uniform load: " + str(load.magnitude_n) + " N/m from "
            + str(load.position_m) + " m to "
            + str(round(load.position_m + load.span_m, 3)) + " m")


def total_force_n(load: Load) -> float:
    """Return the total force of one load in newtons."""
    if load.kind == "point":
        return load.magnitude_n
    return load.magnitude_n * load.span_m


def force_position_m(load: Load) -> float:
    """Return where along the beam the load's total force acts."""
    if load.kind == "point":
        return load.position_m
    return load.position_m + load.span_m / 2


def loads_fit(loads: list[Load], length_m: float) -> bool:
    """Return True if every load is on the beam (not past its end)."""
    for load in loads:
        if load.position_m + load.span_m > length_m:
            return False
    return True


def find_reactions(loads: list[Load], length_m: float) -> list[float]:
    """Return [left reaction, right reaction] in newtons.

    Take moments about the left support to get the right reaction,
    then the two reactions must add up to the total load.
    """
    total_force = 0.0
    moment_about_left = 0.0
    for load in loads:
        force = total_force_n(load)
        total_force = total_force + force
        moment_about_left = moment_about_left + force * force_position_m(load)
    right_reaction = moment_about_left / length_m
    left_reaction = total_force - right_reaction
    return [left_reaction, right_reaction]


def moment_from_load(load: Load, x_m: float) -> float:
    """Return the moment (N*m) at x_m caused by one load that is left of x_m."""
    if load.kind == "point":
        if x_m > load.position_m:
            return load.magnitude_n * (x_m - load.position_m)
        return 0.0
    # Uniform load: only the part of it that is left of x_m counts
    covered = x_m - load.position_m
    if covered < 0:
        covered = 0.0
    if covered > load.span_m:
        covered = load.span_m
    arm = x_m - load.position_m - covered / 2
    return load.magnitude_n * covered * arm


def moment_at(loads: list[Load], left_reaction_n: float, x_m: float) -> float:
    """Return the bending moment (N*m) at spot x_m along the beam."""
    moment = left_reaction_n * x_m
    for load in loads:
        moment = moment - moment_from_load(load, x_m)
    return moment


def find_max_moment(loads: list[Load], length_m: float) -> float:
    """Return the largest bending moment (N*m) anywhere on the beam.

    We check STEPS evenly spaced spots, plus the start and end of every load.
    """
    left_reaction = find_reactions(loads, length_m)[0]
    spots = []
    for step in range(STEPS + 1):
        spots.append(length_m * step / STEPS)
    for load in loads:
        spots.append(load.position_m)
        spots.append(load.position_m + load.span_m)
    biggest = 0.0
    for spot in spots:
        moment = abs(moment_at(loads, left_reaction, spot))
        if moment > biggest:
            biggest = moment
    return biggest


def bending_stress_mpa(moment_nm: float, width_mm: float, height_mm: float) -> float:
    """Return the largest bending stress (MPa) in a rectangular cross-section.

    stress = M * c / I, where I = width * height^3 / 12 and c = height / 2.
    The moment is converted from N*m to N*mm so the answer comes out in MPa.
    """
    inertia_mm4 = width_mm * height_mm ** 3 / 12
    c_mm = height_mm / 2
    return moment_nm * 1000 * c_mm / inertia_mm4


def find_safety_factor(material: str, stress_mpa: float) -> float:
    """Return yield strength divided by stress (999.0 if there is no stress)."""
    if stress_mpa == 0:
        return 999.0
    return MATERIAL_YIELD_MPA[material] / stress_mpa


def get_verdict(safety_factor: float) -> str:
    """Return "SAFE" if the safety factor is 1 or more, otherwise "UNSAFE"."""
    if safety_factor >= 1:
        return "SAFE"
    return "UNSAFE"


# ---------------------------------------------------------------------------
# Routes (each route is one page or one button action)
# ---------------------------------------------------------------------------

@route
def index(state: State) -> Page:
    """Home page: explains the site and has a Start button."""
    return Page(state, [
        Header("Beam Checker"),
        "Check whether a simply supported beam is safe under your loads.",
        "You enter the beam, add point or uniform loads, and the site finds the "
        "bending stress and a safety factor.",
        Button("Start", beam_setup)
    ])


@route
def beam_setup(state: State, message: str = "") -> Page:
    """Page with the form for the beam's length, material, and cross-section."""
    return Page(state, [
        Header("Step 1: The Beam"),
        message,
        "Beam length (m):",
        TextBox("length", show_value(state.length_m)),
        "Material:",
        SelectBox("material", MATERIALS, state.material),
        "Cross-section width (mm):",
        TextBox("width", show_value(state.width_mm)),
        "Cross-section height (mm):",
        TextBox("height", show_value(state.height_mm)),
        Button("Save Beam", save_beam)
    ])


@route
def save_beam(state: State, length: str, material: str, width: str, height: str) -> Page:
    """Check the beam form. If it is good, save it and go to the loads page."""
    if not (is_number(length) and is_number(width) and is_number(height)):
        return beam_setup(state, "Length, width, and height must be numbers.")
    length_m = float(length)
    width_mm = float(width)
    height_mm = float(height)
    if length_m <= 0 or width_mm <= 0 or height_mm <= 0:
        return beam_setup(state, "Length, width, and height must be more than 0.")
    if not loads_fit(state.loads, length_m):
        return beam_setup(state, "A load is past the end of this shorter beam. "
                                 "Remove that load first.")
    state.length_m = length_m
    state.material = material
    state.width_mm = width_mm
    state.height_mm = height_mm
    return loads_page(state)


@route
def loads_page(state: State, message: str = "") -> Page:
    """Page that lists the loads on the beam, with Add, Remove, and Check buttons."""
    content = [
        Header("Step 2: The Loads"),
        "Beam: " + str(state.length_m) + " m " + state.material + ", "
        + str(state.width_mm) + " mm wide, " + str(state.height_mm) + " mm tall",
        message,
    ]
    if len(state.loads) == 0:
        content.append("No loads yet. Click Add Load.")
    else:
        spot = 0
        for load in state.loads:
            content.append(str(spot + 1) + ". " + describe_load(load))
            content.append(Button("Remove", remove_load,
                                  arguments=[Argument("load_number", spot)]))
            spot = spot + 1
    content.append(Button("Add Load", add_load))
    content.append(Button("Edit Beam", beam_setup))
    if len(state.loads) > 0:
        content.append(Button("Check Beam", check_beam))
    return Page(state, content)


@route
def add_load(state: State, message: str = "") -> Page:
    """Page with the form for one new load."""
    return Page(state, [
        Header("Add a Load"),
        message,
        "Load type:",
        SelectBox("kind", LOAD_KINDS, "point"),
        "Magnitude (N for a point load, N/m for a uniform load):",
        TextBox("magnitude"),
        "Position along the beam (m), measured from the left end:",
        TextBox("position"),
        "Span (m), only for a uniform load:",
        TextBox("span"),
        Button("Save Load", save_load),
        Button("Cancel", loads_page)
    ])


@route
def save_load(state: State, kind: str, magnitude: str, position: str, span: str) -> Page:
    """Check the load form. If it is good, add the load to the state."""
    if not (is_number(magnitude) and is_number(position)):
        return add_load(state, "Magnitude and position must be numbers.")
    span_m = 0.0
    if kind == "uniform":
        if not is_number(span):
            return add_load(state, "A uniform load needs a span that is a number.")
        span_m = float(span)
        if span_m <= 0:
            return add_load(state, "The span must be more than 0.")
    if float(magnitude) <= 0:
        return add_load(state, "The magnitude must be more than 0.")
    if float(position) + span_m > state.length_m:
        return add_load(state, "That load goes past the end of the beam ("
                        + str(state.length_m) + " m).")
    state.loads.append(Load(kind, float(magnitude), float(position), span_m))
    return loads_page(state)


@route
def remove_load(state: State, load_number: int) -> Page:
    """Remove the load at spot load_number in the list, then show the loads page."""
    state.loads.pop(load_number)
    return loads_page(state)


@route
def check_beam(state: State) -> Page:
    """Do the beam math, save the answers in the state, and show the results."""
    if len(state.loads) == 0:
        return loads_page(state, "Add at least one load first.")
    state.max_moment_nm = find_max_moment(state.loads, state.length_m)
    state.max_stress_mpa = bending_stress_mpa(state.max_moment_nm, state.width_mm,
                                              state.height_mm)
    state.safety_factor = find_safety_factor(state.material, state.max_stress_mpa)
    state.verdict = get_verdict(state.safety_factor)
    return results(state)


@route
def results(state: State) -> Page:
    """Page that shows the reactions, the largest moment and stress, and the verdict."""
    reactions = find_reactions(state.loads, state.length_m)
    content = [
        Header("Results"),
        "Beam: " + str(state.length_m) + " m " + state.material + ", "
        + str(state.width_mm) + " mm x " + str(state.height_mm) + " mm",
        "Loads:",
    ]
    for load in state.loads:
        content.append(describe_load(load))
    content.append("Left support reaction: " + str(round(reactions[0], 2)) + " N")
    content.append("Right support reaction: " + str(round(reactions[1], 2)) + " N")
    content.append("Largest bending moment: " + str(round(state.max_moment_nm, 2))
                   + " N*m")
    content.append("Largest bending stress: " + str(round(state.max_stress_mpa, 2))
                   + " MPa")
    content.append("Yield strength of " + state.material + ": "
                   + str(MATERIAL_YIELD_MPA[state.material]) + " MPa")
    content.append("Safety factor: " + str(round(state.safety_factor, 2)))
    content.append(Header("Verdict: " + state.verdict, 2))
    content.append(Button("Edit Loads", loads_page))
    content.append(Button("Start Over", reset))
    return Page(state, content)


@route
def reset(state: State) -> Page:
    """Clear the beam and the loads, then go back to the home page."""
    state.length_m = 0.0
    state.material = "steel"
    state.width_mm = 0.0
    state.height_mm = 0.0
    state.loads = []
    state.max_moment_nm = 0.0
    state.max_stress_mpa = 0.0
    state.safety_factor = 0.0
    state.verdict = ""
    return index(state)


# Unit tests


def beam_state() -> State:
    """Return a State with a 4 m steel beam, 50 mm wide and 100 mm tall."""
    return State(4.0, "steel", 50.0, 100.0, [], 0.0, 0.0, 0.0, "")


def loaded_state() -> State:
    """Return beam_state() with a 1000 N point load in the middle."""
    state = beam_state()
    state.loads.append(Load("point", 1000.0, 2.0, 0.0))
    return state


# is_number and show_value
assert_equal(is_number("2.5"), True)
assert_equal(is_number("-3"), False)
assert_equal(is_number("abc"), False)
assert_equal(show_value(0.0), "")
assert_equal(show_value(4.0), "4.0")

# Beam math, checked by hand: P = 1000 N in the middle of a 4 m beam
# gives reactions of 500 N each and M = P * L / 4 = 1000 N*m.
assert_equal(find_reactions([Load("point", 1000.0, 2.0, 0.0)], 4.0), [500.0, 500.0])
assert_equal(find_reactions([Load("point", 1000.0, 1.0, 0.0)], 4.0), [750.0, 250.0])
assert_equal(find_reactions([Load("uniform", 500.0, 0.0, 4.0)], 4.0), [1000.0, 1000.0])
assert_equal(round(find_max_moment([Load("point", 1000.0, 2.0, 0.0)], 4.0), 2), 1000.0)
# Uniform 500 N/m over 4 m: M = w * L^2 / 8 = 1000 N*m
assert_equal(round(find_max_moment([Load("uniform", 500.0, 0.0, 4.0)], 4.0), 2), 1000.0)
# Stress: 6 * M / (b * h^2) = 6 * 1,000,000 N*mm / (50 * 100^2) = 12 MPa
assert_equal(round(bending_stress_mpa(1000.0, 50.0, 100.0), 2), 12.0)
assert_equal(round(find_safety_factor("steel", 12.5), 2), 20.0)
assert_equal(find_safety_factor("steel", 0.0), 999.0)
assert_equal(get_verdict(1.0), "SAFE")
assert_equal(get_verdict(0.99), "UNSAFE")
assert_equal(loads_fit([Load("uniform", 10.0, 3.0, 2.0)], 4.0), False)
assert_equal(describe_load(Load("point", 500.0, 2.0, 0.0)), "Point load: 500.0 N at 2.0 m")

# One test (or more) for every route
assert_equal(index(new_state()).state.length_m, 0.0)
assert_equal(beam_setup(new_state()).state.material, "steel")
assert_equal(save_beam(new_state(), "4", "wood", "50", "100").state.material, "wood")
assert_equal(save_beam(new_state(), "abc", "wood", "50", "100").state.material, "steel")
assert_equal(len(loads_page(loaded_state()).state.loads), 1)
assert_equal(add_load(beam_state()).state.length_m, 4.0)
assert_equal(len(save_load(beam_state(), "point", "1000", "2", "").state.loads), 1)
assert_equal(len(save_load(beam_state(), "point", "1000", "9", "").state.loads), 0)
assert_equal(len(remove_load(loaded_state(), 0).state.loads), 0)
assert_equal(check_beam(loaded_state()).state.verdict, "SAFE")
assert_equal(check_beam(beam_state()).state.verdict, "")
assert_equal(results(check_beam(loaded_state()).state).state.verdict, "SAFE")
assert_equal(reset(loaded_state()).state.length_m, 0.0)
# A very thin steel beam with a big load should be UNSAFE
assert_equal(check_beam(State(4.0, "steel", 10.0, 10.0, [Load("point", 5000.0, 2.0, 0.0)],
                              0.0, 0.0, 0.0, "")).state.verdict, "UNSAFE")

start_server(new_state())
