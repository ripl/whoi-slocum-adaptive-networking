import json
import time
from abc import abstractmethod
from collections import Callable, defaultdict
from typing import Set, Dict

import yaml
from pydantic import BaseModel

from ..exceptions import InvalidStateError


class GenericModel(BaseModel):
    class Config:
        underscore_attrs_are_private = True
        use_enum_values = True

    def as_json(self) -> str:
        return self.json(sort_keys=True, indent=4)

    def as_yaml(self) -> str:
        return yaml.safe_dump(json.loads(self.as_json()), sort_keys=True, indent=4)

    @abstractmethod
    def report(self) -> dict:
        pass


class Shuttable:
    _shuttables: Dict[int, Set['Shuttable']] = defaultdict(set)

    def __init__(self, priority: int = 0):
        self._is_shutdown: bool = False
        self._callbacks: Set[Callable] = set()
        # keep track of all shuttables
        Shuttable._shuttables[priority].add(self)

    @property
    def is_shutdown(self) -> bool:
        return self._is_shutdown

    def register_shutdown_callback(self, cb: Callable):
        if self.is_shutdown:
            classes = [cls.__name__ for cls in type(self).__class__.__subclasses__()]
            raise InvalidStateError(f"Object of type {classes} received a request to register "
                                    f"a new shutdown callback but the instance was already "
                                    f"shutdown.")
        self._callbacks.add(cb)

    def join(self, nap_duration: float = 0.25) -> None:
        """
        Blocks until this Shuttable is shut down.

        :param nap_duration: how often (in seconds) we wake up and check for change in status
        """
        try:
            while not self.is_shutdown:
                time.sleep(nap_duration)
        except KeyboardInterrupt:
            print("Received a Keyboard Interrupt, exiting...")
            Shuttable.shutdown_all()

    def mark_as_shutdown(self):
        self._is_shutdown = True

    def shutdown(self):
        was_shutdown = self.is_shutdown
        # mark as shutdown
        self.mark_as_shutdown()
        # notify callbacks
        if not was_shutdown:
            for cb in self._callbacks:
                cb()

    @classmethod
    def shutdown_all(cls):
        for priority in sorted(cls._shuttables.keys(), reverse=True):
            for shuttable in cls._shuttables[priority]:
                shuttable.shutdown()


class Reminder:

    def __init__(self, period=None, frequency=None):
        self._period = Reminder._get_period(period, frequency)
        self._last_execution = time.time()

    def reset(self):
        self._last_execution = time.time()

    def is_time(self, period=None, frequency=None, dry_run=False):
        _period = self._period
        # use provided period/frequency (if any)
        if period is not None or frequency is not None:
            _period = Reminder._get_period(period, frequency)
        # ---
        _is_time = (time.time() - self._last_execution) >= _period
        if _is_time and not dry_run:
            self.reset()
        return _is_time

    @staticmethod
    def _get_period(period=None, frequency=None):
        # period or frequency has to be given
        if period is None and frequency is None:
            raise ValueError('When you construct an object of type Reminder you need '
                             'to provide either a `period` or a `frequency`.')
        # period and frequency cannot be set at the same time
        if period is not None and frequency is not None:
            raise ValueError('When you construct an object of type Reminder you need '
                             'to provide either a `period` or a `frequency`, not both.')
        # get period
        _period = 0
        if period is not None:
            if not isinstance(period, (int, float)):
                raise ValueError('Parameter `period` must be a number, got {:s} instead'.format(
                    str(type(period))
                ))
            _period = period
        if frequency is not None:
            if not isinstance(frequency, (int, float)):
                raise ValueError('Parameter `frequency` must be a number, got {:s} instead'.format(
                    str(type(frequency))
                ))
            _period = 1.0 / frequency
        # ---
        return _period
