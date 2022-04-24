from typing import Optional

import discord

from util import mkembed, hivemap
from util.storage import RegisteredDrone, Storage, get_drone


def has_access(source: RegisteredDrone, target: RegisteredDrone) -> bool:
    """Returns true if `source` is in `target`'s access list"""
    target_al = target.get("access", None)
    if not target_al:
        target["access"] = [target["discordid"]]
        Storage.backend.save(target)

    if source["discordid"] in target["access"]:
        return True
    elif source["discordid"] == get_drone_hive_owner(target)["discordid"]:
        return True
    elif source["discordid"] == 212005474764062732:  # Director
        return True
    else:
        return False


def grant_access(from_drone: RegisteredDrone, to_drone: RegisteredDrone) -> bool:
    """Adds `from_drone`'s discord ID to the access list of `to_drone`"""
    if has_access(from_drone, to_drone):
        return False
    else:
        to_drone["access"].append(from_drone["discordid"])
        Storage.backend.save(to_drone)
        return True


def revoke_access(from_drone: RegisteredDrone, to_drone: RegisteredDrone) -> bool:
    """Removes `from_drone`'s discord ID from the access list of `to_drone`"""
    if not has_access(from_drone, to_drone):
        return False
    else:
        to_drone["access"].remove(from_drone["discordid"])
        Storage.backend.save(to_drone)
        return True


def accesslist_to_dronelist(accesslst: [int]) -> [RegisteredDrone]:
    r = []
    for i in accesslst:
        db_drone = get_drone(i)
        if db_drone:
            r.append(db_drone)
    return r


async def get_command_drones(
    operator: int,
    target: int,
    chkaccess: bool = True,
) -> (RegisteredDrone, RegisteredDrone, discord.Embed):
    """Ensures that `operator` and `target` are both registered drones, accepting either a 4 character drone ID or a
    longer Discord ID. Returns an optional Embed in the third position as an error, this should be sent to the invoking
    user and the caller should return early if present. If `chkaccess` is true, also checks that `operator` is in
    `target`'s access list."""
    operator_drone = get_drone(operator)
    if not operator_drone:
        return None, None, mkembed("error", "`You do not appear to be a registered drone.`")
    target_drone = get_drone(target)
    if not target_drone:
        return (
            operator_drone,
            None,
            mkembed("error", f"`{target} does not appear to be a registered drone.`"),
        )
    if chkaccess:
        if not has_access(operator_drone, target_drone):
            return operator_drone, target_drone, mkembed("error", "`Permission denied.`")
    return operator_drone, target_drone, None


def get_drone_hive_owner(drone: RegisteredDrone) -> Optional[RegisteredDrone]:
    owner_id = hivemap[drone["hive"]]["owner"]
    drone_owner = get_drone(owner_id)
    return drone_owner
