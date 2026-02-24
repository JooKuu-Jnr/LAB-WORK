"""Lab 3 - FSM Decision Agent.

Implements reactive behavior using a Finite State Machine to transition between:
Idle -> Alert -> Assessment -> Response -> Completion
"""
from spade.agent import Agent
from spade.behaviour import FSMBehaviour, State
from spade.message import Message
import asyncio

STATE_IDLE = "IdleState"
STATE_ALERT = "AlertState"
STATE_ASSESSMENT = "AssessmentState"
STATE_RESPONSE = "ResponseState"
STATE_COMPLETION = "CompletionState"

class IdleState(State):
    async def run(self):
        msg = await self.receive(timeout=3.0)
        if msg:
            event = msg.body
            if event == "SHUTDOWN":
                print("[FSM] Shutting down.")
                await self.agent.stop()
                return
            
            if event != "NORMAL_CONDITION":
                print(f"\n[FSM] IdleState: Abnormal condition detected! Event received: {event}")
                self.agent.current_event = event
                self.set_next_state(STATE_ALERT)
            else:
                print("[FSM] IdleState: All normal. Monitoring...")
                self.set_next_state(STATE_IDLE)
        else:
            self.set_next_state(STATE_IDLE)

class AlertState(State):
    async def run(self):
        print("[FSM] AlertState: Sounding initial alarms and validating hazard.")
        await asyncio.sleep(0.5) 
        self.set_next_state(STATE_ASSESSMENT)

class AssessmentState(State):
    async def run(self):
        event = self.agent.current_event
        print(f"[FSM] AssessmentState: Assessing severity of {event}...")
        await asyncio.sleep(0.5)
        
        if event in ["GAS_LEAK_CONFIRMED", "CRITICAL_GAS_LEVEL"]:
            print("[FSM] AssessmentState: High risk confirmed! Moving to Response.")
            self.set_next_state(STATE_RESPONSE)
        elif event == "POSSIBLE_GAS_LEAK":
            print("[FSM] AssessmentState: Early warning, no active leak yet. Returning to monitoring.")
            self.set_next_state(STATE_COMPLETION)
        else:
            self.set_next_state(STATE_COMPLETION)

class ResponseState(State):
    async def run(self):
        event = self.agent.current_event
        print(f"[FSM] ResponseState: Executing emergency protocols for {event}!")
        if event == "CRITICAL_GAS_LEVEL":
            print(" ----> EVACUATE STATION! SHUTTING DOWN MAIN VALVES!")
        else:
            print(" ----> ALERTING STAFF! VENTILATION ON.")
        
        await asyncio.sleep(0.5)
        print("[FSM] ResponseState: Emergency protocols engaged.")
        self.set_next_state(STATE_COMPLETION)

class CompletionState(State):
    async def run(self):
        print("[FSM] CompletionState: Incident handled. Resetting systems...")
        self.agent.current_event = None
        await asyncio.sleep(0.5)
        print("-" * 50)
        self.set_next_state(STATE_IDLE)


class DisasterFSMAgent(Agent):
    async def setup(self):
        print(f"[DisasterFSMAgent] Setup complete for {self.jid}")
        self.current_event = None
        
        fsm = FSMBehaviour()
        fsm.add_state(name=STATE_IDLE, state=IdleState(), initial=True)
        fsm.add_state(name=STATE_ALERT, state=AlertState())
        fsm.add_state(name=STATE_ASSESSMENT, state=AssessmentState())
        fsm.add_state(name=STATE_RESPONSE, state=ResponseState())
        fsm.add_state(name=STATE_COMPLETION, state=CompletionState())
        
        fsm.add_transition(source=STATE_IDLE, dest=STATE_IDLE)
        fsm.add_transition(source=STATE_IDLE, dest=STATE_ALERT)
        
        fsm.add_transition(source=STATE_ALERT, dest=STATE_ASSESSMENT)
        
        fsm.add_transition(source=STATE_ASSESSMENT, dest=STATE_RESPONSE)
        fsm.add_transition(source=STATE_ASSESSMENT, dest=STATE_COMPLETION)
        
        fsm.add_transition(source=STATE_RESPONSE, dest=STATE_COMPLETION)
        fsm.add_transition(source=STATE_COMPLETION, dest=STATE_IDLE)
        
        self.add_behaviour(fsm)

async def main():
    agent = DisasterFSMAgent("fsm_agent@localhost", "password")
    await agent.start(auto_register=True)
    
    while agent.is_alive():
        try:
            await asyncio.sleep(1)
        except KeyboardInterrupt:
            break
    await agent.stop()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
