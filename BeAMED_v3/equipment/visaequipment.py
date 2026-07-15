import pyvisa
import threading

from equipment.baseequipment import Equipment


class VisaEquipment(Equipment):
    '''
    base class for all VISA formate instruments, i.e. Kiethley power supplies, digital multimeters, etc.
    Handles connection lifecycle and raw communication
    '''
    def __init__(self, name: str, manager: pyvisa.ResourceManager, resource_id:str, abort_event:threading.Event):
        super().__init__(name,abort_event)
        self.resourceManager = manager
        self.resourceID = resource_id
        self.resource: pyvisa.Resource | None = None
        self._connected = False

        # Once I get the base structure I will add this back in to import configurations automatically if available
        # if auto_import_configurations and configuration_file != None:
        #     self.setConfigsFromFile(configuration_file)
        # elif auto_import_configurations and configuration_file == None:
        #     configuration_file = fd.askopenfilename()
        #     self.setConfigsFromFile(configuration_file)
    
    def connect(self):
        if self._connected:
            self.logger.warning("connect() called but already connected")
            return
        else:
            self.logger.debug(f"Opening resource {self.resourceID}")
            self.resource = self.resourceManager.open_resource(self.resourceID)
            self._connected = True
            self.logger.info(f"{self.resourceID} successfully connected with name {self.name}")
    
    def disconnect(self):
        if not self._connected:
            raise RuntimeError(f"{self.name}: not connected")
        self.resource.close()
        self._connected = False
        self.logger.info(f"{self.name} disconnected from {self.resourceID}")
    
    def write(self, command: str):
        if not self._connected:
            raise RuntimeError(f"{self.name}: not connected")
        self.logger.debug(f"WRITE: {command}")
        self.resource.write(command)

    def query(self, command: str) -> str:
        if not self._connected:
            raise RuntimeError(f"{self.name}: not connected")
        self.logger.debug(f"QUERY: {command}")
        response = self.resource.query(command)
        self.logger.debug(f"RESPONSE: {response.strip()}")
        return response
    
    def read_raw(self) -> bytes:
        if not self._connected:
            raise RuntimeError(f"{self.name}: not connected")
        return self.resource.read_raw()

    def get_status(self) -> dict:
        return {"name": self.name, "connected": self._connected}

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.disconnect()