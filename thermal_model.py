"""
Heat Sink Thermal Assessment Model
===================================
Step-by-step thermal resistance network calculation for processor heat sink design.
Based on the Thermal Reference document methodology.

Thermal Resistance Network:
  R_total = R_jc + R_TIM + R_hs
  where R_hs = R_cond + R_conv
"""

import math


def compute_thermal_resistance(params: dict) -> dict:
    """
    Compute the full thermal resistance network and junction temperature.

    Parameters
    ----------
    params : dict
        Dictionary containing all input parameters (see DEFAULT_PARAMS for keys).

    Returns
    -------
    dict
        Dictionary with all intermediate and final results.
    """

    # ── Step 1: Extract inputs ──────────────────────────────────────────
    die_length   = params["die_length_m"]          # m
    die_width    = params["die_width_m"]            # m
    die_area     = die_length * die_width           # m²

    Q            = params["tdp_w"]                  # W

    sink_length  = params["sink_length_m"]          # m
    sink_width   = params["sink_width_m"]           # m
    base_thick   = params["base_thickness_m"]       # m

    n_fins       = params["num_fins"]
    fin_thick    = params["fin_thickness_m"]        # m
    fin_height   = params["fin_height_m"]           # m

    k_al         = params["k_heatsink"]             # W/m·K
    k_tim        = params["k_tim"]                  # W/m·K
    t_tim        = params["tim_thickness_m"]        # m

    k_air        = params["k_air"]                  # W/m·K
    nu           = params["kinematic_viscosity"]     # m²/s
    Pr           = params["prandtl"]
    V            = params["air_velocity"]           # m/s

    T_amb        = params["ambient_temp_c"]         # °C
    R_jc         = params["r_jc"]                   # °C/W

    # ── Step 2: Fin spacing ─────────────────────────────────────────────
    S_f = (sink_width - n_fins * fin_thick) / (n_fins - 1)   # m

    # ── Step 3: Junction-to-Case Resistance (given) ─────────────────────
    # R_jc already provided as input

    # ── Step 4: TIM Resistance ──────────────────────────────────────────
    R_TIM = t_tim / (k_tim * die_area)              # °C/W

    # ── Step 5a: Conduction Resistance through heat-sink base ───────────
    R_cond = base_thick / (k_al * die_area)         # °C/W

    # ── Step 5b: Convection Resistance ──────────────────────────────────
    # Reynolds number (characteristic length = fin spacing)
    Re = V * S_f / nu

    # Nusselt number
    if Re < 2300:
        # Laminar – Sieder-Tate correlation
        Nu = 1.86 * (Re * Pr * 2 * S_f / sink_length) ** (1 / 3)
        flow_regime = "Laminar"
    else:
        # Turbulent – Dittus-Boelter correlation
        Nu = 0.023 * Re ** 0.8 * Pr ** 0.3
        flow_regime = "Turbulent"

    # Convective heat-transfer coefficient
    h_conv = Nu * k_air / (2 * S_f)                # W/m²·K

    # ── Convection area ─────────────────────────────────────────────────
    # Single fin area: both sides + tip
    A_single_fin = 2 * fin_height * sink_length + fin_thick * sink_length   # m²
    A_fins_total = n_fins * A_single_fin                                     # m²

    # Exposed base area between fins
    A_base = (sink_width - n_fins * fin_thick) * sink_length                 # m²

    A_total = A_fins_total + A_base                                          # m²

    # Convection resistance
    R_conv = 1.0 / (h_conv * A_total)              # °C/W

    # ── Step 5c: Total heat-sink resistance ─────────────────────────────
    R_hs = R_cond + R_conv

    # ── Step 6: Total thermal resistance ────────────────────────────────
    R_total = R_jc + R_TIM + R_hs

    # ── Step 7: Junction temperature ────────────────────────────────────
    T_junction = T_amb + Q * R_total

    # ── Assemble results ────────────────────────────────────────────────
    return {
        "inputs": {
            "die_length_m": die_length,
            "die_width_m": die_width,
            "die_area_m2": round(die_area, 7),
            "tdp_w": Q,
            "sink_length_m": sink_length,
            "sink_width_m": sink_width,
            "base_thickness_m": base_thick,
            "num_fins": n_fins,
            "fin_thickness_m": fin_thick,
            "fin_height_m": fin_height,
            "fin_spacing_m": round(S_f, 10),
            "k_heatsink": k_al,
            "k_tim": k_tim,
            "tim_thickness_m": t_tim,
            "k_air": k_air,
            "kinematic_viscosity": nu,
            "prandtl": Pr,
            "air_velocity": V,
            "ambient_temp_c": T_amb,
            "r_jc": R_jc,
        },
        "intermediate": {
            "fin_spacing_m": S_f,
            "reynolds_number": Re,
            "flow_regime": flow_regime,
            "nusselt_number": Nu,
            "h_convection_W_m2K": h_conv,
            "area_single_fin_m2": A_single_fin,
            "area_fins_total_m2": A_fins_total,
            "area_base_m2": A_base,
            "area_total_m2": A_total,
        },
        "resistances": {
            "R_jc": R_jc,
            "R_TIM": R_TIM,
            "R_cond": R_cond,
            "R_conv": R_conv,
            "R_hs": R_hs,
            "R_total": R_total,
        },
        "result": {
            "R_total_degC_per_W": R_total,
            "T_junction_degC": T_junction,
        },
    }


# ── Default parameters matching the reference spreadsheet ──────────────
DEFAULT_PARAMS = {
    # Processor die
    "die_length_m": 0.0525,
    "die_width_m": 0.045,
    # Power
    "tdp_w": 150,
    # Heat sink
    "sink_length_m": 0.09,
    "sink_width_m": 0.116,
    "base_thickness_m": 0.0025,
    "num_fins": 60,
    "fin_thickness_m": 0.0008,
    "fin_height_m": 0.0245,
    # Material – Aluminium 6061-T6
    "k_heatsink": 167,
    # TIM – Thermal grease
    "k_tim": 4,
    "tim_thickness_m": 0.0001,
    # Air properties at 25 °C
    "k_air": 0.0262,
    "kinematic_viscosity": 1.568e-05,
    "prandtl": 0.71,
    "air_velocity": 1,
    # Environment
    "ambient_temp_c": 25,
    # Junction-to-case resistance
    "r_jc": 0.2,
}


def validate_against_excel():
    """Compare model outputs with reference spreadsheet values."""

    results = compute_thermal_resistance(DEFAULT_PARAMS)

    # Expected values from Excel
    excel = {
        "R_jc":       0.2,
        "R_TIM":      0.010582010582010583,
        "R_cond":     0.006336533282641068,
        "Re":         73.50397786233138,
        "Nu":         2.048884469223276,
        "h":          23.287982445039265,
        "A_single":   0.004482,
        "A_fins":     0.26892,
        "A_base":     0.00612,
        "A_total":    0.27504,
        "R_conv":     0.15612493681013329,
        "R_total":    0.37304348067478493,
        "T_junction": 80.95652210121774,
    }

    model = {
        "R_jc":       results["resistances"]["R_jc"],
        "R_TIM":      results["resistances"]["R_TIM"],
        "R_cond":     results["resistances"]["R_cond"],
        "Re":         results["intermediate"]["reynolds_number"],
        "Nu":         results["intermediate"]["nusselt_number"],
        "h":          results["intermediate"]["h_convection_W_m2K"],
        "A_single":   results["intermediate"]["area_single_fin_m2"],
        "A_fins":     results["intermediate"]["area_fins_total_m2"],
        "A_base":     results["intermediate"]["area_base_m2"],
        "A_total":    results["intermediate"]["area_total_m2"],
        "R_conv":     results["resistances"]["R_conv"],
        "R_total":    results["resistances"]["R_total"],
        "T_junction": results["result"]["T_junction_degC"],
    }

    print("=" * 72)
    print("  THERMAL MODEL VALIDATION AGAINST REFERENCE SPREADSHEET")
    print("=" * 72)
    print(f"{'Parameter':<14} {'Model':>20} {'Excel':>20} {'Match':>8}")
    print("-" * 72)

    all_pass = True
    for key in excel:
        m = model[key]
        e = excel[key]
        match = abs(m - e) < 1e-6
        flag = " PASS" if match else " FAIL"
        if not match:
            all_pass = False
        print(f"{key:<14} {m:>20.10f} {e:>20.10f} {flag:>8}")

    print("-" * 72)

    print("\n" + "=" * 72)
    print("  FINAL RESULTS")
    print("=" * 72)
    print(f"  Total Thermal Resistance (R_total) : {results['result']['R_total_degC_per_W']:.6f} °C/W")
    print(f"  Junction Temperature   (T_junction): {results['result']['T_junction_degC']:.6f} °C")
    print(f"  Flow Regime                        : {results['intermediate']['flow_regime']}")
    print("=" * 72)

    if all_pass:
        print("\n  [PASS]  ALL VALUES MATCH THE REFERENCE SPREADSHEET!")
    else:
        print("\n  [FAIL]  SOME VALUES DO NOT MATCH - review the deltas above.")

    return all_pass


if __name__ == "__main__":
    validate_against_excel()
