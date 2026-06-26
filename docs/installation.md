# Local Installation

Wind Turbine Design Lab is designed to run locally on each user's computer. You
do not need Streamlit Cloud, Snowflake, hosting, or any paid service.

## Requirements

- Windows 10/11 or macOS
- Python 3.12 or newer
- Git, recommended for easy updates
- uv, recommended for simple dependency setup

## Install with Git

```bash
git clone https://github.com/TBK0749/wind-turbine-design-lab.git
cd wind-turbine-design-lab
uv sync
uv run streamlit run app/main.py
```

Open the local URL shown by Streamlit:

```text
http://127.0.0.1:8501
```

To stop the app, return to the terminal and press:

```text
Ctrl + C
```

## Install from ZIP

1. Open the GitHub repository.
2. Click **Code**.
3. Click **Download ZIP**.
4. Unzip the project folder.
5. Open a terminal in the unzipped folder.
6. Run:

```bash
uv sync
uv run streamlit run app/main.py
```

## Update an existing Git installation

If the project was cloned with Git, users do not need to clone again:

```bash
git pull
uv sync
uv run streamlit run app/main.py
```

If the project was downloaded as a ZIP file, download a new ZIP and replace the
old project folder. Save exported CSV, JSON, and design sheet files outside the
project folder before replacing it.

## Common issues

- If Streamlit asks for an email address, press `Enter` without typing anything.
- If port `8501` is busy, stop the old Streamlit terminal with `Ctrl + C`.
- If `git pull` reports local changes, save exported work outside the project
  folder and avoid editing source files.
- Do not click **Deploy** for normal classroom use. This project is intended to
  run locally unless a teacher explicitly asks for online deployment.
