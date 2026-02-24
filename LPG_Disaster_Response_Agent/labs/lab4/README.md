# Lab 4 – Agent Communication using FIPA-ACL

This folder contains the code for Lab 4 of the LPG Disaster Response Agent
project.  The goal is to demonstrate coordination between multiple agents
using standard FIPA-ACL performatives (`INFORM`, `REQUEST`, etc.).

## Overview

* **SensorAgent** – polls the simulated LPG station (reused from lab2) and
  classifies hazard severity.  Each cycle the agent sends an `INFORM` message to
the coordinator with the current event (e.g. `GAS_LEAK_CONFIRMED`).  A final
  `SHUTDOWN` inform terminates the simulation.

* **CoordinatorAgent** – listens for sensor informs.  When an abnormal event is
  received it dispatches `REQUEST` messages to a set of response agents.  It
  also logs confirmation informs from responders and propagates a shutdown
  signal when the sensor finishes.

* **ResponseAgent** – waits for requests from the coordinator, simulates
  handling the request, then replies with an `INFORM` confirming completion.  A
  `SHUTDOWN` message causes the agent to stop.

The flow mimics a real emergency system where a central coordinator (e.g. Ghana
National Fire Service) forwards orders to various response units, and those
units acknowledge back.

## Running the Simulation

1. Ensure a local XMPP server is running on `localhost:5222` (the labs assume
   `ejabberd` or similar; you can use the Docker image included in earlier
   labs).

2. From the project root path run:

   ```bash
   python -m labs.lab4.main
   ```

   The script will start a coordinator, two response agents and a sensor.  All
   agents are started with `auto_register=True`, so they will attempt to
   register on the server if the JIDs do not already exist; this is convenient
   for fresh installations.  Watch the console output to see messages being
   exchanged.

3. To stop early press `Ctrl+C`.  The sensor agent automatically issues a
   shutdown after a fixed number of cycles, which cascades to the other
   agents.

## Notes

* Code in this lab imports modules from previous labs (e.g. the `SimulatedLPGStation`)
  to illustrate how earlier work can be reused.
* Performatives and ontologies are set on `spade.message.Message`
  metadata; the behaviour classes use simple `CyclicBehaviour` loops to handle
  incoming messages.

This lab prepares the foundations for more sophisticated multi‑agent
coordination in future exercises.
