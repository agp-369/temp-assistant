from abc import ABC, abstractmethod

class Plugin(ABC):
    """
    Base class for all plugins.
    """
    @abstractmethod
    def can_handle(self, command):
        """
        Returns True if the plugin can handle the given command.
        """
        pass

    @abstractmethod
    def handle(self, command, assistant):
        """
        Handles the given command.
        """
        pass
