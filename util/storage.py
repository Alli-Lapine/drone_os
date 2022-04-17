from typing import Optional
from blitzdb import Document, FileBackend


class RegisteredDrone(Document):
    pass


class DroneChannel(Document):
    pass


class _StorageBackend:
    def __init__(self):
        self.backend = FileBackend('db')
        self.backend.autocommit = True


Storage = _StorageBackend()


def get_drone(query: dict) -> Optional[RegisteredDrone]:
    try:
        db_drone = Storage.backend.get(RegisteredDrone, query)
    except RegisteredDrone.DoesNotExist:
        return None
    else:
        return db_drone


def get_channel(query: dict) -> Optional[DroneChannel]:
    try:
        db_drone = Storage.backend.get(DroneChannel, query)
    except DroneChannel.DoesNotExist:
        return None
    else:
        return db_drone
