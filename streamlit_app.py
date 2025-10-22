from __future__ import annotations


# streamlit_app.py
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple
import statistics
import math


import streamlit as st
import pandas as pd
import plotly.express as px
import pathlib

APP_TITLE = "SEED — Sustainability Evaluation for Early-stage Decisions"
APP_TAGLINE = "Project-based scoping for new materials & products"

# -------------------------------
# Data & configuration
# -------------------------------

WORKFLOW_STEPS = [
    "1) TRL & actors",
    "2) Scoping & lifecycle",
    "3) Select factors (3 each)",
    "4) Scoring grid",
    "5) Results & plots",
]


TRL_TABLE = [
    {"level": 1, "actors": ["Technology developers", "External scientific experts"],
     "definition": "Basic principles observed"},
    {"level": 2, "actors": ["Technology developers", "External scientific experts"],
     "definition": "Technology concept formulated"},
    {"level": 3, "actors": ["Technology developers", "External scientific experts"],
     "definition": "Experimental proof of concept"},
    {"level": 4, "actors": ["Technology developers", "External scientific experts", "Industry representatives"],
     "definition": "Technology validated in lab"},
    {"level": 5, "actors": ["Technology developers", "External scientific experts", "Industry representatives", "Government agency representatives"],
     "definition": "Technology validated in relevant environment (industrially relevant environment in the case of key enabling technologies)"},
    {"level": 6, "actors": ["N/A"],
     "definition": "Technology demonstrated in relevant environment (industrially relevant environment in the case of key enabling technologies)"},
    {"level": 7, "actors": ["N/A"],
     "definition": "System prototype demonstration in operational environment"},
    {"level": 8, "actors": ["N/A"],
     "definition": "System complete and qualified"},
    {"level": 9, "actors": ["N/A"],
     "definition": "Actual system proven in operational environment (competitive manufacturing in the case of key enabling technologies; or in space)"},
]

ENVIRONMENTAL_FACTORS = [
    {"name": "Climate change", "unit": "kg CO2 eq", "explanation": "Modification of climate affecting global ecosystem.", "selected": True},
    {"name": "Particulate matters", "unit": "disease incidence", "explanation": "PM effects on human health.", "selected": False},
    {"name": "Water use", "unit": "m3 world eq", "explanation": "Consumption & depletion, scarcity-adjusted.", "selected": False},
    {"name": "Resource use, fossils", "unit": "MJ", "explanation": "Depletion of non-renewable energy resources.", "selected": True},
    {"name": "Land Use", "unit": "point", "explanation": "Impact on land degradation & biodiversity.", "selected": True},
    {"name": "Resource use, minerals and metals", "unit": "kg Sb eq", "explanation": "Depletion of mineral resources.", "selected": False},
    {"name": "Ozone depletion", "unit": "kg CFC-11 eq", "explanation": "Impoverishment of protective ozone layer.", "selected": False},
    {"name": "Acidification", "unit": "mol H+ eq", "explanation": "Atmospheric chemicals redeposited in ecosystems.", "selected": False},
    {"name": "Ionizing radiation, effect on human health", "unit": "kBq U235 eq", "explanation": "Effects of radioactivity.", "selected": False},
    {"name": "Photochemical ozone formation, effect on human health", "unit": "kg NMVOC eq", "explanation": "Air quality deterioration (smog).", "selected": False},
    {"name": "Eutrophication, terrestrial", "unit": "mol N eq", "explanation": "Excess enrichment leading to imbalance.", "selected": False},
    {"name": "Eutrophication, marine", "unit": "kg N eq", "explanation": "Excess nutrients leading to dead zones.", "selected": False},
    {"name": "Eutrophication, freshwater", "unit": "kg P eq", "explanation": "Excess nutrients in rivers & lakes.", "selected": False},
]

SOCIAL_FACTORS = [
    {"name": "Health and safety (workers)", "unit": "", "explanation": "Worker health & safety across supply chain.", "selected": True},
    {"name": "Equal opportunities (workers)", "unit": "", "explanation": "Non-discrimination & inclusion.", "selected": False},
    {"name": "Smallholders including farmers (workers)", "unit": "", "explanation": "Impacts on smallholders.", "selected": False},
    {"name": "Access to material resources (local community)", "unit": "", "explanation": "Shared resource access & rights.", "selected": False},
    {"name": "Delocalization and migration (local community)", "unit": "", "explanation": "Community displacement risks.", "selected": False},
    {"name": "Safe and healthy living conditions (local community)", "unit": "", "explanation": "Ambient environmental & safety conditions.", "selected": False},
    {"name": "Respect of indigenous rights (local community)", "unit": "", "explanation": "FPIC & cultural heritage.", "selected": False},
    {"name": "Local employment (local community)", "unit": "", "explanation": "Quality job opportunities locally.", "selected": False},
    {"name": "Public commitment to sustainability issues (society)", "unit": "", "explanation": "Transparency & responsible conduct.", "selected": True},
    {"name": "Contribution to economic development (society)", "unit": "", "explanation": "Shared prosperity enablement.", "selected": False},
    {"name": "Prevention and mitigation of conflicts (society)", "unit": "", "explanation": "Conflict sensitivity & mitigation.", "selected": False},
    {"name": "Technology development (society)", "unit": "", "explanation": "Innovation spillovers & capacity.", "selected": False},
    {"name": "Ethical treatment of animals (society)", "unit": "", "explanation": "Animal welfare standards.", "selected": False},
    {"name": "Poverty alleviation (society)", "unit": "", "explanation": "Inclusive growth & poverty reduction.", "selected": False},
    {"name": "Health and safety (consumers)", "unit": "", "explanation": "Consumer health & safety.", "selected": False},
    {"name": "End of life responsibility (consumers)", "unit": "", "explanation": "Design for circularity & EPR.", "selected": True},
    {"name": "Health issues for children as consumers (children)", "unit": "", "explanation": "Child-specific health risks.", "selected": False},
]

ECONOMIC_FACTORS = [
    {"name": "Complexity of production process", "unit": "", "explanation": "How complex is manufacturing?", "selected": True},
    {"name": "Raw material cost", "unit": "", "explanation": "Cost of feedstocks & inputs.", "selected": True},
    {"name": "Market size", "unit": "", "explanation": "Addressable market potential.", "selected": False},
    {"name": "Cost of final product", "unit": "", "explanation": "Unit economics and price point.", "selected": True},
    {"name": "Scalability of production process", "unit": "", "explanation": "Ease of scale-up to volume.", "selected": False},
    {"name": "Raw material availability", "unit": "", "explanation": "Supply security & constraints.", "selected": False},
    {"name": "Chance on subsidies", "unit": "", "explanation": "Public funding & incentives likelihood.", "selected": False},
]

INTERPRETATION = [
    {"label":"Measurably Worse", "upper":1, "explanation":"Leads to a measurable worsening"},
    {"label":"Possibly Worse", "upper":2, "explanation":"Might lead to a measurable worsening"},
    {"label":"Equal", "upper":3, "explanation":"No measurable change"},
    {"label":"Possibly Better", "upper":4, "explanation":"Might lead to a measurable improvement"},
    {"label":"Measurably Better", "upper":5, "explanation":"Leads to a measurable improvement"},
]


# --- Factor metadata for Step 3 (EF3.1) ---
ENV_FACTOR_META = {
    "Acidification": {
        "indicator": "Accumulated Exceedance (AE)", "category": "ACIDIFICATION",
        "method": "EF3.1", "version": "2017-01.04.000",
        "uuid": "b5c611c6-def3-11e6-bf01-fe55135034f3",
        "explanation": "Atmospheric chemicals redeposited in ecosystems.",
    },
    "Climate change": {
        "indicator": "Radiative forcing as GWP100", "category": "CLIMATE_CHANGE",
        "method": "EF3.1", "version": "2022-01.00.000",
        "uuid": "6209b35f-9447-40b5-b68c-a1099e3674a0",
        "explanation": "Modification of climate affecting global ecosystem.",
    },
    "Ecotoxicity, freshwater": {
        "indicator": "CTUe", "category": "AQUATIC_ECO_TOXICITY",
        "method": "EF3.1", "version": "2022-01.00.000",
        "uuid": "05316e7a-b254-4bea-9cf0-6bf33eb5c630",
        "explanation": "Toxic effects on freshwater organisms.",
    },
    "Eutrophication, marine": {
        "indicator": "Fraction of N to marine", "category": "AQUATIC_EUTROPHICATION",
        "method": "EF3.1", "version": "2017-02.00.010",
        "uuid": "b5c619fa-def3-11e6-bf01-fe55135034f3",
        "explanation": "Excess nutrients leading to dead zones.",
    },
    "Eutrophication, freshwater": {
        "indicator": "Fraction of P to freshwater", "category": "AQUATIC_EUTROPHICATION",
        "method": "EF3.1", "version": "2017-01.00.010",
        "uuid": "b53ec18f-7377-4ad3-86eb-cc3f4f276b2b",
        "explanation": "Excess nutrients in rivers & lakes.", 
    },
    "Eutrophication, terrestrial": {
        "indicator": "Accumulated Exceedance (AE)", "category": "TERRESTRIAL_EUTROPHICATION",
        "method": "EF3.1", "version": "2017-01.02.009",
        "uuid": "b5c614d2-def3-11e6-bf01-fe55135034f3",
        "explanation": "Excess enrichment leading to imbalance.",
    },
    "Ionizing radiation, effect on human health": {
        "indicator": "Human exposure efficiency rel. U235", "category": "IONIZING_RADIATION",
        "method": "EF3.1", "version": "2017-01.00.011",
        "uuid": "b5c632be-def3-11e6-bf01-fe55135034f3",
        "explanation": "Effects of radioactivity.",
    },
    "Land Use": {
        "indicator": "Soil quality index", "category": "LAND_USE",
        "method": "EF3.1", "version": "2017-01.00.010",
        "uuid": "b2ad6890-c78d-11e6-9d9d-cec0c932ce01",
        "explanation": "Impact on land degradation & biodiversity.",
    },
    "Ozone depletion": {
        "indicator": "ODP", "category": "OZONE_DEPLETION",
        "method": "EF3.1", "version": "2017-02.00.012 (until 2040)",
        "uuid": "b5c629d6-def3-11e6-bf01-fe55135034f3",
        "explanation": "Impoverishment of protective ozone layer.",
    },
    "Particulate matters": {
        "indicator": "Impact on human health", "category": "RESPIRATORY_INORGANICS",
        "method": "EF3.1", "version": "2017-02.00.011",
        "uuid": "b5c602c6-def3-11e6-bf01-fe55135034f3",
        "explanation": "PM effects on human health.", 
    },
    "Photochemical ozone formation, effect on human health": {
        "indicator": "Tropospheric ozone conc. increase", "category": "PHOTOCHEMICAL_OZONE_CREATION",
        "method": "EF3.1", "version": "2017-02.01.000",
        "uuid": "b5c610fe-def3-11e6-bf01-fe55135034f3",
        "explanation": "Air quality deterioration (smog).",
    },
    "Resource use, fossils": {
        "indicator": "ADP-fossil", "category": "ABIOTIC_RESOURCE_DEPLETION",
        "method": "EF3.1", "version": "2017-01.00.010",
        "uuid": "b2ad6110-c78d-11e6-9d9d-cec0c932ce01",
        "explanation": "Depletion of non-renewable energy resources.",
    },
    "Resource use, minerals and metals": {
        "indicator": "ADP ultimate reserve", "category": "ABIOTIC_RESOURCE_DEPLETION",
        "method": "EF3.1", "version": "2017-01.00.010",
        "uuid": "b2ad6494-c78d-11e6-9d9d-cec0c932ce01",
        "explanation": "Depletion of mineral resources.",
    },
    "Water use": {
        "indicator": "Deprivation-weighted water consumption", "category": "OTHER",
        "method": "EF3.1", "version": "2017-03.00.014",
        "uuid": "b2ad66ce-c78d-11e6-9d9d-cec0c932ce01",
        "explanation": "Consumption & depletion, scarcity-adjusted.",
    },
}

# Social & Economic text used in fold-outs
SOCIAL_FACTOR_META = {
    "Health and safety (workers)": "Ensures safe working conditions; avoids long-term health risks (OSH).",
    "Equal opportunities (workers)": "Fair access to employment, advancement, benefits.",
    "Smallholders including farmers (workers)": "Fair integration and economic benefit of small-scale producers.",
    "Access to material resources (local community)": "Effect on access to land, water, essential resources.",
    "Delocalization and migration (local community)": "Risk of displacement/forced migration due to operations.",
    "Safe and healthy living conditions (local community)": "Air, water, noise, safety around sites.",
    "Respect of indigenous rights (local community)": "FPIC, land rights, cultural heritage.",
    "Local employment (local community)": "Creation of fair, stable local jobs and suppliers.",
    "Public commitment to sustainability issues (society)": "Transparency, responsible communication & initiatives.",
    "Contribution to economic development (society)": "Broader growth and infrastructure benefits.",
    "Prevention and mitigation of conflicts (society)": "Conflict sensitivity and mitigation.",
    "Technology development (society)": "Innovation spillovers, capacity building.",
    "Ethical treatment of animals (society)": "Animal welfare in sourcing/testing.",
    "Poverty alleviation (society)": "Contribution to reducing poverty.",
    "Health and safety (consumers)": "Product safety for end users, compliance.",
    "End of life responsibility (consumers)": "Design for circularity; take-back support.",
    "Health issues for children as consumers (children)": "Child-specific exposure risks.",
}

ECON_FACTOR_META = {
    "Complexity of production process": "Technical/operational difficulty; impacts cost and scale.",
    "Raw material cost": "Current prices and stability of inputs.",
    "Market size": "Total addressable demand and growth potential.",
    "Cost of final product": "Price vs. cost; affordability; competitiveness.",
    "Scalability of production process": "Ease of ramping volume without heavy capex.",
    "Raw material availability": "Abundance, geography, supply risk.",
    "Chance on subsidies": "Likelihood of public funding/incentives.",
}

# -------------------------------
# Data model
# -------------------------------
@dataclass
class FactorScore:
    score: Optional[float] = None   # None = “I don’t know”
    note: str = ""

@dataclass
class Project:
    name: str
    description: str = ""
    trl: int = 4
    scoping_notes: str = ""
    lifecycle_stages: List[str] = field(default_factory=list)  # start empty; you manage via UI
    lifecycle_changed: Dict[str, bool] = field(default_factory=dict)
    selected_factors: Dict[str, List[str]] = field(default_factory=dict)  # keys: Environmental/Social/Economic
    grid: Dict[str, Dict[str, FactorScore]] = field(default_factory=dict)  # stage -> factor -> FactorScore
    core_function: str = ""
    functional_unit: str = ""

    # --- restore this! ---
    def ensure_grid(self, all_factors: List[str]) -> None:
        """Make sure every (stage, factor) exists in the grid with a FactorScore."""
        for stage in self.lifecycle_stages:
            stage_map = self.grid.setdefault(stage, {})
            # keep only relevant factors for this stage (optional: clean stale)
            for f in all_factors:
                if f not in stage_map:
                    stage_map[f] = FactorScore()
            # optionally drop factors no longer selected:
            for f in list(stage_map.keys()):
                if f not in all_factors:
                    del stage_map[f]

    def average_by_stage(self) -> Dict[str, float]:
        out: Dict[str, float] = {}
        for stage, facs in self.grid.items():
            vals = [fs.score for fs in facs.values() if getattr(fs, "score", None) is not None] if facs else []
            out[stage] = statistics.mean(vals) if vals else float("nan")
        return out

    def average_by_factor(self) -> Dict[str, float]:
        acc: Dict[str, List[float]] = {}
        for facs in self.grid.values():
            for f, fs in facs.items():
                if getattr(fs, "score", None) is not None:
                    acc.setdefault(f, []).append(fs.score)
        return {f: statistics.mean(v) for f, v in acc.items()} if acc else {}

    def overall_score(self) -> Optional[float]:
        avs = self.average_by_stage()
        vals = [v for v in avs.values() if isinstance(v, (int, float)) and not math.isnan(v)]
        return round(statistics.mean(vals), 2) if vals else None

    # keep this to fix imports
    def coerce_grid(self) -> None:
        """Turn nested dicts (from JSON) back into FactorScore instances."""
        for stage, fdict in self.grid.items():
            for fname, fs in list(fdict.items()):
                if isinstance(fs, dict):
                    self.grid[stage][fname] = FactorScore(**fs)

# -------------------------------
# Helpers
# -------------------------------

# --- Landing page renderer ---
import plotly.express as px
import pandas as pd
import random
import re

def _new_project_name(base="New SEED Project"):
    # create a unique default project name if the user clicks the CTA
    existing = set(st.session_state.get("projects", {}).keys())
    if base not in existing:
        return base
    i = 2
    while f"{base} {i}" in existing:
        i += 1
    return f"{base} {i}"

def _design_paradox_fig():
    # Simple illustration of the sustainable design paradox:
    # knowledge ↑ over time, design freedom ↓ over time.
    x = list(range(0, 101, 5))
    knowledge = [1 + 99*(t/100)**1.6 for t in x]      # rising curve
    freedom   = [100 - 90*(t/100)**0.7 for t in x]    # falling curve
    df = pd.DataFrame({
        "Development progress (%)": x,
        "Knowledge about impacts": knowledge,
        "Design freedom": freedom
    })
    fig = px.line(
        df,
        x="Development progress (%)",
        y=["Knowledge about impacts", "Design freedom"],
        markers=True
    )
    fig.add_vrect(x0=0, x1=25, fillcolor="LightGreen", opacity=0.25, line_width=0,
                  annotation_text="Early stage leverage", annotation_position="top left")
    fig.update_layout(
        margin=dict(t=10, r=10, b=10, l=10),
        legend_title="",
        yaxis_title="Relative level",
    )
    return fig

def render_landing():
    # light CSS for badges/cards
    st.markdown("""
    <style>
      .pill {display:inline-block;padding:.25rem .6rem;margin-right:.4rem;margin-bottom:.4rem;
             border-radius:999px;font-weight:600;font-size:.80rem;border:1px solid #e2e8f0;background:#fff;}
      .card {border:1px solid #e2e8f0;border-radius:14px;padding:14px;background:#fff;}
      .muted{color:#667085}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='hero'>", unsafe_allow_html=True)
    st.markdown(
        "<div class='muted'>A qualitative, actor-driven scoping tool for low-TRL projects — "
        "to reason about sustainability trade-offs before a full LCA is feasible.</div>",
        unsafe_allow_html=True,
    )

    # Pills
    st.markdown(
        "<div class='pill'>Low TRL focus</div>"
        "<div class='pill'>Qualitative assessment</div>"
        "<div class='pill'>Trade-offs & hot-spots</div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    c1, c2 = st.columns([3, 2], gap="large")

    with c1:
        st.markdown("#### What this helps you do")
        st.markdown(
            "- **Engage the right actors early** (Step 1) and **co-scope** function & system boundaries (Step 2).\n"
            "- **Select key factors** across Environmental, Social, Economic (Step 3) — with definitions.\n"
            "- **Score transparently** across life-cycle stages (Step 4) and **surface hot-spots** instantly (Step 5).\n"
            "- Use results to **justify claims** in proposals when a full **LCA is premature**."
        )
        st.markdown("#### Interpreting results")
        st.markdown(
            "- Sustainability is a **balance**: improvements in one factor may worsen another.\n"
            "- Plots are **centered at a baseline of 3 (Equal)**, so left = worse, right = better.\n"
            "- We highlight **worst-performing stages** early so you can iterate design choices."
        )
        st.markdown("#### Scope & limits")
        st.markdown(
            "- Qualitative, early-stage scoping — **not** a substitute for LCA/S-LCA.\n"
            "- Best for **TRL 1–5** where uncertainty is high but design freedom remains."
        )

    with c2:
        st.markdown("#### Sustainable design paradox")
        st.caption("We know most about impacts when it’s hardest to change the design — act early.")
        st.plotly_chart(_design_paradox_fig(), use_container_width=True)

    # Three mini cards
    st.markdown("#### How it works")
    st.caption("Take your time to go through the tool to understand the stages before gathering your stakeholders. Use the example file on windmill blades to go through the tool.")
    # Example file download (unchanged)
    example_path = pathlib.Path("recyclable_windmill_blades.json")
    if example_path.exists():
        with open(example_path, "rb") as f:
            st.download_button(
                "📥 Download example project: Recyclable windmill blades",
                data=f.read(),
                file_name="recyclable_windmill_blades.json",
                mime="application/json",
            )
    else:
        st.info("Place `recyclable_windmill_blades.json` in the app folder to enable the example project download.")

    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        st.markdown("##### 1) TRL & actors")
        st.info("Identify TRL and **who to involve** (devs, experts, industry, etc.).")
    with cc2:
        st.markdown("##### 2) Scoping & lifecycle")
        st.info("Define **core function** and **functional unit**; map a **lean lifecycle**.")
    with cc3:
        st.markdown("##### 3–5) Factors → Scores → Hot-spots")
        st.info("Pick 3 factors per pillar, score 1–5 vs baseline, and review **worst stages**.")

    st.markdown("---")
    cta1, cta2 = st.columns([1, 3])

    # ➕ Create new
    with cta1:
        st.subheader("Start a new project")
        name = st.text_input("Project name", value="New SEED Project") 
        desc = st.text_area("Short description", value="")
        if st.button("➕ Start a new SEED project", use_container_width=True, type="primary"):
            name = _new_project_name()
            st.session_state.projects[name] = Project(name=name, description="")
            st.session_state.active_project = name
            st.session_state.step_idx = 0
            st.success(f"Created project “{name}”.")
            st.rerun()

    # 📥 Import OR open existing
    with cta2:
        st.subheader("Start from an existing file")
        uploaded = st.file_uploader(
            "Import project JSON",
            type=["json"],
            help="Upload a project previously exported from this app.",
        )
        if uploaded is not None:
            try:
                data = json.load(uploaded)
                proj = Project(**data)
                proj.coerce_grid()
                st.session_state.projects[proj.name] = proj
                st.session_state.active_project = proj.name
                st.session_state.step_idx = 0
                st.success(f"Imported project “{proj.name}”.")
                st.rerun()
            except Exception as e:
                st.error(f"Could not import: {e}")

        # Optional: open an already-saved local project from this session
        existing = list(st.session_state.projects.keys())
        if existing:
            st.markdown("Or open a project you created earlier in this session:")
            sel = st.selectbox("Open project", options=["<Select>"] + existing, index=0)
            if sel != "<Select>":
                st.session_state.active_project = sel
                st.session_state.step_idx = 0
                st.rerun()

def bottom_nav(total_steps=len(WORKFLOW_STEPS)):
    st.markdown("---")
    c1, c2, c3 = st.columns([1, 6, 1])
    left_disabled  = st.session_state.step_idx <= 0
    right_disabled = st.session_state.step_idx >= total_steps - 1

    with c1:
        if st.button("⬅️ Back", use_container_width=True, disabled=left_disabled):
            if st.session_state.step_idx > 0:
                st.session_state.step_idx -= 1
                st.rerun()

    with c3:
        if st.button("Next ➡️", use_container_width=True, disabled=right_disabled):
            if st.session_state.step_idx < total_steps - 1:
                st.session_state.step_idx += 1
                st.rerun()

    
def factor_breakdown_plot(stage_name: str, breakdown: Dict[str, FactorScore]):
    # dict -> DataFrame
    df = pd.DataFrame(
        {"Factor": list(breakdown.keys()),
         "Average score": [float(breakdown[f].score) for f in breakdown.keys()]}
    )
    plot_df = to_plot_df(df, "Factor", "Average score").rename(columns={"Factor": "Category"})
    title = f"Factor breakdown — {stage_name}"
    return horizontal_delta_bar(plot_df, title)

def factor_names(factors):
    return [f["name"] for f in factors]

def score_band_color(score: float) -> str:
    if score > 3.5:
        return "#2e7d32"  # green
    if score < 2.5:
        return "#c62828"  # red
    return "#f57c00"      # orange

def to_plot_df(df: pd.DataFrame, cat_col: str, val_col: str) -> pd.DataFrame:
    out = df.copy()
    out["Score"] = out[val_col].astype(float)
    out["Delta"] = out["Score"] - 3.0
    out["Color"] = out["Score"].apply(score_band_color)
    # label shown at bar end (original score, not delta)
    out["Label"] = out["Score"].round(1)
    return out

def horizontal_delta_bar(plot_df: pd.DataFrame, title: str):
    fig = px.bar(
        plot_df.sort_values("Delta"),         # sorts so leftmost (worse) on top for readability
        x="Delta",
        y="Category",
        text="Label",
        color="Color",
        orientation="h",
        color_discrete_map="identity",
    )
    # Axis: show original score ticks (1..5) mapped onto delta (-2..2)
    fig.update_xaxes(
        range=[-2, 2],
        tickmode="array",
        tickvals=[-2, -1, 0, 1, 2],
        ticktext=["1", "2", "3", "4", "5"],
        title="Score (baseline = 3)"
    )
    fig.update_yaxes(title="")
    # Styling
    fig.update_traces(
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Score: %{customdata[0]:.2f}<extra></extra>",
        customdata=plot_df[["Score"]].values,
        marker_line_color="rgba(0,0,0,0.15)",
        marker_line_width=1,
    )
    # Baseline at 0 (i.e., score 3)
    fig.add_vline(x=0, line_dash="dash", line_color="#666", opacity=0.7)
    fig.add_annotation(
        x=0, y=1.02, xref="x", yref="paper",
        text="Baseline (= 3)",
        showarrow=False, font=dict(size=11, color="#666")
    )
    fig.update_layout(
        title=title,
        margin=dict(t=30, r=10, b=20, l=10),
        legend=dict(title="", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig

def get_selected_factors(factors, override_selected: Optional[List[str]] = None) -> List[str]:
    if override_selected is not None:
        return override_selected
    return [f["name"] for f in factors if f.get("selected")]

def interp_label(value: float) -> str:
    for row in INTERPRETATION:
        if value <= row["upper"] + 1e-9:
            return row["label"]
    return "n/a"

def download_json_button(obj, filename, label):
    st.download_button(
        label=label,
        data=json.dumps(obj, indent=2),
        file_name=filename,
        mime="application/json"
    )

# -------------------------------
# State init
# -------------------------------
if "projects" not in st.session_state:
    st.session_state.projects: Dict[str, Project] = {}
if "active_project" not in st.session_state:
    st.session_state.active_project: Optional[str] = None

# -------------------------------
# Sidebar: Project management
# -------------------------------
with st.sidebar:
    st.title("🧭 Process")

    ap_key = st.session_state.get("active_project")
    ap = st.session_state.projects.get(ap_key) if ap_key else None

    if ap:
        step = st.radio(
            "Navigate steps",
            options=WORKFLOW_STEPS,
            index=st.session_state.step_idx,
            key="workflow_radio",
        )
        st.session_state.step_idx = WORKFLOW_STEPS.index(step)

        st.markdown("---")
        st.caption("Active project")
        st.write(f"**{ap.name}**")  # <- guaranteed to be the Project.name
        if ap.description:
            st.caption(ap.description)

        download_json_button(asdict(ap), f"{ap.name.replace(' ','_')}.json", "💾 Export active project")
        st.markdown("---")
    else:
        st.info("Create or import a project on the landing page to begin.")



# -------------------------------
# Header & guard
# -------------------------------
st.set_page_config(page_title="SEED", page_icon="🌱", layout="wide")
st.title(f"🌿 {APP_TITLE}")
st.caption(APP_TAGLINE)

if st.session_state.active_project is None:
    render_landing()
    st.stop()


project: Project = st.session_state.projects[st.session_state.active_project]

# ---------- Canonical subtitles + detailed stage labels ----------
CANONICAL_SECTIONS = [
    "Product (A0–A3)",
    "Construction (A4–A5)",
    "Use (B1–B5)",
    "End of Life (C1–C4, D)",
]

# Make SECTION_TITLES exactly match the canonical order (prevents KeyError)
SECTION_TITLES = CANONICAL_SECTIONS

# --- NEW: sections (per-session lists of stages under each subtitle) ---
if "sections" not in st.session_state:
    st.session_state.sections = {title: [] for title in SECTION_TITLES}

# ✅ Compute scoping status on every run from the active project
def scoping_is_done(p: Project) -> bool:
    return bool(getattr(p, "functional_unit", "").strip()) and len(p.lifecycle_stages) > 0

st.session_state.scoping_done = scoping_is_done(project)






# -------------------------------
# Step 1: TRL
# -------------------------------
if step.startswith("1"):
    st.subheader("Step 1 — TRL & recommended actors")
    project.trl = st.select_slider("Select your TRL level", options=[r["level"] for r in TRL_TABLE], value=project.trl)
    row = next(r for r in TRL_TABLE if r["level"] == project.trl)

    cols = st.columns([2,2])
    with cols[0]:
        st.metric("Selected TRL", project.trl)
        st.write("**EU definition**")
        st.info(row["definition"])
    with cols[1]:
        st.write("**Actors to engage**")
        st.success(", ".join(row["actors"]))

    st.text_area("Notes on stakeholders / initial assumptions", key="trl_notes", value=project.scoping_notes, on_change=lambda: None)
    # update back when leaving step 1
    project.scoping_notes = st.session_state.get("trl_notes", project.scoping_notes)
    bottom_nav()

# -------------------------------
# Step 2: Scoping & lifecycle
# -------------------------------

elif step.startswith("2"):
    st.subheader("Step 2 — Scoping and lifecycle")
    st.write("The subtitles below are **not** stages. Add the **actual stages** under the relevant subtitle. Max total 7 stages.")

    # ---------- Robust init for sections store ----------
    if "sections" not in st.session_state or not isinstance(st.session_state.sections, dict):
        st.session_state.sections = {t: [] for t in SECTION_TITLES}
    # ensure every subtitle exists and is a list
    for _t in SECTION_TITLES:
        if not isinstance(st.session_state.sections.get(_t), list):
            st.session_state.sections[_t] = []
    sections = st.session_state.sections  # shorthand

    # ---------- Canonical subtitles + detailed stage labels ----------
    CANONICAL_SECTIONS = [
        "Product (A0–A3)",
        "Construction (A4–A5)",
        "Use (B1–B5)",
        "End of Life (C1–C4, D)",
    ]

    # Make SECTION_TITLES exactly match the canonical order (prevents KeyError)
    SECTION_TITLES = CANONICAL_SECTIONS

    # Detailed labels from your document
    CODE_TO_LABEL = {
        "A0": "A0 - Pre-construction (design & non-physical activities) [UK]",
        "A1": "A1 - Raw Material Supply",
        "A2": "A2 - Transport to Manufacturer",
        "A3": "A3 - Manufacturing",
        "A4": "A4 - Transport to Site",
        "A5": "A5 - Installation on Site",
        "B1": "B1 - Use/Application",
        "B2": "B2 - Maintenance",
        "B3": "B3 - Repair",
        "B4": "B4 - Replacement",
        "B5": "B5 - Refurbishment",
        # Not seeded by default, but defined for future toggles/migrations if needed:
        "B6": "B6 - Operational Energy Use",
        "B7": "B7 - Operational Water Use",
        "B8": "B8 - Operational Transport (NS3720/PAS2080/EN-17472)",
        "B9": "B9 - User Utilisation (PAS2080)",
        "C1": "C1 - Deconstruction/Demolition",
        "C2": "C2 - Transport to Waste Processing",
        "C3": "C3 - Waste Processing for Reuse/Recovery/Recycling",
        "C4": "C4 - Disposal",
        "D":  "D - Reuse/Recovery/Recycling Potentials (beyond boundary)",
    }

    

    # Bucketing helper based on stage code
    def _bucket_for_code(code: str) -> str:
        code = code.upper().strip()
        if code in ("A0","A1","A2","A3"):
            return CANONICAL_SECTIONS[0]  # Product
        if code in ("A4","A5"):
            return CANONICAL_SECTIONS[1]  # Construction
        if code in ("B1","B2","B3","B4","B5"):
            return CANONICAL_SECTIONS[2]  # Use
        if code in ("C1","C2","C3","C4","D"):
            return CANONICAL_SECTIONS[3]  # End of Life
        return CANONICAL_SECTIONS[0]

    # Extract a stage code from any string like "A1", "A1 - ...", etc.
    import re
    def _code_from_name(name: str) -> str | None:
        m = re.match(r"^\s*([ABCD]\d?)\b", str(name).upper())
        return m.group(1) if m else None
    
    # ---------- Preload sections from the active project's lifecycle_stages (on import) ----------
    def _changed_flag_from_project(label: str) -> bool:
        # prefer exact label, else match by stage code
        code = _code_from_name(label)
        if label in project.lifecycle_changed:
            return bool(project.lifecycle_changed[label])
        for k, v in project.lifecycle_changed.items():
            if _code_from_name(k) == code:
                return bool(v)
        return False

    def _canonical_label(name: str) -> str:
        code = _code_from_name(name)
        return CODE_TO_LABEL.get(code, name)

    # If buckets are empty but project already has stages, preload them
    if all(len(v) == 0 for v in sections.values()) and getattr(project, "lifecycle_stages", []):
        for stage in project.lifecycle_stages:
            label = _canonical_label(stage)
            bucket = _bucket_for_code(_code_from_name(stage))
            if label not in sections[bucket]:
                sections[bucket].append(label)
            project.lifecycle_changed[label] = _changed_flag_from_project(stage)

    # Else (truly new project), seed defaults once
    elif (
        not st.session_state.get("seeded_canon_labels", False)
        and not project.lifecycle_stages
        and all(len(v) == 0 for v in sections.values())
    ):
        DEFAULT_PRODUCT = ["A1","A2","A3"]
        DEFAULT_CONSTR  = ["A4","A5"]
        DEFAULT_USE     = ["B1","B2","B3","B4","B5"]
        DEFAULT_EOL     = ["C1","C2","C3","C4"]

        def _add_unique(bucket: str, code: str):
            label = CODE_TO_LABEL.get(code, code)
            if label not in sections[bucket]:
                sections[bucket].append(label)
            project.lifecycle_changed[label] = False

        for c in DEFAULT_PRODUCT:  _add_unique(CANONICAL_SECTIONS[0], c)
        for c in DEFAULT_CONSTR:   _add_unique(CANONICAL_SECTIONS[1], c)
        for c in DEFAULT_USE:      _add_unique(CANONICAL_SECTIONS[2], c)
        for c in DEFAULT_EOL:      _add_unique(CANONICAL_SECTIONS[3], c)
        st.session_state.seeded_canon_labels = True
    

    # If current session sections don’t match canonical titles, migrate everything
    if set(st.session_state.sections.keys()) != set(CANONICAL_SECTIONS):
        new_sections = {t: [] for t in CANONICAL_SECTIONS}
        for _, lst in st.session_state.sections.items():
            for s in (lst or []):
                code = _code_from_name(s) or s.strip().upper()
                bucket = _bucket_for_code(code)
                label = CODE_TO_LABEL.get(code, s)
                if label not in new_sections[bucket]:
                    new_sections[bucket].append(label)
                # Default all migrated to not "will change" unless already set
                if label not in project.lifecycle_changed:
                    project.lifecycle_changed[label] = False
        st.session_state.sections = new_sections

    # Refresh local alias after migration & ensure all canonical keys exist
    sections = st.session_state.sections
    for t in CANONICAL_SECTIONS:
        sections.setdefault(t, [])

    # ---------- Seed defaults once with detailed labels ----------
    DEFAULT_PRODUCT = ["A1","A2","A3"]         # Product bucket
    DEFAULT_CONSTR  = ["A4","A5"]              # Construction bucket
    DEFAULT_USE     = ["B1","B2","B3","B4","B5"]
    DEFAULT_EOL     = ["C1","C2","C3","C4"]
    OPTION_A0 = "A0"
    OPTION_D  = "D"

    def _add_unique(bucket: str, code: str):
        label = CODE_TO_LABEL.get(code, code)
        if label not in sections[bucket]:
            sections[bucket].append(label)
        project.lifecycle_changed[label] = False  # never highlighted by default

    # Seed only if everything is empty (no user content yet)
    if (
        not st.session_state.get("seeded_canon_labels", False)
        and not project.lifecycle_stages
        and all(len(v) == 0 for v in sections.values())
    ):
        for c in DEFAULT_PRODUCT:  _add_unique(CANONICAL_SECTIONS[0], c)
        for c in DEFAULT_CONSTR:   _add_unique(CANONICAL_SECTIONS[1], c)
        for c in DEFAULT_USE:      _add_unique(CANONICAL_SECTIONS[2], c)
        for c in DEFAULT_EOL:      _add_unique(CANONICAL_SECTIONS[3], c)
        st.session_state.seeded_canon_labels = True

    # ---------- Optional modules (A0 and D) with detailed labels ----------
    opt_cols = st.columns([3, 3])
    with opt_cols[0]:
        inc_a0 = st.checkbox("Include A0 (UK only)", value=False, key="inc_a0")
    with opt_cols[1]:
        inc_d  = st.checkbox("Include D (beyond system boundary)", value=False, key="inc_d")

    label_a0 = CODE_TO_LABEL[OPTION_A0]
    label_d  = CODE_TO_LABEL[OPTION_D]

    if inc_a0:
        _add_unique(CANONICAL_SECTIONS[0], OPTION_A0)
    else:
        if label_a0 in sections[CANONICAL_SECTIONS[0]]:
            sections[CANONICAL_SECTIONS[0]].remove(label_a0)
            project.lifecycle_changed.pop(label_a0, None)

    if inc_d:
        _add_unique(CANONICAL_SECTIONS[3], OPTION_D)
    else:
        if label_d in sections[CANONICAL_SECTIONS[3]]:
            sections[CANONICAL_SECTIONS[3]].remove(label_d)
            project.lifecycle_changed.pop(label_d, None)

    # Give users headroom beyond defaults
    MAX_TOTAL = max(30, MAX_TOTAL if 'MAX_TOTAL' in locals() else 30)




    # ---------- Scoping exercise (required) ----------
    st.markdown("##### Scoping exercise (required before proceeding)")
    st.markdown(
        "Before using SEED, define the **core function** and a **functional unit**.\n\n"
        "Prefer function-over-time, e.g. “A tire enabling **100,000 km** of travel with reduced maintenance.”"
    )

    PDF_PATH = pathlib.Path("scopingexercise.pdf")  # adjust if it's in a subfolder, e.g. Path("assets/scopingexercise.pdf")
    try:
        if PDF_PATH.exists():
            with PDF_PATH.open("rb") as f:
                st.download_button(
                    "📥 Download help for the scoping exercise (PDF)",
                    data=f.read(),
                    file_name="scopingexercise.pdf",
                    mime="application/pdf",
                )
        else:
            st.info(f"Place **{PDF_PATH}** next to your app to enable the download button.")
    except Exception as e:
        st.warning(f"Couldn’t load the PDF: {e}")

    # --- Core function (keeps live-binding as you had) ---
    project.core_function = st.text_area(
        "Core function (one sentence)",
        value=project.core_function,
        height=80,
        placeholder="e.g., The main function of the self-healing tire is to enable 100,000 km of safe travel with reduced maintenance.",
    )

    # --- Functional unit with explicit Save button ---
    # Use a draft field in session state so typing doesn't overwrite the saved value
    if "fu_draft" not in st.session_state:
        st.session_state.fu_draft = project.functional_unit

    st.session_state.fu_draft = st.text_input(
        "Functional unit (required)",
        value=st.session_state.fu_draft,
        placeholder="e.g., A tire enabling 100,000 km of driving",
        key="functional_unit_draft_input",
    )

    cols_fu = st.columns([1, 6])
    with cols_fu[0]:
        if st.button("💾 Save", key="save_fu_btn", use_container_width=True):
            project.functional_unit = (st.session_state.fu_draft or "").strip()
            # recompute the gate immediately
            st.session_state.scoping_done = scoping_is_done(project)
            st.success("Functional unit saved.")
            st.rerun()
    with cols_fu[1]:
        st.caption(f"Saved value: **{project.functional_unit or '— (none saved yet) —'}**")




    # ---------- Helpers ----------
    MAX_TOTAL = 7
    def total_count() -> int:
        return sum(len(v) for v in sections.values())

    # ---------- Per-subtitle stage editor ----------
    for sec_idx, title in enumerate(SECTION_TITLES):
        safe = f"sec{sec_idx}"  # unique, stable key prefix for this section
        st.markdown(f"#### {title}")
        lst = sections[title]   # the actual list of stages under this subtitle

        # Existing rows
        for i, name in enumerate(list(lst)):  # list(...) to avoid issues if we pop during iteration
            cols = st.columns([6, 2, 2, 2, 2])
            # rename
            new_name = cols[0].text_input("Stage name", value=name, key=f"{safe}_name_{i}")
            # will change?
            will_change = project.lifecycle_changed.get(name, False)
            new_change = cols[1].checkbox("Will change?", value=will_change, key=f"{safe}_chg_{i}")

            # move up
            if cols[2].button("⬆️", key=f"{safe}_up_{i}") and i > 0:
                lst[i-1], lst[i] = lst[i], lst[i-1]
                st.rerun()
            # move down
            if cols[3].button("⬇️", key=f"{safe}_dn_{i}") and i < len(lst)-1:
                lst[i+1], lst[i] = lst[i], lst[i+1]
                st.rerun()
            # delete
            if cols[4].button("🗑️", key=f"{safe}_del_{i}"):
                project.lifecycle_changed.pop(name, None)
                lst.pop(i)
                st.rerun()

            # write back rename + change flag (handle rename)
            if new_name != name:
                # carry the change flag to the new name
                project.lifecycle_changed[new_name] = new_change
                project.lifecycle_changed.pop(name, None)
                lst[i] = new_name
            else:
                project.lifecycle_changed[name] = new_change
                lst[i] = name

        # Add a new stage within this subtitle
        add_cols = st.columns([6, 2, 2])
        add_name = add_cols[0].text_input(f"➕ Add stage in {title}", key=f"{safe}_add_name")
        add_change = add_cols[1].checkbox("Will change?", key=f"{safe}_add_chg")
        if add_cols[2].button("Add stage", key=f"{safe}_add_btn"):
            if not add_name.strip():
                st.warning("Please enter a stage name.")
            elif total_count() >= MAX_TOTAL:
                st.warning(f"Max {MAX_TOTAL} stages in total.")
            else:
                nm = add_name.strip()
                lst.append(nm)
                project.lifecycle_changed[nm] = add_change
                st.rerun()

        st.markdown("---")

    # ---------- Flatten to legacy fields used by steps 3–5 ----------
    project.lifecycle_stages = [nm for t in SECTION_TITLES for nm in sections[t]]
    # Clean any stale flags
    project.lifecycle_changed = {k: v for k, v in project.lifecycle_changed.items() if k in project.lifecycle_stages}

    # ---------- Status + utilities ----------
    st.metric("Total stages", len(project.lifecycle_stages))

    ucols = st.columns(2)
    with ucols[0]:
        if st.button("↺ Reset all stages"):
            st.session_state.sections = {t: [] for t in SECTION_TITLES}
            project.lifecycle_stages = []
            project.lifecycle_changed = {}
            st.rerun()
    with ucols[1]:
        project.scoping_notes = st.text_area(
            "Notes (sources, assumptions, scope boundaries)",
            value=project.scoping_notes,
            height=120,
            key="scoping_notes",
        )

    # Gate / status (no need to set a flag here; we already compute it globally)
    if st.session_state.scoping_done:
        st.success("Scoping complete ✅  (Functional unit provided and at least one stage added.)")
    else:
        missing = []
        if not project.functional_unit.strip():
            missing.append("functional unit")
        if not project.lifecycle_stages:
            missing.append("≥ 1 stage")
        st.warning("Please provide: " + " and ".join(missing) + " before moving to Step 3.")
    bottom_nav()


# -------------------------------
# Step 3: Select factors
# -------------------------------
elif step.startswith("3"):
    st.subheader("Step 3 — Select the 3 most important factors in each dimension")
    st.caption("Exactly 3 in Environmental, 3 in Social, and 3 in Economic. These will be used in the scoring grid.")

# Require scoping completion
    if not st.session_state.get("scoping_done"):
        st.error("Please complete the Scoping exercise in Step 2 (functional unit + at least one stage).")
        st.stop()

    # Helpful fold-outs with factor meanings
    with st.expander("🔎 Factor definitions (Environmental/Social/Economic)"):
        tab_env, tab_soc, tab_eco = st.tabs(["Environmental (EF3.1)", "Social", "Economic"])

        with tab_env:
            for name in sorted(ENV_FACTOR_META.keys()):
                meta = ENV_FACTOR_META[name]
                with st.expander(name, expanded=False):
                    st.markdown(
                        f"**Indicator:** {meta['indicator']}  \n"
                        f"**Category:** {meta['category']}  \n"
                        f"**Method:** {meta['method']} ({meta['version']})  \n"
                        f"**UUID:** `{meta['uuid']}` \n"
                        f"**Explanation:** {meta['explanation']} \n"
                    )

        with tab_soc:
            for name in sorted(SOCIAL_FACTOR_META.keys()):
                with st.expander(name, expanded=False):
                    st.markdown(SOCIAL_FACTOR_META[name])

        with tab_eco:
            for name in sorted(ECON_FACTOR_META.keys()):
                with st.expander(name, expanded=False):
                    st.markdown(ECON_FACTOR_META[name])


    def pick3(label, factors_list, keyprefix, current_selection):
        options = factor_names(factors_list)
        default = current_selection if current_selection else [f for f in options if next(ff for ff in factors_list if ff["name"]==f)["selected"]]
        chosen = st.multiselect(label, options=options, default=default, key=keyprefix)
        if len(chosen) != 3:
            st.warning("Please select exactly 3.")
        return chosen

    env_sel = pick3("Environmental", ENVIRONMENTAL_FACTORS, "ENV_SEL", project.selected_factors.get("Environmental", []))
    soc_sel = pick3("Social", SOCIAL_FACTORS, "SOC_SEL", project.selected_factors.get("Social", []))
    eco_sel = pick3("Economic", ECONOMIC_FACTORS, "ECO_SEL", project.selected_factors.get("Economic", []))

    project.selected_factors["Environmental"] = env_sel
    project.selected_factors["Social"] = soc_sel
    project.selected_factors["Economic"] = eco_sel

    # Ensure grid has all combinations
    all9 = env_sel + soc_sel + eco_sel
    project.ensure_grid(all9)
    bottom_nav()

# -------------------------------
# Step 4: Scoring grid
# -------------------------------
elif step.startswith("4"):
    st.subheader("Step 4 — Score each selected factor across each life cycle stage")
    st.caption("Use 1–5 where 1 = Much Worse, 3 = Equal, 5 = Much Better (vs. baseline). Include a one‑sentence justification.")

    # all factors (must be exactly 9)
    all9 = project.selected_factors.get("Environmental", []) + \
           project.selected_factors.get("Social", []) + \
           project.selected_factors.get("Economic", [])

    if len(all9) != 9 or any(len(project.selected_factors.get(k, [])) != 3 for k in ["Environmental","Social","Economic"]):
        st.error("You must select exactly 3 factors in each category in Step 3 before scoring.")
        st.stop()

    project.ensure_grid(all9)

    legend = pd.DataFrame([{"Score": r["upper"], "Meaning": r["label"], "Explanation": r["explanation"]} for r in INTERPRETATION])
    st.caption("Tip: Tick **I don’t know** to exclude a cell from all averages.")
    st.dataframe(legend, use_container_width=True)

    for stage in project.lifecycle_stages:
        st.markdown(f"#### 🧩 {stage}")
        if project.lifecycle_changed.get(stage, False):
            st.caption("This stage is expected to change with the new material.")

        # Show by category
        for cat, factors in [("Environmental", project.selected_factors["Environmental"]),
                             ("Social", project.selected_factors["Social"]),
                             ("Economic", project.selected_factors["Economic"])]:
            with st.expander(f"{cat}", expanded=True):
                cols = st.columns(3)
                for i, fname in enumerate(factors):
                    col = cols[i % 3]
                    with col:
                        fs = project.grid.setdefault(stage, {}).setdefault(fname, FactorScore())
                        # Select-slider including “I don’t know”
                        current = fs.score if fs.score in (1, 2, 3, 4, 5) else "I don’t know"
                        unknown_key = f"{stage}_{fname}_unknown"
                        is_unknown_default = (fs.score is None)
                        is_unknown = st.checkbox("I don’t know", value=is_unknown_default, key=unknown_key)

                        # Slider: enabled only when not unknown
                        # If previously unknown, show a neutral default (3) until the user picks a value.
                        current_val = 3 if fs.score is None else int(fs.score)
                        new_val = st.slider(
                            f"{fname} — score",
                            min_value=1,
                            max_value=5,
                            value=current_val,
                            key=f"{stage}_{fname}_score",
                            disabled=is_unknown
                        )

                        # Persist back to the model
                        fs.score = None if is_unknown else float(new_val)
                        fs.note = st.text_area(f"Justification for {fname}", value=fs.note, key=f"{stage}_{fname}_note", height=80)
                        project.grid[stage][fname] = fs
    bottom_nav()


# -------------------------------
# Step 5: Results & plots
# -------------------------------
elif step.startswith("5"):
    st.subheader("Step 5 — Results & plots")

    all9 = project.selected_factors.get("Environmental", []) + \
           project.selected_factors.get("Social", []) + \
           project.selected_factors.get("Economic", [])
    if len(all9) != 9:
        st.error("Complete Steps 3–4 first.")
        st.stop()

    project.ensure_grid(all9)

    # Tables
    avg_stage = project.average_by_stage()
    avg_factor = project.average_by_factor()
    overall = project.overall_score()

    left, right = st.columns(2)
    with left:
        st.metric("Overall score", overall if overall is not None else "n/a", help="Average of stage means (1=Much Better, 3=Equal, 5=Much Worse).")
        stage_df = pd.DataFrame({
            "Lifecycle stage": list(avg_stage.keys()),
            "Average score": [None if math.isnan(v) else round(v, 1) for v in avg_stage.values()]
        })
        st.dataframe(stage_df, use_container_width=True)
    with right:
        factor_df = pd.DataFrame({"Factor": list(avg_factor.keys()), "Average score": [round(v,1) for v in avg_factor.values()]})
        st.dataframe(factor_df, use_container_width=True)
    
    # Build plotting frames
    stage_plot = to_plot_df(stage_df, "Lifecycle stage", "Average score").rename(columns={"Lifecycle stage": "Category"})
    factor_plot = to_plot_df(factor_df, "Factor", "Average score").rename(columns={"Factor": "Category"})


    # Plots
    st.markdown("#### 📊 Average by lifecycle stage")
    fig1 = horizontal_delta_bar(stage_plot, "Average by lifecycle stage")
    st.plotly_chart(fig1, use_container_width=True)

    st.markdown("#### 📈 Average by factor")
    fig2 = horizontal_delta_bar(factor_plot, "Average by factor")
    st.plotly_chart(fig2, use_container_width=True)

    # Worst performing stage (ignore NaNs)
    valid_stage_avgs = {k: v for k, v in avg_stage.items() if not math.isnan(v)}
    if valid_stage_avgs:
        worst_stage, worst_val = min(valid_stage_avgs.items(), key=lambda kv: kv[1])
        st.markdown(f"### 🚩 Worst performing stage: **{worst_stage}** (avg {worst_val:.2f} — {interp_label(worst_val)})")
        breakdown = project.grid.get(worst_stage, {})
        if breakdown:
            wdf = pd.DataFrame({
                "Factor":[f for f in breakdown.keys()],
                "Score":[breakdown[f].score for f in breakdown.keys()],
                "Justification":[breakdown[f].note for f in breakdown.keys()],
            }).sort_values("Score", ascending=True)
            st.dataframe(wdf, use_container_width=True)

    # Best performing stage (ignore NaNs)
    if valid_stage_avgs:
        best_stage, best_val = max(valid_stage_avgs.items(), key=lambda kv: kv[1])
        st.markdown(f"### 🏆 Best performing stage: **{best_stage}** (avg {best_val:.2f} — {interp_label(best_val)})")
        breakdown = project.grid.get(best_stage, {})
        if breakdown:

            bdf = pd.DataFrame({
                "Factor":[f for f in breakdown.keys()],
                "Score":[breakdown[f].score for f in breakdown.keys()],
                "Justification":[breakdown[f].note for f in breakdown.keys()],
            }).sort_values("Score", ascending=False)
            st.dataframe(bdf, use_container_width=True)

    # Export results
    export = {
        "project": project.name,
        "description": project.description,
        "trl": project.trl,
        "lifecycle_stages": project.lifecycle_stages,
        "lifecycle_changed": project.lifecycle_changed,
        "selected_factors": project.selected_factors,
        "grid": {stage:{f: asdict(fs) for f, fs in fdict.items()} for stage, fdict in project.grid.items()},
        "averages": {"by_stage": avg_stage, "by_factor": avg_factor, "overall": overall},
    }
    st.download_button("💾 Download results JSON", data=json.dumps(export, indent=2), file_name=f"{project.name.replace(' ','_')}_results.json", mime="application/json")




    def report_md(
        project,
        overall,
        avg_stage: Dict[str, float],
        avg_factor: Dict[str, float],
        functional_unit: str,
        core_function: str,
    ) -> str:
        lines = []
        lines.append(f"# {project.name} — SEED report")
        lines.append("")
        lines.append(f"**TRL:** {project.trl}")
        if core_function.strip():
            lines.append(f"**Core function:** {core_function.strip()}")
        if functional_unit.strip():
            lines.append(f"**Functional unit:** {functional_unit.strip()}")
        lines.append("")
        lines.append("## Lifecycle stages")
        for s in project.lifecycle_stages:
            chg = " *(will change)*" if project.lifecycle_changed.get(s, False) else ""
            lines.append(f"- {s}{chg}")
        lines.append("")
        lines.append("## Selected factors")
        for cat in ("Environmental","Social","Economic"):
            lines.append(f"**{cat}:** " + ", ".join(project.selected_factors.get(cat, [])))
        lines.append("")
        lines.append("## Scores")
        lines.append(f"- **Overall score:** {overall if overall is not None else 'n/a'}")
        if avg_stage:
            lines.append("")
            lines.append("### Average by lifecycle stage")
            valid_stage_avgs = {k: v for k, v in avg_stage.items() if not math.isnan(v)}
            for k, v in sorted(valid_stage_avgs.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"- {k}: {v:.2f}")

        if avg_factor:
            lines.append("")
            lines.append("### Average by factor")
            for k, v in sorted(avg_factor.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"- {k}: {v:.2f}")
        if valid_stage_avgs:
            worst_stage, worst_val = min(valid_stage_avgs.items(), key=lambda kv: kv[1])
            lines.append("")
            lines.append("### Worst performing stage")
            lines.append(f"- **{worst_stage}** (avg {worst_val:.2f} — {interp_label(worst_val)})")
        lines.append("")
        if valid_stage_avgs:
            best_stage, best_val = max(valid_stage_avgs.items(), key=lambda kv: kv[1])
            lines.append("### Best performing stage")
            lines.append(f"- **{best_stage}** (avg {best_val:.2f} — {interp_label(best_val)})")
        lines.append("")
        if project.scoping_notes.strip():
            lines.append("## Notes")
            lines.append(project.scoping_notes.strip())
            lines.append("")
        lines.append("_Score guide — 1: Much Better • 2: Better • 3: Equal • 4: Worse • 5: Much Worse._")
        return "\n".join(lines)
    
    

    # --- Report button lives here, AFTER overall/avg_* are defined ---
    st.download_button(
        "📄 Download Markdown report",
        data=report_md(
            project,
            overall,
            avg_stage,
            avg_factor,
            functional_unit=project.functional_unit,
            core_function=project.core_function,
        ),
        file_name=f"{project.name.replace(' ','_')}_SEED_report.md",
        mime="text/markdown",
    )
    bottom_nav()



# -------------------------------
# Footer
# -------------------------------
st.markdown("---")
st.caption("Score guide — 1: Much Worse • 2: Worse • 3: Equal • 4: Better • 5: Much Better.")
st.caption("This tool is intended for early‑stage, qualitative sustainability scoping and is not a substitute for a full LCA or S-LCA.")
