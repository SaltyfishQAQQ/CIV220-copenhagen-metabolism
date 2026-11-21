# Copenhagen urban metabolism dashboard

Interactive companion to the CIV220 urban metabolism report (City of Copenhagen, 2024).

## Run locally (conda environment ECE421)

Open Anaconda Prompt and run:

    conda activate ECE421
    cd C:\Users\yhlin\CIV220
    pip install -r requirements.txt
    streamlit run app.py

The dashboard opens at http://localhost:8501. Stop it with Ctrl+C.

## Deploy on Streamlit Community Cloud

1. Create a public GitHub repository and upload everything in this folder
   (including the `.streamlit` folder).
2. Go to https://share.streamlit.io, sign in with GitHub and choose "Create app".
3. Pick the repository, branch `main`, and main file `app.py`. Under
   "Advanced settings", choose Python 3.11 or later.
4. Deploy, then copy the app's URL into Section 2 of the report.

## Files

- `app.py`: the whole dashboard, including the interactive metabolism diagram.
- `data.json`: every per-capita value shown, produced by `build_data.py`.
- `build_data.py`: computes the values from the sourced totals and rewrites `data.json`
  (run `python build_data.py` only if you change an input).
- `requirements.txt`: packages the app needs.
- `.streamlit/config.toml`: colour theme.
