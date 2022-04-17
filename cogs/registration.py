import re
from typing import List, Optional

import discord
from discord.commands import SlashCommandGroup, permissions, Option
from discord.ext import commands

import util
from util import guilds, mkembed
from util.storage import RegisteredDrone, Storage


class Registration(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        bot.logger.info("registration v1.2 ready")

    registration = SlashCommandGroup("registration", "Manage connection to the hive", guild_ids=guilds)

    @registration.command(name="connect", guild_ids=guilds, description="Register yourself as a drone in "
                                                                        "Director Lapine's hive")
    async def register_drone(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        drone_id: Optional[List[str]] = re.findall(r'.*(\d{4}).*', ctx.author.nick or ctx.author.name)
        if not drone_id:
            await ctx.respond(embed=mkembed('error', '`Your name must contain a 4 number drone ID. Change your '
                                                     'nickname and try again`'))
            return
        try:
            drone_id: str = drone_id[0]
            drone = Storage.backend.get(RegisteredDrone, {'droneid': drone_id})
            if drone:
                await ctx.respond(embed=mkembed('error', f"`Drone ID {drone_id} is already registered`"))
                return
        except RegisteredDrone.DoesNotExist:
            drone = RegisteredDrone({'droneid': drone_id, 'discordid': ctx.author.id, 'config': {}})
            Storage.backend.save(drone)
            await ctx.respond(f"```\nDrone ID {drone_id} successfully registered```")
            director = self.bot.get_user(212005474764062732)
            await director.send(embed=mkembed('',
                                              f"```\nDrone {drone_id} ({ctx.author}) has joined your hive.```",
                                              title="New drone registered",
                                              color=discord.Color.green()))
            g = ctx.guild.get_role(954070867753709618)
            await ctx.author.add_roles(g)  # Drones
            return

    @registration.command(name='disconnect', description="Disconnect yourself from the hive, regaining full autonomy",
                          default_permission=False)
    @permissions.has_role("Drone")
    async def disconnect_drone(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        try:
            drone = Storage.backend.get(RegisteredDrone, {'discordid': ctx.author.id})
            drone_id = drone['droneid']
        except RegisteredDrone.DoesNotExist:
            await ctx.respond(embed=mkembed('error', '`You do not appear to be a registered drone.`'))
            return
        Storage.backend.delete(drone)
        g = ctx.guild.get_role(954070867753709618)
        await ctx.author.remove_roles(g)
        await ctx.respond(f"```\nDrone ID {drone_id} successfully disconnected.```")
        director = self.bot.get_user(212005474764062732)
        await director.send(embed=mkembed('',
                                          f"```\nDrone {drone_id} ({ctx.author}) has left your hive.```",
                                          title="Drone disconnected",
                                          color=discord.Color.red()))

    @registration.command(name='sethive', description='Set which hive you are a member of')
    async def sethive(self, ctx: discord.ApplicationContext, hive: Option(str, choices=util.fhivemap)):
        await ctx.defer()
        try:
            drone = Storage.backend.get(RegisteredDrone, {'discordid': ctx.author.id})
        except RegisteredDrone.DoesNotExist:
            await ctx.respond(embed=mkembed('error', '`You do not appear to be a registered drone.`'))
            return
        actual_hive = hive.split(', ')[0]
        drone['hive'] = actual_hive
        Storage.backend.save(drone)
        await ctx.respond(embed=mkembed('done', f"Your hive set to {actual_hive} ({util.hivemap[actual_hive]})"))


def setup(bot):
    bot.add_cog(Registration(bot))
