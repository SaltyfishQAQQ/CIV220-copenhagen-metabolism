"""Copenhagen urban metabolism dashboard (CIV220 assignment companion).

Run locally:   streamlit run app.py
Data:          data.json, produced by build_data.py from the sourced totals.
"""
import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

D = json.loads(Path(__file__).with_name("data.json").read_text())
SRC, ASS, POP = D["sources"], D["assumptions"], D["population"]

ENERGY, WATER, WASTE, AIR = "#eb6834", "#2a78d6", "#1baf7a", "#6250d6"
INK, INK2, MUTED, PLANE, LINE, SURF, GRID = ("#0b0b0b", "#52514e", "#898781", "#f4f3ef",
                                             "#d9d7cf", "#fcfcfb", "#e1e0d9")

st.set_page_config(page_title="Copenhagen urban metabolism", page_icon="🏙️", layout="wide")
st.title("The metabolism of the City of Copenhagen, 2024")


# ====================================================================== helpers
def hbar(labels, values, color, unit, fmt=".1f"):
    """Horizontal bar chart, one hue, direct labels, hover tooltip."""
    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h", marker_color=color,
        text=[f"{v:{fmt}}" for v in values], textposition="outside", cliponaxis=False,
        hovertemplate="%{y}: %{x:" + fmt + "} " + unit + "<extra></extra>"))
    fig.update_layout(
        height=70 + 38 * len(labels), margin=dict(l=10, r=60, t=10, b=30),
        xaxis=dict(title=unit, gridcolor=GRID, zeroline=True, zerolinecolor="#c3c2b7"),
        yaxis=dict(autorange="reversed"), plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)", font=dict(color=INK2), showlegend=False)
    return fig


def rgba(hex_, a):
    h = hex_.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{a})"


def num(x):
    """Three significant figures, thousands separators."""
    ax = abs(x)
    if ax >= 100:
        return f"{x:,.0f}"
    if ax >= 10:
        return f"{x:.1f}"
    if ax >= 1:
        return f"{x:.2f}"
    return f"{x:.3f}" if ax >= 0.01 else f"{x:.4f}"


class Scale:
    """Formats a per-resident value either per resident or for the whole city."""

    def __init__(self, city):
        self.city = city

    def unit_div(self, kind, per_cap_total):
        if not self.city:
            return {"GJ": "GJ / person / yr", "t": "t / person / yr",
                    "co2": "t CO₂e / person / yr"}[kind], 1
        total = per_cap_total * POP
        if kind == "GJ":
            return "PJ / yr", 1e6
        word = " CO₂e" if kind == "co2" else ""
        if total >= 1e6:
            return f"million t{word} / yr", 1e6
        if total >= 1e3:
            return f"thousand t{word} / yr", 1e3
        return f"t{word} / yr", 1

    def fmt(self, x, div, per_cap_fmt):
        return num(x * POP / div) if self.city else format(x, per_cap_fmt)


# ====================================================================== diagram
DIAGRAM_CSS = f"""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<style>
html,body {{margin:0; background:{SURF};}}
.umd {{font-family:Inter, system-ui, sans-serif; color:{INK}; background:{SURF}; padding:4px 6px;}}
.cols {{display:grid; grid-template-columns:minmax(0,1fr) minmax(220px,.8fr) minmax(0,1fr); gap:0 18px;}}
.side-h {{font-size:15px; font-weight:700; letter-spacing:.06em; color:{MUTED}; margin:0 0 10px;}}
.side-h.r {{text-align:right;}}
.grp {{display:grid; gap:14px; align-items:center; margin-bottom:30px; border-radius:10px; padding:4px 6px;
  transition:opacity .15s, background .15s; cursor:default;}}
.in .grp {{grid-template-columns:minmax(0,1fr) 78px;}}
.out .grp {{grid-template-columns:78px minmax(0,1fr);}}
.head {{font-size:13px; font-weight:700; letter-spacing:.03em; margin-bottom:2px;}}
.val {{font-size:34px; font-weight:700; line-height:1.15;}}
.unit {{font-size:13px; color:{INK2}; font-weight:400; margin-left:6px;}}
.row {{display:flex; align-items:center; font-size:13px; color:{INK2}; margin-top:5px; padding:1px 4px;
  border-radius:4px;}}
.row:hover {{background:{PLANE};}}
.sw {{width:11px; height:11px; margin-right:8px; flex:none;}}
.row b {{margin-left:auto; color:{INK}; font-weight:600;}}
.arrow {{height:58px; clip-path:polygon(0 0,72% 0,100% 50%,72% 100%,0 100%); transition:transform .15s;}}
.arrow-d {{width:100%; height:48px; display:block; transition:transform .15s;}}
.city {{background:{PLANE}; border:1.5px solid {LINE}; border-radius:16px; padding:18px 16px; display:flex;
  flex-direction:column; gap:12px; margin-top:28px; height:calc(100% - 28px); box-sizing:border-box;}}
.skyline {{width:100%; height:54px; display:block;}}
.city-name {{text-align:center; font-size:20px; font-weight:700; line-height:1.25; padding:14px 0 18px;
  border-bottom:1px solid {LINE};}}
.loops-h {{text-align:center; font-size:12px; font-weight:700; letter-spacing:.05em; color:{INK2};}}
.loop {{background:{SURF}; border:1px solid {LINE}; border-left-width:6px; border-radius:8px; padding:10px 12px;
  transition:opacity .15s, box-shadow .15s;}}
.loop .t {{font-size:14px; font-weight:700;}}
.loop .s {{font-size:13px; color:{INK2}; margin-top:3px;}}
.ledger {{margin-top:6px; border:1.5px dashed #c3c2b7; border-radius:12px; padding:14px 18px; display:flex;
  flex-wrap:wrap; align-items:center; gap:10px 40px;}}
.ledger .lh {{font-size:13px; font-weight:700; letter-spacing:.04em; margin-right:auto;}}
.ledger .item {{border-radius:8px; padding:2px 6px; transition:opacity .15s, background .15s;}}
.ledger .big {{font-size:22px; font-weight:700;}}
.ledger .sm {{display:block; font-size:13px; color:{INK2}; margin-top:1px;}}
.umd.focus [data-tip] {{opacity:.28;}}
.umd.focus [data-tip].on, .umd.focus [data-tip].on [data-tip] {{opacity:1;}}
.grp.on, .ledger .item.on {{background:{PLANE};}}
.grp.on .arrow, .grp.on .arrow-d {{transform:scale(1.08);}}
.loop.on {{box-shadow:0 2px 10px rgba(0,0,0,.08);}}
#tip {{position:fixed; pointer-events:none; z-index:10; max-width:300px; background:{INK}; color:#fff;
  font:13px/1.45 Inter, system-ui, sans-serif; padding:9px 12px; border-radius:8px; opacity:0;
  transition:opacity .12s; box-shadow:0 4px 14px rgba(0,0,0,.18);}}
#tip b {{font-weight:700;}}
@media (max-width:900px) {{
  .cols {{grid-template-columns:1fr;}}
  .arrow, .arrow-d {{display:none;}}
  .in .grp, .out .grp {{grid-template-columns:1fr;}}
  .side-h.r {{text-align:left;}}
  .city {{height:auto;}}
}}
</style>
"""

DIAGRAM_JS = """
<div id="tip"></div>
<script>
const root = document.querySelector('.umd'), tip = document.getElementById('tip');
document.querySelectorAll('[data-tip]').forEach(el => {
  el.addEventListener('mouseenter', () => {
    root.classList.add('focus'); el.classList.add('on');
    tip.innerHTML = el.dataset.tip; tip.style.opacity = 1;
  });
  el.addEventListener('mousemove', e => {
    const w = tip.offsetWidth, h = tip.offsetHeight;
    let x = e.clientX + 16, y = e.clientY + 16;
    if (x + w > window.innerWidth - 8) x = e.clientX - w - 16;
    if (y + h > window.innerHeight - 8) y = e.clientY - h - 16;
    tip.style.left = x + 'px'; tip.style.top = y + 'px';
  });
  el.addEventListener('mouseleave', () => {
    root.classList.remove('focus'); el.classList.remove('on'); tip.style.opacity = 0;
  });
});
</script>
"""


def svg_img(svg, cls):
    import base64
    return f'<img class="{cls}" src="data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}">'


SKYLINE = svg_img(
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 34 10" preserveAspectRatio="none">'
    f'<polygon fill="{LINE}" points="0,10 0,7 2,7 2,5 4,5 4,7.5 6,7.5 6,4 6.6,4 7.1,0 7.6,4 8.2,4 8.2,6.5 '
    f'10.5,6.5 10.5,5.4 13,5.4 13,7.6 15,7.6 15,4.5 17,2.8 19,4.5 19,7 21.5,7 21.5,5.6 24,5.6 24,7.8 '
    f'26,7.8 26,3.8 27,3.8 27,6.6 29.5,6.6 29.5,5 32,5 32,7.4 34,7.4 34,10"/></svg>', "skyline")
DASHED = svg_img(
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 48"><polygon points="2,4 56,4 77,24 56,44 2,44" '
    f'fill="none" stroke="{WATER}" stroke-width="2.2" stroke-dasharray="6 4"/></svg>', "arrow-d")


def esc(s):
    return s.replace('"', "&quot;")


def build_diagram(sc):
    e, w, g, a = D["energy_GJ_cap"], D["water"], D["ghg_t_cap"], D["air_kg_cap"]
    lp, o, wc = D["loops"], D["off_ledger"], D["waste_t_cap"]
    sorted_ = sorted(((k, v) for k, v in wc.items() if not k.startswith("Residual")), key=lambda kv: -kv[1])
    other = sum(v for _, v in sorted_[3:])

    def rows(items, color, alphas, total, div, pcf, unit):
        out = ""
        for (lab, v), al in zip(items, alphas):
            share = f"{100 * v / total:.0f}% of the total" if v > 0 else "a net removal"
            t = f"<b>{lab}</b><br>{sc.fmt(v, div, pcf)} {unit}<br>{share}"
            out += (f'<div class="row" data-tip="{esc(t)}"><span class="sw" style="background:{rgba(color, al)}">'
                    f'</span>{lab}<b>{sc.fmt(v, div, pcf)}</b></div>')
        return out

    def group(side, head, kind, total, pcf, color, tipt, row_items=(), alphas=(), dashed=False, prefix="", tpcf=None):
        unit, div = sc.unit_div(kind, total)
        arrow = DASHED if dashed else f'<div class="arrow" style="background:{color}"></div>'
        body = rows(row_items, color, alphas, total, div, pcf, unit) if row_items else ""
        text = (f'<div><div class="head">{head}</div><div class="val">{prefix}{sc.fmt(total, div, tpcf or pcf)}'
                f'<span class="unit">{unit}</span></div>{body}</div>')
        inner = text + arrow if side == "in" else arrow + text
        return f'<div class="grp" data-tip="{esc(tipt)}">{inner}</div>'

    inputs = "".join([
        group("in", "ENERGY DELIVERED", "GJ", D["energy_total_GJ_cap"], ".1f", ENERGY,
              "<b>Energy delivered</b><br>Electricity, district heat, fuels and gas used inside the city. "
              "Source: City of Copenhagen CO₂ account 2024.",
              list(e.items()), [1, .82, .64, .46, .3]),
        group("in", "CLEAN WATER", "t", w["total"], ".0f", WATER,
              "<b>Clean water supplied</b><br>Groundwater pumped from well fields outside the city. "
              "Households use 98 L per person per day (HOFOR, 2025).",
              [("Households (98 L per day)", w["household"]), ("Business, institutions, losses", w["other"])],
              [1, .55]),
        group("in", "RAIN AND GROUNDWATER ENTERING SEWERS", "t", D["extraneous_t_cap"], ".0f", WATER,
              "<b>Rain and groundwater (estimate)</b><br>Wastewater treated minus clean water supplied. "
              "It enters the combined sewers and is treated as if it were sewage.", dashed=True, prefix="≈"),
    ])
    au, adiv = sc.unit_div("t", a["NOx"] / 1000)
    air_tip = esc("<b>Other air contaminants, 2021</b><br>Emissions inside the city (Jensen et al., 2024). "
                  "Fine particles are the smallest flow by mass but cause most of the health harm.")
    air = (f'<div class="grp" data-tip="{air_tip}">'
           f'<div></div><div><div class="head">OTHER AIR CONTAMINANTS</div>'
           f'<div style="font-size:15px;font-weight:700;margin-top:2px">'
           f'NOₓ {sc.fmt(a["NOx"] / 1000, adiv, ".4f")}&nbsp;&nbsp; SOₓ {sc.fmt(a["SOx"] / 1000, adiv, ".4f")}'
           f'&nbsp;&nbsp; PM₂.₅ {sc.fmt(a["PM2.5"] / 1000, adiv, ".4f")}</div>'
           f'<div class="unit" style="margin:0">{au}</div></div></div>')
    outputs = "".join([
        group("out", "GREENHOUSE GASES (TERRITORIAL)", "co2", D["ghg_total_t_cap"], ".2f", AIR,
              "<b>Territorial greenhouse gases</b><br>What the city reports. Biomass is counted as zero. "
              "Source: City of Copenhagen CO₂ account 2024.",
              list(g.items()), [1, .8, .6, .42, .25]),
        air,
        group("out", "WASTEWATER TREATED", "t", D["wastewater_t_cap"], ".0f", WATER,
              f"<b>Wastewater treated</b><br>{D['wastewater_t_cap'] / w['total']:.1f} times the clean water "
              "supplied, treated at Lynetten and Damhusåen and discharged to the Øresund."),
        group("out", "RESIDENTIAL SOLID WASTE", "t", D["waste_total_t_cap"], ".3f", WASTE,
              "<b>Residential solid waste</b><br>Household-collected waste in 15 fractions "
              "(City of Copenhagen, 2025b). Excludes recycling-centre drop-offs.",
              [("Residual, incinerated", wc["Residual (incinerated)"])] + sorted_[:3]
              + [("Eleven other sorted fractions", other)], [1, .75, .6, .48, .32], tpcf=".2f"),
    ])
    eu, ediv = sc.unit_div("GJ", 1)
    tu, tdiv = sc.unit_div("t", D["waste_separated_t_cap"])
    eu, tu = eu.split(" / ")[0], tu.split(" / ")[0]
    per = "" if sc.city else " / person"
    loops = [
        (WASTE, "Residual waste to energy", f"↺ returns {sc.fmt(lp['waste_to_energy_GJ_cap'], ediv, '.1f')} {eu}{per}",
         "Household residual waste burned at Amager Bakke, returned as district heat and electricity."),
        (WATER, "Sludge and biogas", f"↺ returns {sc.fmt(lp['wastewater_energy_GJ_cap'], ediv, '.1f')} {eu}{per}",
         "Heat, electricity and biogas recovered from sewage sludge at the BIOFOS treatment plants."),
        (WASTE, "Source separation", f"↺ {sc.fmt(D['waste_separated_t_cap'], tdiv, '.2f')} {tu}{per} recycled",
         "Household waste sorted at the kerb and sent to recycling and biogas: 45% of residential waste."),
    ]
    city = (f'<div class="city">{SKYLINE}<div class="city-name">CITY OF<br>COPENHAGEN</div>'
            f'<div class="loops-h">LOOPS ALREADY CLOSED</div>'
            + "".join(f'<div class="loop" style="border-left-color:{c}" data-tip="{esc(f"<b>{t}</b><br>{tp}")}">'
                      f'<div class="t">{t}</div><div class="s">{s}</div></div>' for c, t, s, tp in loops)
            + "</div>")
    lu, ldiv = sc.unit_div("t", o["wood_chip_eq_t_cap"])
    short = lu.split(" / ")[0]
    ledger_items = [
        (f"≈{sc.fmt(o['wood_chip_eq_t_cap'], ldiv, '.1f')} {short}", "wood burned",
         "<b>Wood burned (estimate)</b><br>Wood-chip equivalent of the biomass burned for the city's heat "
         "and power. The largest solid material the city consumes."),
        (f"≈{sc.fmt(o['biogenic_tCO2_cap'], ldiv, '.1f')} {short.replace('t', 't CO₂', 1)}", "biogenic, uncounted",
         "<b>Biogenic CO₂ (estimate)</b><br>Released by burning that wood, about twice the reported "
         "total, but counted as zero in the official account."),
        (f"{sc.fmt(o['consumption_tCO2e_cap'], ldiv, '.1f')} {short.replace('t', 't CO₂e', 1)}", "consumption footprint",
         "<b>Consumption-based footprint, 2019</b><br>Emissions caused worldwide by residents' consumption "
         "(City of Copenhagen, 2023), about nine times the territorial figure."),
    ]
    ledger = ('<div class="ledger"><span class="lh">OUTSIDE THE OFFICIAL LEDGER</span>'
              + "".join(f'<span class="item" data-tip="{esc(tp)}"><span class="big">{b}</span>'
                        f'<span class="sm">{s}</span></span>' for b, s, tp in ledger_items) + "</div>")
    return (DIAGRAM_CSS + '<div class="umd"><div class="cols">'
            f'<div class="in"><div class="side-h">INPUTS</div>{inputs}</div><div>{city}</div>'
            f'<div class="out"><div class="side-h r">OUTPUTS</div>{outputs}</div></div>{ledger}</div>'
            + DIAGRAM_JS)


# ====================================================================== page
tab1, tab2 = st.tabs(["Metabolism", "Data and sources"])
o = D["off_ledger"]

with tab1:
    view = st.segmented_control("Show flows", ["Per resident", "Whole city"], default="Per resident",
                                label_visibility="collapsed")
    diagram = build_diagram(Scale(view == "Whole city"))
    if hasattr(st, "iframe"):  # Streamlit 1.66 and later
        st.iframe(diagram, height="content")
    else:  # older Streamlit, e.g. on Python 3.10
        import streamlit.components.v1 as components
        components.html(diagram, height=820, scrolling=True)

    st.divider()
    st.subheader("Breakdown by flow")
    left, right = st.columns(2, gap="large")
    with left:
        st.markdown("**Energy delivered, by carrier**")
        e = D["energy_GJ_cap"]
        st.plotly_chart(hbar(list(e), list(e.values()), ENERGY, "GJ / person / yr"), width="stretch")
        st.markdown("**Water entering the system**")
        w = D["water"]
        st.plotly_chart(hbar(
            ["Households", "Business, institutions, losses", "Rain and groundwater (estimate)"],
            [w["household"], w["other"], D["extraneous_t_cap"]], WATER, "t / person / yr", ".0f"),
            width="stretch")
    with right:
        st.markdown("**Territorial greenhouse gases, by source**")
        g = D["ghg_t_cap"]
        st.plotly_chart(hbar(list(g), list(g.values()), AIR, "t CO₂e / person / yr", ".2f"), width="stretch")
        st.markdown("**Residential solid waste, by fraction**")
        ws = dict(sorted(D["waste_t_cap"].items(), key=lambda kv: -kv[1]))
        st.plotly_chart(hbar(list(ws), [v * 1000 for v in ws.values()], WASTE, "kg / person / yr", ".0f"),
                        width="stretch")

# ------------------------------------------------------------------ data
with tab2:
    st.subheader("Per-capita values and where they come from")
    rows = [
        ("Energy delivered", D["energy_total_GJ_cap"], "GJ", "2024", "City of Copenhagen CO₂ account 2024; fuels converted from CO₂ with emission factors"),
        ("Clean water, households", D["water"]["household"], "t", "2025", "HOFOR: 98 L per person per day"),
        ("Clean water, total", D["water"]["total"], "t", "2024", "Household use divided by the national household share of 66 % (DANVA)"),
        ("Wastewater treated", D["wastewater_t_cap"], "t", "2024", "99.2 million m³ at Lynetten and Damhusåen × 67.61 % Copenhagen share (CO₂ account 2024)"),
        ("Residential solid waste", D["waste_total_t_cap"], "t", "2024", "City of Copenhagen household waste fact sheets, 15 kerbside fractions"),
        ("Greenhouse gases, territorial", D["ghg_total_t_cap"], "t CO₂e", "2024", "City of Copenhagen CO₂ account 2024"),
        ("NOₓ", D["air_kg_cap"]["NOx"] / 1000, "t", "2021", "DCE report 605 (Jensen et al. 2024)"),
        ("SOₓ", D["air_kg_cap"]["SOx"] / 1000, "t", "2021", "DCE report 605 (Jensen et al. 2024)"),
        ("PM₂.₅", D["air_kg_cap"]["PM2.5"] / 1000, "t", "2021", "DCE report 605 (Jensen et al. 2024)"),
        ("Wood burned, chip equivalent (estimate)", o["wood_chip_eq_t_cap"], "t", "2024", "HOFOR biomass heat and power in the CO₂ account ÷ 9.3 GJ/t (Danish Energy Agency)"),
        ("Biogenic CO₂ (estimate)", o["biogenic_tCO2_cap"], "t", "2024", "Biomass fuel × 112 kg CO₂/GJ (IPCC 2006)"),
        ("Consumption-based footprint", o["consumption_tCO2e_cap"], "t CO₂e", "2019", "City of Copenhagen, Climate Plan 2035 background note"),
    ]
    st.dataframe(pd.DataFrame(rows, columns=["Flow", "Per person per year", "Unit", "Data year", "Source and method"])
                 .style.format({"Per person per year": "{:.4g}"}), hide_index=True, width="stretch")
    with st.expander("Assumptions"):
        st.json(ASS)
    with st.expander("Sourced totals"):
        st.json(SRC)
