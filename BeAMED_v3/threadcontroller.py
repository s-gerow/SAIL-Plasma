import threading
import queue
import logging
from typing import Any
from equipment.baseequipment import Equipment
from dataclasses import dataclass, field

@dataclass
class ConnectResult:
    key: str
    success: bool
    error: str = None

@dataclass
class ActionResult:
    key: str
    action: str
    success: bool
    data: dict = field(default_factory=dict)
    error: str = None

@dataclass
class StepResult:
    step_name: str
    success: bool
    data: dict = field(default_factory=dict)
    error: str = None

@dataclass
class SequenceComplete:
    success: bool
    aborted: bool = False


class Controller:
    '''
    Controls sequencing and independent operations of each instrument and information queue
    '''
    def __init__(self):
        self.logger = logging.getLogger("BeAMED.controller")
        self.registry: dict[str, Equipment] = {}
        self.queue: queue.Queue = queue.Queue()
        self.event_abortAll = threading.Event()

    def register(self, key: str, equipment: Equipment):
        '''
        Adds an instrument to the controller registry.
        '''
        self.registry[key] = equipment
        self.logger.info(f"Registered equipment: {key} ({type(equipment).__name__})")

    def get(self, key: str) -> Equipment:
        if key not in self.registry:
            raise KeyError(f"No equipment registered under '{key}")
        return self.registry[key]
    
    def connect_all(self):
        '''
        Connects all registered equipment, assigining each one a custom thread.
        '''
        threads = []
        for key, equipment in self.registry.items():
            t = threading.Thread(target = self._connect_instrument,
                                 args=(key,equipment),
                                 daemon=True
                                 )
            threads.append(t)
            t.start()
        for t in threads:
            t.join(timeout=10)

    def _connect_instrument(self, key:str, equipment: Equipment):
        try:
            self.logger.info(f"Connecting {key}...")
            equipment.connect()
            self.queue.put(ConnectResult(key=key, success=True))
        except Exception as e:
            self.logger.exception(f"Failed to connect {key}")
            self.queue.put(ConnectResult(key=key, success=False, error=str(e)))

    def disconnect_all(self):
        for key, equipment in self.registry.items():
            self._disconnect_instrument(key,equipment)

    def _disconnect_instrument(self, key: str, equipment: Equipment):
        try:
            equipment.disconnect()
            self.logger.info(f"Disconnected {key}")
        except Exception as e:
            self.logger.exception(f"Error disconnecting {key}")

    def run(self, action: str, target: str, method: str, **kwargs):
        '''
        Calls equipment action on a thread
        '''
        threading.Thread(target = self._run,
                         args=(action, target, method),
                         kwargs=kwargs,
                         daemon=True).start()
        
    def _run(self, action: str, target: str, method: str, **kwargs):
        try:
            equipment = self.get(target)
            result = getattr(equipment, method)(**kwargs)
            self.result_queue.put(ActionResult(
                key = target,
                action=action,
                success = True,
                data={"result":result}
            ))
        except Exception as e:
            self.logger.exception(f"Action '{action}' failed")
            self.queue.put(ActionResult(
                key = target,
                action=action,
                success = False,
                error = str(e)
            ))

    def shutdown(self):
        self.logger.info("Shutting down. Closing all open threads...")
        self.event_abortAll.set()
        self.disconnect_all()