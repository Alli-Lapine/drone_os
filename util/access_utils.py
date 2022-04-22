from typing import Optional

from util import hivemap
from util.storage import RegisteredDrone, Storage, get_drone


def has_access(source: RegisteredDrone, target: RegisteredDrone) -> bool:
    """Returns true if `source` is in `target`'s access list"""
    target_al = target.get('access', None)
    if not target_al:
        target['access'] = [target['discordid']]
        Storage.backend.save(target)

    if source['discordid'] in target['access']:
        return True
    elif source['discordid'] == get_drone_hive_owner(target):
        return True
    elif source['discordid'] == 212005474764062732:  # Director
        return True
    else:
        return False


def get_drone_hive_owner(drone: RegisteredDrone) -> Optional[RegisteredDrone]:
    owner_id = hivemap[drone['hive']]['owner']
    drone_owner = get_drone(owner_id)
    return drone_owner


def grant_access(from_drone: RegisteredDrone, to_drone: RegisteredDrone) -> bool:
    """Adds `from_drone`'s discord ID to the access list of `to_drone`"""
    if has_access(from_drone, to_drone):
        return False
    else:
        to_drone['access'].append(from_drone['discordid'])
        Storage.backend.save(to_drone)
        return True


def revoke_access(from_drone: RegisteredDrone, to_drone: RegisteredDrone) -> bool:
    """Removes `from_drone`'s discord ID from the access list of `to_drone`"""
    if not has_access(from_drone, to_drone):
        return False
    else:
        to_drone['access'].remove(from_drone['discordid'])
        Storage.backend.save(to_drone)
        return True


def accesslist_to_dronelist(accesslst: [int]) -> [RegisteredDrone]:
    r = []
    for i in accesslst:
        db_drone = get_drone(i)
        if db_drone:
            r.append(db_drone)
    return r

