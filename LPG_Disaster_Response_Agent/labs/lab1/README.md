# Intelligent LPG Leak Detection and Disaster Response Multi-Agent System (Lab 1)

This Lab 1 workspace sets up the development environment and a basic SPADE agent platform for the project.

## Project Structure

```text
labs/lab1/
├── agents/
│   └── basic_agent.py
├── logs/
├── reports/
│   └── lab1_environment_setup_report.md
├── requirements.txt
└── README.md
```

## Install Requirements

From the Lab 1 root (`LPG_Disaster_Response_Agent/labs/lab1`):

```bash
pip install -r requirements.txt
```

## Run the Basic Agent

Ensure your local XMPP server is running and reachable at `localhost`.

Run from the Lab 1 root:

```bash
python agents/basic_agent.py
```

Expected result:

- the agent connects,
- prints startup and behaviour messages,
- executes one simple behaviour,
- shuts down cleanly.
