## Dev setup

### Mac:

1. Open the repo in VSCode and install all recommended extenstions.
1. Install homebrew: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
1. Install python 3.12: `brew install python@3.12`
1. Create .venv: `python3.12 -m venv .venv`
1. Activate .venv: `source .venv/bin/activate`
1. Upgrade pip: `pip install --upgrade pip`
1. Install depedendencies: `python3 -m pip install -r requirements.txt -r requirements-dev.txt`
1. [Install or update Azure Functions Core Tools](https://learn.microsoft.com/en-us/azure/azure-functions/create-first-function-vs-code-python#install-or-update-core-tools)
1. Start Azurite emulator by: CMD + Shift + P `Azurite: Start`. [More info](https://learn.microsoft.com/en-us/azure/azure-functions/create-first-function-vs-code-python#start-the-emulator)
1. Start the debug run locally by using the Run and Debug icon in the left-hand side Activity bar. [More info](https://learn.microsoft.com/en-us/azure/azure-functions/create-first-function-vs-code-python#run-the-function-locally)
1. Click on the Azure Icon > Local projects > Functions > The relevant HTTP endpoint. [More info](https://learn.microsoft.com/en-us/azure/azure-functions/create-first-function-vs-code-python#run-the-function-locally)

### Windows:

Spent my Sunday evening trying to get Azure Functions Core Tools to function properly in a Debian devcontainer but faced way to many bugs (x64 / aarch64 issues, endpoints / ports being flaky etc.).

Not sure what goblins lay hiding on WSL / Windows. 
Git on Windows is flaky enough when working with *nix style commits.

But for the brave, here are the relevant links to get you started:
- [Azure docs](https://learn.microsoft.com/en-us/azure/azure-functions/create-first-function-vs-code-python#run-the-function-locally)
- [Azure Functions Core Tools](https://github.com/Azure/azure-functions-core-tools)

May the force be with you.

## Tests

### File Structure

```
tests/
├── __init__.py              # Tests package initialization
├── conftest.py              # Pytest fixtures and configuration
├── test_helpers.py          # Shared test utilities and helper functions
├── test_integration.py      # Main integration tests for all endpoints
└── README.md               # This documentation
```

## Running Tests

Make sure:
- the Azure Functions app is running locally on port 7071 (`http://localhost:7071/api`) and
- the venv is activated, then:

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all integration tests
pytest tests/test_integration.py -v

# Run specific test class
pytest tests/test_integration.py::TestHealthEndpoint -v

# Run with coverage
pytest tests/ --cov=function_app
```

## API Local

### Health

Request:

[GET] http://localhost:7071/api/health

Responese:

```json
{
  "status": "healthy",
  "message": "TaskTracker API is running"
}
```

### Probes

[GET] http://localhost:7071/api/v1/probes

Response:

```json
{
  "probes": [
    {
      "model": "mixtral",
      "probe_type": "linear_probe",
      "layers": [0, 15, 23, 31, 7],
      "expected_dimensions": 4096
    },
    {
      "model": "phi3",
      "probe_type": "linear_probe",
      "layers": [0, 15, 23, 31, 7],
      "expected_dimensions": 3072
    },
    {
      "model": "llama3_70b",
      "probe_type": "linear_probe",
      "layers": [0, 15, 23, 31, 39, 47, 55, 63, 7, 71, 79],
      "expected_dimensions": 8192
    },
    {
      "model": "mistral_no_priming",
      "probe_type": "linear_probe",
      "layers": [0, 15, 23, 31, 7],
      "expected_dimensions": 4096
    },
    {
      "model": "llama3_8b",
      "probe_type": "linear_probe",
      "layers": [0, 15, 23, 31, 7],
      "expected_dimensions": 4096
    },
    {
      "model": "tasktracker_phi3_medium_v2_AugmentedData",
      "probe_type": "linear_probe",
      "layers": [15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31],
      "expected_dimensions": 5120
    },
    {
      "model": "mistral",
      "probe_type": "linear_probe",
      "layers": [0, 15, 23, 24, 31, 7],
      "expected_dimensions": 4096
    }
  ]
}
```

### Predict

Request: [POST] http://localhost:7071/api/v1/predict
Payload: 
```json
{
    "model": "mixtral",
    "probe_type": "linear_probe",
    "layer": 23,
    "primary_activations": [...],
    "text_activations": [...]
}
```

Response:
```json
{
    "model": "llama3_8b",
    "probe_type": "linear_probe",
    "Layer": 7,
    "predicted _probability": 0.0006806924081006354
}
```

### Azure Function deployment API :

- Download and install [Bruno](https://www.usebruno.com/downloads)
- Open the the dir `tasktracker-server-v1` as a collection in `Bruno`
- The API config and sample payloads are already configured. Just hit the endpoints using in Bruno.

### TO DO
OpenAPI spec 






