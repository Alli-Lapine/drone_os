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
