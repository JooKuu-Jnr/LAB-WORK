"""Entrypoint for Lab 3: Start Sensor Agent and FSM Agent."""
import asyncio
import sys
from pathlib import Path

# Need to properly resolve paths to allow importing agents
_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

# Now we can import the agents
from labs.lab3_fsm.agents.sensor_agent import SensorAgent
from labs.lab3_fsm.agents.fsm_agent import DisasterFSMAgent

async def main():
    print("=" * 60)
    print("Lab 3: FSM Agent Simulation Started")
    print("=" * 60)

    # 1. Start FSM Agent
    fsm_agent = DisasterFSMAgent("fsm_agent@localhost", "password")
    await fsm_agent.start(auto_register=True)
    print("FSM Agent started.")
    
    # 2. Start Sensor Agent
    sensor_agent = SensorAgent(
        jid="sensor_agent@localhost", 
        password="password", 
        target_jid="fsm_agent@localhost"
    )
    await sensor_agent.start(auto_register=True)
    print("Sensor Agent started.\n")
    
    try:
        while sensor_agent.is_alive() and fsm_agent.is_alive():
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping agents...")
    finally:
        if sensor_agent.is_alive():
            await sensor_agent.stop()
        if fsm_agent.is_alive():
            await fsm_agent.stop()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(main())
