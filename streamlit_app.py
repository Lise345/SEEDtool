
# streamlit_app.py
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple
import statistics

import streamlit as st
import pandas as pd
import plotly.express as px

APP_TITLE = "Early-Stage Sustainability Assessment (ESSA)"
APP_TAGLINE = "For new materials & products — quick, structured, and project-based"

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
        name = st.text_input("Project name", value="New ESSA Project")
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
st.set_page_config(page_title="ESSA", page_icon="🌿", layout="wide")
st.title(f"🌿 {APP_TITLE}")
st.caption(APP_TAGLINE)

if st.session_state.active_project is None:
    st.info("Create or open a project from the sidebar to begin.")
    st.stop()

project: Project = st.session_state.projects[st.session_state.active_project]

# -------------------------------
# Navigation
# -------------------------------
st.markdown("### Workflow")
step = st.sidebar.radio(
    "Navigate steps",
    options=[
        "1) TRL & actors",
        "2) Scoping & lifecycle",
        "3) Select factors (3 each)",
        "4) Scoring grid",
        "5) Results & plots",
    ],
    index=0
)

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
    st.write("Draft your life cycle stages (max 7). Mark which ones are expected to change due to your new material.")

    # Manage lifecycle stages
    with st.expander("Life cycle stages", expanded=True):
        # Keep list length <= 7
        stages = project.lifecycle_stages.copy()
        for i, stage in enumerate(stages):
            cols = st.columns([8,2,2])
            with cols[0]:
                new_name = st.text_input(f"Stage {i+1}", value=stage, key=f"stage_{i}")
            with cols[1]:
                if st.button("⬆️", key=f"up_{i}") and i>0:
                    stages[i-1], stages[i] = stages[i], stages[i-1]
            with cols[2]:
                if st.button("🗑️", key=f"del_{i}"):
                    stages.pop(i)
                    # force break to avoid index issues
                    st.experimental_rerun()
            stages[i] = new_name

        cols = st.columns(2)
        with cols[0]:
            if len(stages) < 7 and st.button("➕ Add stage"):
                stages.append(f"New stage {len(stages)+1}")
        with cols[1]:
            if st.button("↺ Reset to default"):
                stages = DEFAULT_LIFE_CYCLE.copy()

        project.lifecycle_stages = stages

    with st.expander("Mark stages that change due to the new material", expanded=True):
        changed = {}
        for stage in project.lifecycle_stages:
            changed[stage] = st.checkbox(stage, value=project.lifecycle_changed.get(stage, False), key=f"chg_{stage}")
        project.lifecycle_changed = changed

    st.subheader("Scoping notes")
    project.scoping_notes = st.text_area("Capture decisions and data sources for the scoping exercise.", value=project.scoping_notes, height=150)

# -------------------------------
# Step 3: Select factors
# -------------------------------
elif step.startswith("3"):
    st.subheader("Step 3 — Select the 3 most important factors in each dimension")
    st.caption("Exactly 3 in Environmental, 3 in Social, and 3 in Economic. These will be used in the scoring grid.")

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
        stage_df = pd.DataFrame({"Lifecycle stage": list(avg_stage.keys()), "Average score": [round(v,2) for v in avg_stage.values()]})
        st.dataframe(stage_df, use_container_width=True)
    with right:
        factor_df = pd.DataFrame({"Factor": list(avg_factor.keys()), "Average score": [round(v,2) for v in avg_factor.values()]})
        st.dataframe(factor_df, use_container_width=True)

    # Plots
    st.markdown("#### 📊 Average by lifecycle stage")
    fig1 = px.bar(stage_df, x="Lifecycle stage", y="Average score", text="Average score", range_y=[1,5])
    fig1.update_traces(textposition='outside')
    fig1.update_layout(yaxis_title="Score (1=Better … 5=Worse)", xaxis_title="Lifecycle stage", margin=dict(t=10,b=10))
    st.plotly_chart(fig1, use_container_width=True)

    st.markdown("#### 📈 Average by factor")
    fig2 = px.bar(factor_df, x="Factor", y="Average score", text="Average score", range_y=[1,5])
    fig2.update_traces(textposition='outside')
    fig2.update_layout(yaxis_title="Score (1=Better … 5=Worse)", xaxis_title="Factor", margin=dict(t=10,b=10))
    st.plotly_chart(fig2, use_container_width=True)

    # Worst performing stage
    if avg_stage:
        worst_stage, worst_val = max(avg_stage.items(), key=lambda kv: kv[1])
        st.markdown(f"### 🚩 Worst performing stage: **{worst_stage}** (avg {worst_val:.2f} — {interp_label(worst_val)})")
        # Show its factor breakdown
        breakdown = project.grid.get(worst_stage, {})
        if breakdown:
            wdf = pd.DataFrame({
                "Factor":[f for f in breakdown.keys()],
                "Score":[breakdown[f].score for f in breakdown.keys()],
                "Justification":[breakdown[f].note for f in breakdown.keys()],
            }).sort_values("Score", ascending=False)
            st.dataframe(wdf, use_container_width=True)

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

# -------------------------------
# Footer
# -------------------------------
st.markdown("---")
st.caption("Score guide — 1: Much Better • 2: Better • 3: Equal • 4: Worse • 5: Much Worse.")
st.caption("This tool is intended for early‑stage, qualitative sustainability scoping and is not a substitute for a full LCA or S-LCA.")
