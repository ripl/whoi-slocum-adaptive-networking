from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional


class QueueType(Enum):
    PERSISTENT = "persistent"
    CACHE = "cache"


class IQueue(ABC):

    def __init__(self, type: QueueType, channel: str):
        self._type: QueueType = type
        self._channel: str = channel

    @abstractmethod
    def put(self, data: bytes):
        pass

    @abstractmethod
    def get(self, block: bool = True) -> Optional[bytes]:
        pass
