import discord
from typing import Any, Union
import yaml
import os

guilds = []
hivemap = {}
fhivemap = []
filters = {}
config = {}
codes = None


def mkembed(kind: str, description: str, **kwargs) -> discord.Embed:
    """Creates a discordpy Embed with some sane defaults"""
    kindmap = {
        "done": discord.Color.green(),
        "error": discord.Color.red(),
        "info": discord.Color.blue(),
    }
    e = discord.Embed(
        title=kwargs.get("title", None) or kind.capitalize(),
        description=description,
        color=kwargs.get("color", None) or kindmap[kind],
    )
    return e


def update_guilds(guildlist: list):
    global guilds
    guilds = guildlist


def aget(listlike: Union[list, tuple], index: int, default: Any) -> Any:
    """Like .get on Dicts. Returns the item at `index` or `default` if it is out of range. Coded in anger."""
    try:
        return listlike[index]
    except IndexError:
        return default


def load_codes():
    """Populates util.codes with the contents of codes.yml"""
    global codes
    codes = {}
    for codefiles in os.listdir("codes"):
        with open(os.path.join("codes", codefiles), 'r') as f:
            codes.update(yaml.safe_load(f))


def load_hives():
    with open("hives.yml", "r") as f:
        global hivemap
        global fhivemap
        hivemap = yaml.safe_load(f)
        fhivemap = [f"{x}, {hivemap[x]['sym']}" for x in hivemap.keys()]


def load_filters():
    with open("filters.yml", "r") as f:
        global filters
        filters = yaml.safe_load(f)


def load_config():
    with open("config.yml", "r") as f:
        global config
        config = yaml.safe_load(f)
