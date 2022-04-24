import re

import discord
from typing import Optional, List

from util import aget, codes
from util.storage import RegisteredDrone


async def reply_builder(msg: discord.Message) -> Optional[discord.Embed]:
    """Returns a formatted embed if `msg` contains a reference to another message, otherwise None."""
    # TODO: This may break on pins or other types of references.
    if msg.reference:
        rmsg = msg.reference.resolved
        reply_embed = discord.Embed(
            color=discord.Color.green(), description=f"[Reply to]({rmsg.jump_url}): {rmsg.content}"
        ).set_author(
            # Webhook bot messages are Users rather than Members and have no nick
            name=rmsg.author.nick if isinstance(rmsg.author, discord.Member) else rmsg.author.name,
            icon_url=msg.reference.resolved.author.avatar.url,
        )
    else:
        reply_embed = None
    return reply_embed


async def get_drone_webhook(channel: discord.channel) -> Optional[discord.Webhook]:
    """Returns the 'Drone speech optimization' webhook for `channel` if it exists, otherwise None."""
    hooks = await channel.webhooks()
    if not hooks:
        return None

    for h in hooks:
        if h.name == "Drone speech optimization":
            return h

    return None


def _get_emojis(msg: discord.Message) -> List[dict]:
    content = msg.content
    res = re.finditer(r"<(?P<animated>a)?:(?P<name>\w+):(?P<snowflake>\d+)>", content)
    if not res:
        return []
    emos = []
    for r in res:
        rd = r.groupdict()
        ext = "gif" if rd.get("animated") else "png"
        emo = {
            "name": rd["name"],
            "id": rd["snowflake"],
            "url": f"https://cdn.discordapp.com/emojis/{rd['snowflake']}.{ext}",
            "data": None,
            "animated": rd.get("animated"),
        }
        emos.append(emo)
    return emos


def _format_emoji(emo: dict) -> str:
    return f"<{'a' if emo['animated'] else ''}:{emo['name']}:{emo['id']}> "


def format_code(content: str, drone: RegisteredDrone) -> (Optional[str], Optional[str]):
    """Given a drone and its message content, return a nicely formatted status code block and the status code used"""
    if drone:
        c = aget(re.findall(r"^(.{3,4})(.*)$", content), 0, None)
        if c:
            if c[0] in codes.keys():
                return f"Code {c[0]} :: {codes[c[0]]}", c[0]
    return None, None
