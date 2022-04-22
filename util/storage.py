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


def get_drone(query: int) -> Optional[RegisteredDrone]:
    if len(str(query)) == 4:
        try:
            db_drone = Storage.backend.get(RegisteredDrone, {'droneid': str(query)})
        except RegisteredDrone.DoesNotExist:
            return None
        return db_drone
    elif len(str(query)) >= 10:
        try:
            db_drone = Storage.backend.get(RegisteredDrone, {'discordid': query})
        except RegisteredDrone.DoesNotExist:
            return None
        return db_drone
    else:
        raise RuntimeError("Invalid drone ID")


def get_channel(query: dict) -> Optional[DroneChannel]:
    try:
        db_drone = Storage.backend.get(DroneChannel, query)
    except DroneChannel.DoesNotExist:
        return None
    else:
        return db_drone
