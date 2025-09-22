# ESSA Streamlit App

This app replaces your macro Excel for early-stage sustainability assessments.

## How to run
1. Install dependencies:
   ```bash
   pip install streamlit plotly pandas
   ```
2. Run the app:
   ```bash
   streamlit run streamlit_app.py
   ```

## What it does
- Create multiple **projects** and navigate steps from the sidebar
- **Step 1**: Choose TRL and see **actors to engage** with EU definitions
- **Step 2**: Do **scoping** and build up to **7 lifecycle stages**; mark which stages change
- **Step 3**: Pick the **top 3 Environmental, 3 Social, 3 Economic** factors
- **Step 4**: Fill the **scoring grid** (1–5) with **one‑sentence notes**
- **Step 5**: See **averages by stage & by factor**, the **worst stage**, and **export results**

The score legend matches your Excel:
- 1 = Much Better
- 2 = Better
- 3 = Equal
- 4 = Worse
- 5 = Much Worse
