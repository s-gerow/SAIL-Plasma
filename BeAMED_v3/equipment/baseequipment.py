from abc import ABC, abstractmethod
import logging
import threading

class Equipment(ABC):
    """
    Abstract object with basic methods and attributes to be inherited by specialized children.

    Returns
    -------
    __Equipment__
        Abstract object with basic methods and attributes to be inherited by specialized children.

    Raises
    ------
    NotImplementedError
        Methods not implemented in this class raise a NotImplementedError if called via Equipment.method()
    """
    def __init__(self, name: str, abort_event: threading.Event):
        """
        Initialize and return equipment object

        Parameters
        ----------
        name : str
            String representing the name of the instrument as it will be referenced in dictionaries, logs, and controller calls
        """
        self.name = name
        self.standalone = False
        self.logger = logging.getLogger(f"BeAMED.{name.lower().replace(' ','_')}")
        self._connected: bool
        self._abort = abort_event

    
    @abstractmethod
    def connect(self) -> None: ...
    
    @abstractmethod
    def disconnect(self) -> None: ...

    @abstractmethod
    def getStatus(self) -> dict: ...

    def reset(self):
        """
        If available, implement a reset function such as *RST which clears the communication line and resets the instrument to default settings.

        Raises
        ------
        NotImplementedError
            Equipment.reset() is not implemented at this level.
        """
        raise NotImplementedError(f"{type(self).__name__} does not implement reset()")
        
    def getName(self) -> str:
        """
        Return the name of the instrument.

        Returns
        -------
        str
            Name of the instrument as used in dictionaries, logs, and method calls.
        """
        return self.name
    
    def setName(self, name: str):
        """
        Set the name of the instrument.

        Parameters
        ----------
        name : str
            Name of the instrument as used in dictionaries, logs, and method calls.
        """
        self.name = name

    def isConnected(self):
        return self._connected