import discord
from typing import Any
import yaml

guilds = []
hivemap = {
    'lapine/unaffiliated': '☼',
    'mndlos': '⍔',
    'xantronix': '⚹',
    'heartthrob': '♥',
    'hexcorp': '⬡'
}
codes = None


def mkembed(kind: str, description: str, **kwargs) -> discord.Embed:
    """Creates a discordpy Embed with some sane defaults"""
    kindmap = {'done': discord.Color.green(), 'error': discord.Color.red(), 'info': discord.Color.blue()}
    e = discord.Embed(
        title=kwargs.get('title', None) or kind.capitalize(),
        description=description,
        color=kwargs.get('color', None) or kindmap[kind]
    )
    return e


def update_guilds(guildlist: list):
    global guilds
    guilds = guildlist


def aget(lst: list, index: int, default: Any) -> Any:
    try:
        return lst[index]
    except IndexError:
        return default


def load_codes():
    '''Populates util.codes with the contents of codes.yml'''
    with open('codes.yml', 'r') as f:
        global codes
        codes = yaml.safe_load(f)