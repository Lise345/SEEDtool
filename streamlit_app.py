
# streamlit_app.py
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple
import statistics

import streamlit as st
import pandas as pd
import plotly.express as px

APP_TITLE = "SEED — Sustainability Evaluation for Early-stage Decisions"
APP_TAGLINE = "Project-based scoping for new materials & products"

# -------------------------------
# Data & configuration
# -------------------------------

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
    {"label":"Much Better", "upper":1, "explanation":"Leads to a measurable improvement"},
    {"label":"Better", "upper":2, "explanation":"Might lead to a measurable improvement"},
    {"label":"Equal", "upper":3, "explanation":"No measurable change"},
    {"label":"Worse", "upper":4, "explanation":"Might lead to a measurable worsening"},
    {"label":"Much Worse", "upper":5, "explanation":"Leads to a measurable worsening"},
]

DEFAULT_LIFE_CYCLE = [
    "Raw material extraction",
    "Material synthesis / processing",
    "Component manufacturing",
    "Product assembly",
    "Distribution & logistics",
    "Use phase",
    "End-of-life (reuse/recycling/disposal)",
]

# --- Subtitles (not counted as stages themselves) ---
SECTION_TITLES = [
    "Raw Material Extraction & Processing",
    "Manufacturing",
    "Transportation",
    "Installation & Operation",
    "End-of-Life & Recycling",
]

# --- Factor metadata for Step 3 (EF3.1) ---
ENV_FACTOR_META = {
    "Acidification": {
        "indicator": "Accumulated Exceedance (AE)", "category": "ACIDIFICATION",
        "method": "EF3.1", "version": "2017-01.04.000",
        "uuid": "b5c611c6-def3-11e6-bf01-fe55135034f3",
    },
    "Climate change": {
        "indicator": "Radiative forcing as GWP100", "category": "CLIMATE_CHANGE",
        "method": "EF3.1", "version": "2022-01.00.000",
        "uuid": "6209b35f-9447-40b5-b68c-a1099e3674a0",
    },
    "Ecotoxicity, freshwater": {
        "indicator": "CTUe", "category": "AQUATIC_ECO_TOXICITY",
        "method": "EF3.1", "version": "2022-01.00.000",
        "uuid": "05316e7a-b254-4bea-9cf0-6bf33eb5c630",
    },
    "Eutrophication, marine": {
        "indicator": "Fraction of N to marine", "category": "AQUATIC_EUTROPHICATION",
        "method": "EF3.1", "version": "2017-02.00.010",
        "uuid": "b5c619fa-def3-11e6-bf01-fe55135034f3",
    },
    "Eutrophication, freshwater": {
        "indicator": "Fraction of P to freshwater", "category": "AQUATIC_EUTROPHICATION",
        "method": "EF3.1", "version": "2017-01.00.010",
        "uuid": "b53ec18f-7377-4ad3-86eb-cc3f4f276b2b",
    },
    "Eutrophication, terrestrial": {
        "indicator": "Accumulated Exceedance (AE)", "category": "TERRESTRIAL_EUTROPHICATION",
        "method": "EF3.1", "version": "2017-01.02.009",
        "uuid": "b5c614d2-def3-11e6-bf01-fe55135034f3",
    },
    "Ionizing radiation, effect on human health": {
        "indicator": "Human exposure efficiency rel. U235", "category": "IONIZING_RADIATION",
        "method": "EF3.1", "version": "2017-01.00.011",
        "uuid": "b5c632be-def3-11e6-bf01-fe55135034f3",
    },
    "Land Use": {
        "indicator": "Soil quality index", "category": "LAND_USE",
        "method": "EF3.1", "version": "2017-01.00.010",
        "uuid": "b2ad6890-c78d-11e6-9d9d-cec0c932ce01",
    },
    "Ozone depletion": {
        "indicator": "ODP", "category": "OZONE_DEPLETION",
        "method": "EF3.1", "version": "2017-02.00.012 (until 2040)",
        "uuid": "b5c629d6-def3-11e6-bf01-fe55135034f3",
    },
    "Particulate matters": {
        "indicator": "Impact on human health", "category": "RESPIRATORY_INORGANICS",
        "method": "EF3.1", "version": "2017-02.00.011",
        "uuid": "b5c602c6-def3-11e6-bf01-fe55135034f3",
    },
    "Photochemical ozone formation, effect on human health": {
        "indicator": "Tropospheric ozone conc. increase", "category": "PHOTOCHEMICAL_OZONE_CREATION",
        "method": "EF3.1", "version": "2017-02.01.000",
        "uuid": "b5c610fe-def3-11e6-bf01-fe55135034f3",
    },
    "Resource use, fossils": {
        "indicator": "ADP-fossil", "category": "ABIOTIC_RESOURCE_DEPLETION",
        "method": "EF3.1", "version": "2017-01.00.010",
        "uuid": "b2ad6110-c78d-11e6-9d9d-cec0c932ce01",
    },
    "Resource use, minerals and metals": {
        "indicator": "ADP ultimate reserve", "category": "ABIOTIC_RESOURCE_DEPLETION",
        "method": "EF3.1", "version": "2017-01.00.010",
        "uuid": "b2ad6494-c78d-11e6-9d9d-cec0c932ce01",
    },
    "Water use": {
        "indicator": "Deprivation-weighted water consumption", "category": "OTHER",
        "method": "EF3.1", "version": "2017-03.00.014",
        "uuid": "b2ad66ce-c78d-11e6-9d9d-cec0c932ce01",
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
    score: int = 3
    note: str = ""

@dataclass
class Project:
    name: str
    description: str = ""
    trl: int = 4
    scoping_notes: str = ""
    lifecycle_stages: List[str] = field(default_factory=lambda: DEFAULT_LIFE_CYCLE.copy())
    lifecycle_changed: Dict[str, bool] = field(default_factory=dict)  # which stages change due to new material
    selected_factors: Dict[str, List[str]] = field(default_factory=dict)  # keys: "Environmental","Social","Economic"
    grid: Dict[str, Dict[str, FactorScore]] = field(default_factory=dict)  # stage -> factor -> FactorScore

    def ensure_grid(self, all_factors: List[str]):
        # Ensure every stage and selected factor pair exists
        for stage in self.lifecycle_stages:
            self.grid.setdefault(stage, {})
            for f in all_factors:
                if f not in self.grid[stage]:
                    self.grid[stage][f] = FactorScore()

    def average_by_stage(self) -> Dict[str, float]:
        out = {}
        for stage, facs in self.grid.items():
            if facs:
                out[stage] = statistics.mean(fs.score for fs in facs.values())
            else:
                out[stage] = float("nan")
        return out

    def average_by_factor(self) -> Dict[str, float]:
        # factor -> mean across stages
        factor_sums: Dict[str, List[int]] = {}
        for stage, facs in self.grid.items():
            for f, fs in facs.items():
                factor_sums.setdefault(f, []).append(fs.score)
        return {f: statistics.mean(vals) for f, vals in factor_sums.items()} if factor_sums else {}

    def overall_score(self) -> Optional[float]:
        avs = self.average_by_stage()
        vals = [v for v in avs.values() if isinstance(v, (int, float))]
        return round(statistics.mean(vals), 2) if vals else None

# -------------------------------
# Helpers
# -------------------------------
def factor_names(factors):
    return [f["name"] for f in factors]

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
    st.title("📁 Projects")
    existing = list(st.session_state.projects.keys())
    selected = st.selectbox("Open project", options=["<New project>"] + existing, index=0 if st.session_state.active_project is None else (existing.index(st.session_state.active_project)+1 if st.session_state.active_project in existing else 0))

    if selected == "<New project>":
        st.write("Create a new project.")
        name = st.text_input("Project name", value="New SEED Project")
        desc = st.text_area("Short description", value="")
        if st.button("➕ Create"):
            if not name.strip():
                st.warning("Please provide a project name.")
            elif name in st.session_state.projects:
                st.warning("A project with this name already exists.")
            else:
                st.session_state.projects[name] = Project(name=name, description=desc)
                st.session_state.active_project = name
                st.success(f"Created project “{name}”.")
    else:
        st.session_state.active_project = selected
        if st.button("🗑️ Delete this project"):
            st.session_state.projects.pop(selected, None)
            st.session_state.active_project = None
            st.warning(f"Deleted project “{selected}”.")

    st.markdown("---")
    st.subheader("Import / Export")
    uploaded = st.file_uploader("Import project JSON", type=["json"], help="Upload a project previously exported from this app.")
    if uploaded is not None:
        try:
            data = json.load(uploaded)
            proj = Project(**data)
            st.session_state.projects[proj.name] = proj
            st.session_state.active_project = proj.name
            st.success(f"Imported “{proj.name}”.")
        except Exception as e:
            st.error(f"Could not import: {e}")

    if st.session_state.active_project:
        ap = st.session_state.projects[st.session_state.active_project]
        download_json_button(asdict(ap), f"{ap.name.replace(' ','_')}.json", "💾 Export active project")

    st.markdown("---")
    st.caption("Tip: You can create multiple projects and switch between them here.")

# -------------------------------
# Header & guard
# -------------------------------
st.set_page_config(page_title="SEED", page_icon="🌱", layout="wide")
st.title(f"🌿 {APP_TITLE}")
st.caption(APP_TAGLINE)

if st.session_state.active_project is None:
    st.info("Create or open a project from the sidebar to begin.")
    st.stop()

project: Project = st.session_state.projects[st.session_state.active_project]

# --- NEW: sections (per-session lists of stages under each subtitle) ---
if "sections" not in st.session_state:
    st.session_state.sections = {title: [] for title in SECTION_TITLES}

# --- NEW: scoping fields ---
if "core_function" not in st.session_state:
    st.session_state.core_function = ""
if "functional_unit" not in st.session_state:
    st.session_state.functional_unit = ""
if "scoping_done" not in st.session_state:
    st.session_state.scoping_done = False


WORKFLOW_STEPS = [
    "1) TRL & actors",
    "2) Scoping & lifecycle",
    "3) Select factors (3 each)",
    "4) Scoring grid",
    "5) Results & plots",
]


# -------------------------------
# Navigation
# -------------------------------
st.markdown("### Workflow")
if "step_idx" not in st.session_state:
    st.session_state.step_idx = 0

step = st.sidebar.radio("Navigate steps", options=WORKFLOW_STEPS, index=st.session_state.step_idx, key="workflow_radio")
# keep idx in sync if user clicks the radio directly
st.session_state.step_idx = WORKFLOW_STEPS.index(step)

# Back / Next buttons (put wherever you prefer — here below the radio in the sidebar)
bcols = st.sidebar.columns(2)
if bcols[0].button("⬅️ Back", use_container_width=True) and st.session_state.step_idx > 0:
    st.session_state.step_idx -= 1
    st.rerun()
if bcols[1].button("Next ➡️", use_container_width=True) and st.session_state.step_idx < len(WORKFLOW_STEPS)-1:
    st.session_state.step_idx += 1
    st.rerun()

# Use `step` in your if/elif sections as before


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

    # ---------- Scoping exercise (required) ----------
    st.markdown("##### Scoping exercise (required before proceeding)")
    st.markdown(
        "Before using SEED, define the **core function** and a **functional unit**.\n\n"
        "**Core Function (one sentence):**\n"
        "“The main function of this material or application is to …”\n\n"
        "**Functional Unit (quantitative reference):**\n"
        "Prefer function-over-time, e.g. “A tire enabling **100,000 km** of travel with reduced maintenance.”"
    )

    # Use only keys; session_state will store the values
    st.text_area(
        "Core function (one sentence)",
        key="core_function",
        height=80,
        placeholder="e.g., The main function of the self-healing tire is to enable 100,000 km of safe travel with reduced maintenance.",
    )
    st.text_input(
        "Functional unit (required)",
        key="functional_unit",
        placeholder="e.g., A tire enabling 100,000 km of driving",
    )

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
            new_change = cols[1].checkbox("Will change compared to previous technology?", value=will_change, key=f"{safe}_chg_{i}")

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
        add_change = add_cols[1].checkbox("Will change compared to previous technology?", key=f"{safe}_add_chg")
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

    # ---------- Gate progression automatically ----------
    fn_unit_ok = bool(st.session_state.get("functional_unit", "").strip())
    at_least_one_stage = len(project.lifecycle_stages) > 0
    st.session_state.scoping_done = fn_unit_ok and at_least_one_stage

    if st.session_state.scoping_done:
        st.success("Scoping complete ✅  (Functional unit provided and at least one stage added.)")
    else:
        missing = []
        if not fn_unit_ok:
            missing.append("functional unit")
        if not at_least_one_stage:
            missing.append("≥ 1 stage")
        st.warning("Please provide: " + " and ".join(missing) + " before moving to Step 3.")

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
                        f"**UUID:** `{meta['uuid']}`"
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

# -------------------------------
# Step 4: Scoring grid
# -------------------------------
elif step.startswith("4"):
    st.subheader("Step 4 — Score each selected factor across each life cycle stage")
    st.caption("Use 1–5 where 1 = Much Better, 3 = Equal, 5 = Much Worse (vs. baseline). Include a one‑sentence justification.")

    # all factors (must be exactly 9)
    all9 = project.selected_factors.get("Environmental", []) + \
           project.selected_factors.get("Social", []) + \
           project.selected_factors.get("Economic", [])

    if len(all9) != 9 or any(len(project.selected_factors.get(k, [])) != 3 for k in ["Environmental","Social","Economic"]):
        st.error("You must select exactly 3 factors in each category in Step 3 before scoring.")
        st.stop()

    project.ensure_grid(all9)

    legend = pd.DataFrame([{"Score": r["upper"], "Meaning": r["label"], "Explanation": r["explanation"]} for r in INTERPRETATION])
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
                        fs.score = st.slider(f"{fname} — score", min_value=1, max_value=5, value=int(fs.score), key=f"{stage}_{fname}_score")
                        fs.note = st.text_area(f"Justification for {fname}", value=fs.note, key=f"{stage}_{fname}_note", height=80)
                        project.grid[stage][fname] = fs

# -------------------------------
# Step 5: Results & plots
# -------------------------------

# -------- Markdown report --------
elif step.startswith("5"):
    st.subheader("Step 5 — Results & plots")

    all9 = project.selected_factors.get("Environmental", []) + \
           project.selected_factors.get("Social", []) + \
           project.selected_factors.get("Economic", [])
    if len(all9) != 9:
        st.error("Complete Steps 3–4 first.")
        st.stop()

    if not project.lifecycle_stages:
        st.error("Add at least one stage in Step 2 first.")
        st.stop()

    project.ensure_grid(all9)

    # Tables
    avg_stage = project.average_by_stage()
    avg_factor = project.average_by_factor()
    overall = project.overall_score()

    left, right = st.columns(2)
    with left:
        st.metric(
            "Overall score",
            overall if overall is not None else "n/a",
            help="Average of stage means (1=Much Better, 3=Equal, 5=Much Worse)."
        )
        stage_df = pd.DataFrame({
            "Lifecycle stage": list(avg_stage.keys()),
            "Average score": [round(v,1) for v in avg_stage.values()]
        })
        st.dataframe(stage_df, use_container_width=True)
    with right:
        factor_df = pd.DataFrame({
            "Factor": list(avg_factor.keys()),
            "Average score": [round(v,1) for v in avg_factor.values()]
        })
        st.dataframe(factor_df, use_container_width=True)

    def status_label(val: float) -> str:
        return "≤3 (good)" if val <= 3 else ">3 (attention)"

    # ---- Build DataFrames ----
    stage_df = pd.DataFrame({
        "Lifecycle stage": list(avg_stage.keys()),
        "Average score": [round(v, 2) for v in avg_stage.values()],
    })
    factor_df = pd.DataFrame({
        "Factor": list(avg_factor.keys()),
        "Average score": [round(v, 2) for v in avg_factor.values()],
    })

    # ---- Add status colors for both charts ----
    stage_df["Status"]  = stage_df["Average score"].apply(status_label)
    factor_df["Status"] = factor_df["Average score"].apply(status_label)

    # ---- Map factors to their domain for the factor chart ----
    # reverse map from your selected_factors
    domain_map = {}
    for dom in ("Environmental", "Social", "Economic"):
        for f in project.selected_factors.get(dom, []):
            domain_map[f] = dom
    factor_df["Domain"] = factor_df["Factor"].map(domain_map).fillna("Unspecified")

    # ---- Color palette (status) ----
    STATUS_COLORS = {
        "≤3 (good)": "#2ca02c",      # green
        ">3 (attention)": "#8b0000", # dark red
    }

    # ==========================
    # 📊 Average by lifecycle stage
    # ==========================
    st.markdown("#### 📊 Average by lifecycle stage")
    fig1 = px.bar(
        stage_df,
        x="Lifecycle stage",
        y="Average score",
        text="Average score",
        range_y=[1, 5],
        color="Status",
        color_discrete_map=STATUS_COLORS,
    )
    fig1.update_traces(textposition="outside")
    fig1.update_layout(
        yaxis_title="Score (1=Better … 5=Worse)",
        xaxis_title="Lifecycle stage",
        margin=dict(t=10, b=10),
        legend_title_text="Status",
    )
    st.plotly_chart(fig1, use_container_width=True)

    # ==========================
    # 📈 Average by factor
    # ==========================
    # Use color for Status (green/red) and pattern for Domain (Env/Soc/Eco)
    st.markdown("#### 📈 Average by factor")
    PATTERN_MAP = {
        "Environmental": "",
        "Social": "/",
        "Economic": ".",
        "Unspecified": ".",
    }
    fig2 = px.bar(
        factor_df,
        x="Factor",
        y="Average score",
        text="Average score",
        range_y=[1, 5],
        color="Status",
        color_discrete_map=STATUS_COLORS,
        pattern_shape="Domain",
        pattern_shape_map=PATTERN_MAP,
        category_orders={"Domain": ["Environmental", "Social", "Economic", "Unspecified"]},
    )
    fig2.update_traces(textposition="outside")
    fig2.update_layout(
        yaxis_title="Score (1=Better … 5=Worse)",
        xaxis_title="Factor",
        margin=dict(t=10, b=10),
        legend_title_text="",
    )
    st.plotly_chart(fig2, use_container_width=True)


    # Worst performing stage
    if avg_stage:
        worst_stage, worst_val = max(avg_stage.items(), key=lambda kv: kv[1])
        st.markdown(f"### 🚩 Worst performing stage: **{worst_stage}** (avg {worst_val:.2f} — {interp_label(worst_val)})")
        breakdown = project.grid.get(worst_stage, {})
        if breakdown:
            wdf = pd.DataFrame({
                "Factor":[f for f in breakdown.keys()],
                "Score":[breakdown[f].score for f in breakdown.keys()],
                "Justification":[breakdown[f].note for f in breakdown.keys()],
            }).sort_values("Score", ascending=False)
            st.dataframe(wdf, use_container_width=True)

    # Export results (JSON)
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
    st.download_button(
        "💾 Download results JSON",
        data=json.dumps(export, indent=2),
        file_name=f"{project.name.replace(' ','_')}_results.json",
        mime="application/json"
    )



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
            for k, v in sorted(avg_stage.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"- {k}: {v:.2f}")
        if avg_factor:
            lines.append("")
            lines.append("### Average by factor")
            for k, v in sorted(avg_factor.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"- {k}: {v:.2f}")
        if avg_stage:
            worst_stage, worst_val = max(avg_stage.items(), key=lambda kv: kv[1])
            lines.append("")
            lines.append("### Worst performing stage")
            lines.append(f"- **{worst_stage}** (avg {worst_val:.2f} — {interp_label(worst_val)})")
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
            st.session_state.get("functional_unit", ""),
            st.session_state.get("core_function", ""),
        ),
        file_name=f"{project.name.replace(' ','_')}_SEED_report.md",
        mime="text/markdown",
    )




# -------------------------------
# Footer
# -------------------------------
st.markdown("---")
st.caption("Score guide — 1: Much Better • 2: Better • 3: Equal • 4: Worse • 5: Much Worse.")
st.caption("This tool is intended for early‑stage, qualitative sustainability scoping and is not a substitute for a full LCA or S-LCA.")
