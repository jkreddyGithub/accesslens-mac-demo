# AccessLens Entitlement Review Demo

A packaged Mac demo for reviewing synthetic access data. The demo records review
decisions locally and does not change real access.

## MCP-assisted review workflow

The optional Python workflow in [main.py](./main.py) demonstrates how MCP-sourced
identity and risk context can extend an entitlement review. A LangGraph workflow
enriches a review item with a risk score, risk flags, and a manager contact, then
generates an explanation and marks the item as pending human review. The example
prints a simulated reviewer decision and updates the workflow state to
`REVOKED_BY_REVIEWER`.

The current implementation uses **mock MCP data** in `main.py`; it does not
connect to a live MCP server or change access in an identity system. Its
LangGraph checkpoint uses in-memory storage for the duration of the process.
This is a separate prototype from the packaged Java web demo below.

To run the workflow, use Python 3.10 or newer, install the dependencies, and
start it from this folder:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

## Requirements

- Java 17 or newer
- macOS

## Run the demo

From this folder, run:

```sh
java -version
java -jar access-review-demo.jar
```

Keep the terminal open and visit <http://localhost:8080>.

Demo sign-in credentials and alternate-port instructions are in
[START-HERE.txt](./START-HERE.txt).

If port 8080 is already in use, start the app on port 8082:

```sh
java -jar access-review-demo.jar --server.port=8082
```

Then visit <http://localhost:8082>.

## Data and source

Review data is saved locally in the `data` folder, which is intentionally
excluded from this repository. This is a demo build; the complete source and
interview documentation are distributed separately.

Use synthetic data only. Do not use these demo credentials or this application
for production access reviews.
