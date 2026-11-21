"""Single source of truth for the Copenhagen urban-metabolism numbers.

Every per-capita value used in the report, the figures and the Streamlit
dashboard is computed here from the sourced totals, then written to data.json.
Run:  python build_data.py
"""
import json
from pathlib import Path

POP = 667_099  # residents, population used in the 2024 CO2 account (CoC 2025a)

# ---------------------------------------------------------------- sourced totals
src = {
    # CoC 2025a - CO2 account 2024
    "electricity_MWh": 2_272_371,
    "rail_electricity_MWh": 102_522,
    "district_heat_MWh": 4_046_000,
    "town_gas_MWh": 123_800,
    "indiv_gas_tCO2": 186, "indiv_gas_EF_kg_MWh": 205,
    "indiv_oil_tCO2": 1_249, "indiv_oil_EF_kg_MWh": 267,
    "road_tCO2": 272_888,
    "rail_total_tCO2": 8_586, "rail_diesel_tCO2": 2_418,
    "air_tCO2": 13_600, "ship_tCO2": 20_791,
    "nonroad_industry_tCO2": 37_507, "nonroad_household_tCO2": 2_957,
    "elec_tCO2": 136_715, "dh_tCO2": 162_259,
    "towngas_tCO2": 9_037, "indiv_heat_tCO2": 1_435, "solvents_tCO2": 11_400,
    "landuse_tCO2": 52, "landfill_tCO2": 750, "wastewater_tCO2": 4_205,
    "forest_tCO2": -13_384, "total_tCO2": 668_797,
    "elec_EF_kg_MWh": 60.2, "dh_EF_kg_MWh": 40.1,
    "hofor_bio_heat_MWh": 2_775_447, "hofor_bio_elec_MWh": 774_399,
    "biofos_heat_MWh": 69_616, "biofos_elec_MWh": 2_599, "biofos_biogas_MWh": 62_102,
    "wastewater_treated_Mm3": 99.2, "cph_wastewater_share": 0.6761,
    "vehicle_km_million": 1_465,
    # CoC 2025b - household waste fact sheets 2024 (tonnes collected at the kerb)
    "waste_t": {
        "Residual (incinerated)": 92_135, "Food waste": 18_128, "Glass": 10_844,
        "Cardboard": 9_549, "Garden waste": 7_712, "Plastic": 7_412,
        "Bulky waste": 5_536, "Paper": 4_870, "Indoor wood": 4_666,
        "Electronics": 2_831, "Metal": 1_870, "Cartons": 815,
        "Hazardous": 528, "Textiles": 427, "Batteries": 78,
    },
    # ARC 2025 - Amager Bakke 2023
    "arc_waste_t": 590_000, "arc_elec_GWh": 283, "arc_heat_GWh": 1_300,
    # HOFOR 2025 / DANVA 2025 - water
    "household_water_L_day": 98, "household_share_of_total": 0.66,
    # Jensen et al. 2024 (DCE 605) - emissions in the municipality, 2021, kg
    "NOx_kg": 1_808_429, "SOx_kg": 88_060, "PM25_kg": 178_409,
    # CoC 2023 - consumption-based footprint 2019
    "consumption_tCO2e_cap": 9.4,
    # Ingenioeren 2025 - mechanically-treated bypass, Damhusaaen 2024
    "bypass_Mm3": 4.28,
}

# ---------------------------------------------------------------- assumptions
ass = {
    "EF_road_kg_GJ": 72.0,      # gasoline 70 / diesel 73 (CIV220 L21), fleet mix
    "EF_diesel_kg_GJ": 73.0,    # CIV220 L21
    "EF_marine_kg_GJ": 74.1,    # IPCC 2006 gas/diesel oil
    "EF_jet_kg_GJ": 71.5,       # IPCC 2006 jet kerosene
    "EF_wood_kg_GJ": 112.0,     # IPCC 2006 wood/wood waste
    "LHV_chips_GJ_t": 9.3,      # Danish Energy Agency standard, 45 % moisture
    "biomass_plant_efficiency": 1.00,  # CHP with flue-gas condensation, LHV basis
    "heat_pump_share_of_DH": 0.18,     # two anchor units (State of Green 2023)
    "heat_pump_COP": 3.0,
    "wastewater_dT_K": 5.0, "cp_water_kJ_kgK": 4.186,
    "stormwater_decoupling": [0.30, 0.40],   # Nielsen 2016
}

GJ = lambda mwh: mwh * 3.6          # MWh -> GJ
cap = lambda x: x / POP

# ---------------------------------------------------------------- energy input
energy_GJ = {
    "District heat": GJ(src["district_heat_MWh"]),
    "Electricity (incl. rail)": GJ(src["electricity_MWh"] + src["rail_electricity_MWh"]),
    "Road fuels": src["road_tCO2"] * 1000 / ass["EF_road_kg_GJ"],
    "Other mobile fuels": (
        (src["nonroad_industry_tCO2"] + src["nonroad_household_tCO2"] + src["rail_diesel_tCO2"])
        * 1000 / ass["EF_diesel_kg_GJ"]
        + src["ship_tCO2"] * 1000 / ass["EF_marine_kg_GJ"]
        + src["air_tCO2"] * 1000 / ass["EF_jet_kg_GJ"]),
    "Town gas and oil": GJ(src["town_gas_MWh"]
                           + src["indiv_gas_tCO2"] * 1000 / src["indiv_gas_EF_kg_MWh"]
                           + src["indiv_oil_tCO2"] * 1000 / src["indiv_oil_EF_kg_MWh"]),
}
energy_cap = {k: cap(v) for k, v in energy_GJ.items()}
energy_total = sum(energy_cap.values())

# ---------------------------------------------------------------- water
water_household = src["household_water_L_day"] * 365 / 1000          # t/cap/yr
water_total = water_household / src["household_share_of_total"]
water_other = water_total - water_household
ww_cph_m3 = src["wastewater_treated_Mm3"] * 1e6 * src["cph_wastewater_share"]
wastewater = cap(ww_cph_m3)
extraneous = wastewater - water_total

# ---------------------------------------------------------------- solid waste
waste_total_t = sum(src["waste_t"].values())
waste_cap = {k: cap(v) for k, v in src["waste_t"].items()}
waste_total = cap(waste_total_t)
waste_residual = waste_cap["Residual (incinerated)"]
waste_separated = waste_total - waste_residual

# ---------------------------------------------------------------- air
transport_t = (src["road_tCO2"] + src["rail_total_tCO2"] + src["air_tCO2"] + src["ship_tCO2"]
               + src["nonroad_industry_tCO2"] + src["nonroad_household_tCO2"])
other_t = (src["towngas_tCO2"] + src["indiv_heat_tCO2"] + src["solvents_tCO2"]
           + src["landuse_tCO2"] + src["landfill_tCO2"] + src["wastewater_tCO2"])
ghg_cap = {
    "Transport": cap(transport_t),
    "District heat": cap(src["dh_tCO2"]),
    "Electricity": cap(src["elec_tCO2"]),
    "Other sources": cap(other_t),
    "Uptake by trees": cap(src["forest_tCO2"]),
}
ghg_total = cap(src["total_tCO2"])
ghg_check = transport_t + other_t + src["dh_tCO2"] + src["elec_tCO2"] + src["forest_tCO2"]
air_kg = {"NOx": cap(src["NOx_kg"]), "SOx": cap(src["SOx_kg"]), "PM2.5": cap(src["PM25_kg"])}

# ---------------------------------------------------------------- loops
arc_GJ_per_t = GJ((src["arc_elec_GWh"] + src["arc_heat_GWh"]) * 1000) / src["arc_waste_t"]
loop_waste_energy = waste_residual * arc_GJ_per_t
loop_ww_energy = cap(GJ(src["biofos_heat_MWh"] + src["biofos_elec_MWh"] + src["biofos_biogas_MWh"]))

# ---------------------------------------------------------------- off-ledger biomass
bio_output_GJ = GJ(src["hofor_bio_heat_MWh"] + src["hofor_bio_elec_MWh"])
bio_fuel_GJ = bio_output_GJ / ass["biomass_plant_efficiency"]
wood_chip_eq = cap(bio_fuel_GJ / ass["LHV_chips_GJ_t"])
biogenic_co2 = cap(bio_fuel_GJ * ass["EF_wood_kg_GJ"] / 1000)


# ---------------------------------------------------------------- recommendations
def rec1(share=ass["heat_pump_share_of_DH"], cop=ass["heat_pump_COP"]):
    heat_MWh = share * src["district_heat_MWh"]
    heat_GJ = GJ(heat_MWh)
    elec_MWh = heat_MWh / cop
    return {
        "share": share, "cop": cop,
        "heat_GWh": heat_MWh / 1000, "heat_GJ_cap": cap(heat_GJ),
        "wood_t": heat_GJ / ass["LHV_chips_GJ_t"],
        "wood_t_cap": cap(heat_GJ / ass["LHV_chips_GJ_t"]),
        "biogenic_tCO2": heat_GJ * ass["EF_wood_kg_GJ"] / 1000,
        "biogenic_tCO2_cap": cap(heat_GJ * ass["EF_wood_kg_GJ"] / 1000),
        "elec_GWh": elec_MWh / 1000,
        "elec_increase_pct": 100 * elec_MWh / src["electricity_MWh"],
        "elec_GJ_cap": cap(GJ(elec_MWh)),
        "imported_energy_cut_GJ_cap": cap(heat_GJ - GJ(elec_MWh)),
        "reported_tCO2_change": elec_MWh * src["elec_EF_kg_MWh"] / 1000,
        "reported_tCO2_cap_change": cap(elec_MWh * src["elec_EF_kg_MWh"] / 1000),
    }


def rec2(decoupling):
    cut = decoupling * extraneous
    return {"decoupling": decoupling, "cut_t_cap": cut,
            "wastewater_after": wastewater - cut,
            "cut_pct": 100 * cut / wastewater,
            "cut_Mm3": cut * POP / 1e6}


r1 = rec1()
r2 = [rec2(d) for d in ass["stormwater_decoupling"]]
ww_heat_potential = wastewater * 1000 * ass["cp_water_kJ_kgK"] * ass["wastewater_dT_K"] / 1e6  # GJ/cap
ww_heat_delivered = ww_heat_potential * ass["heat_pump_COP"] / (ass["heat_pump_COP"] - 1)

data = {
    "population": POP, "year": 2024,
    "sources": src, "assumptions": ass,
    "energy_GJ_cap": energy_cap, "energy_total_GJ_cap": energy_total,
    "water": {"household": water_household, "other": water_other, "total": water_total},
    "wastewater_t_cap": wastewater, "extraneous_t_cap": extraneous,
    "wastewater_cph_Mm3": ww_cph_m3 / 1e6,
    "waste_t_cap": waste_cap, "waste_total_t": waste_total_t,
    "waste_total_t_cap": waste_total, "waste_residual_t_cap": waste_residual,
    "waste_separated_t_cap": waste_separated,
    "ghg_t_cap": ghg_cap, "ghg_total_t_cap": ghg_total, "ghg_sum_check_t": ghg_check,
    "air_kg_cap": air_kg,
    "loops": {"waste_to_energy_GJ_cap": loop_waste_energy, "arc_GJ_per_t": arc_GJ_per_t,
              "wastewater_energy_GJ_cap": loop_ww_energy},
    "off_ledger": {"wood_chip_eq_t_cap": wood_chip_eq, "biogenic_tCO2_cap": biogenic_co2,
                   "bio_fuel_TJ": bio_fuel_GJ / 1000,
                   "consumption_tCO2e_cap": src["consumption_tCO2e_cap"]},
    "rec1": r1, "rec2": r2,
    "wastewater_heat": {"potential_GJ_cap": ww_heat_potential,
                        "delivered_GJ_cap": ww_heat_delivered,
                        "share_of_DH_pct": 100 * ww_heat_delivered / energy_cap["District heat"]},
    "vehicle_km_cap": src["vehicle_km_million"] * 1e6 / POP,
}

if __name__ == "__main__":
    out = Path(__file__).with_name("data.json")
    out.write_text(json.dumps(data, indent=2))
    show = lambda d, n=2: {k: round(v, n) for k, v in d.items()}
    print("ENERGY GJ/cap", show(energy_cap), "total", round(energy_total, 1))
    print("WATER t/cap", show(data["water"], 1), "| wastewater", round(wastewater, 1),
          "| extraneous", round(extraneous, 1), "| CPH Mm3", round(ww_cph_m3 / 1e6, 1))
    print("WASTE t total", waste_total_t, "| t/cap", round(waste_total, 3),
          "residual", round(waste_residual, 3), "separated", round(waste_separated, 3))
    print("GHG t/cap", show(ghg_cap, 3), "total", round(ghg_total, 3), "check t", ghg_check)
    print("AIR kg/cap", show(air_kg, 2))
    print("LOOPS", show(data["loops"], 2))
    print("OFF-LEDGER", show(data["off_ledger"], 2))
    print("REC1", show(r1, 3))
    print("REC2", [show(r, 2) for r in r2])
    print("WW HEAT", show(data["wastewater_heat"], 2), "| vkm/cap", round(data["vehicle_km_cap"]))
