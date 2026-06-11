from abc import ABC, abstractmethod
import logging

class Equipment(ABC):
    '''
    Abstract class designed to be developed into different ways to access a device. Includes key attributes and methods that all devices should have such as an identifier,
    query, write, open, and close functions.
    can be used by a controller or standalone in a GUI or from the terminal
    '''
    def __init__(self, name: str):
        self.name = name
        self.standalone = False
        self.logger = logging.getLogger(f"BeAMED.{name.lower().replace(' ','_')}")

    
    @abstractmethod
    def connect(self) -> None: ...
    
    @abstractmethod
    def disconnect(self) -> None: ...

    @abstractmethod
    def getStatus(self) -> dict: ...

    def reset(self):
        '''
        Override if device supports *RST or equivalent
        '''
        raise NotImplementedError(f"{type(self).__name__} does not implement reset()")
        
    def getName(self):
        return self.name
    
    def setName(self, name: str):
        self.name = name