<img src="media/logo.png" width="420px">

# Todoist Automation with Python

Personal Todoist automations with support for Python scripts and Jupyter
notebooks. The main program reads and modifies real tasks, so it should only be
run with your own credentials and after reviewing the code that will be
activated.

## Requirements

- Python 3.11 recommended. Python 3.10-3.12 should be compatible with the
	versions pinned in `requirements.txt`.
- Git.
- A Todoist account and an API token.
- SMTP credentials if email notifications are enabled.
- An OpenWeather API key only if the weather automation is enabled.

## Windows setup

Open PowerShell in the repository folder:

```powershell
git clone <URL_DEL_REPOSITORIO>
cd Todoist
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks environment activation, you can run the script directly
without activating the environment:

```powershell
.venv\Scripts\python -m pip install -r requirements.txt
```

## macOS or Linux setup

```bash
git clone <URL_DEL_REPOSITORIO>
cd Todoist
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Environment variables

1. Copy `.env.example` to `.env` in the repository root.
2. Fill `.env` with your real values.
3. Do not commit `.env` or paste its values into issues, pull requests,
	notebooks, or logs.

En PowerShell:

```powershell
Copy-Item .env.example .env
notepad .env
```

Available variables:

| Variable | Required for | Description |
| --- | --- | --- |
| `TODOIST_API_TOKEN` | `main.py` and notebooks | Todoist access token. |
| `DIEGO_EMAIL` | daily execution | Report or error recipient. |
| `ECLIPSE_EMAIL` | email notifications | SMTP sender account. |
| `ECLIPSE_APP_PASSWORD` | email notifications | SMTP app password. |
| `OPEN_WEATHER_API_KEY` | weather automation | OpenWeather API key. |
| `AZURE_STORAGE_CONNECTION_STRING` | Liga Pistacho notebook | Optional Azure Storage connection. |

The program loads `.env` automatically through `python-dotenv`. You do not
need to export these variables manually when running from the project root.

## Run the program

With the virtual environment activated:

```powershell
python main.py
```

On Windows, you can also use the interpreter directly:

```powershell
.venv\Scripts\python main.py
```

The daily execution changes Todoist data and may send emails. For a first
test, use a test account or review the method you are going to uncomment
before running it.

## Use the notebooks

Install Jupyter if it is not already available in your environment:

```powershell
python -m pip install jupyter
python -m jupyter notebook
```

Open a notebook from `src/`. The notebooks add the parent folder to
`sys.path` and load the `.env` file from the root. Before running cells that
create, move, or update tasks, check the IDs and filters being used.

## Development

1. Create a working branch based on `dev`.
2. Activate `.venv` and install `requirements.txt`.
3. Make focused changes and keep credentials out of the code.
4. Clear notebook outputs before committing.
5. Check that tokens, passwords, and personal data do not appear in the diff.

You can check script syntax with:

```powershell
python -m py_compile main.py functions.py
```

See `AGENTS.md` for automated-work and collaboration guidelines.

## Security

`.env`, virtual environment folders, and their variants are ignored by Git.
`.env.example` contains only variable names and should be committed.

If a credential is published accidentally, revoke it and generate a new one
immediately. Deleting the file in a later commit does not necessarily remove
the credential from Git history.

## Main structure

```text
.
├── main.py                 # Daily automation entry point
├── functions.py            # Reusable Todoist and email operations
├── requirements.txt        # Pinned Python dependencies
├── .env.example            # Public configuration template
├── src/                    # Notebooks and working data
└── media/                  # Visual assets
```

## CI automation

If `main.py` runs through GitHub Actions, configure the variables as GitHub
Actions Secrets and pass them to the job. Never store their values in the
workflow or repository.
