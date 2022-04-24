import discord
from discord.commands import SlashCommandGroup, ApplicationContext, Option
from discord.ext import commands, tasks

from util import guilds, mkembed
from util.access_utils import get_command_drones
from util.storage import get_channel, DroneChannel, RegisteredDrone, Storage
from util.filter_utils import get_drone_webhook
from datetime import datetime


class Locks(commands.Cog):
    locksgrp = SlashCommandGroup(name="lock", description="Restriction management", guild_ids=guilds)

    def __init__(self, bot):
        self.bot = bot
        bot.logger.info("locks v1.0 ready")

    @locksgrp.command(
        name="prefix-on", description="Lock the specified drone into prefix chat", guild_ids=guilds
    )
    async def lock_drone(
        self,
        ctx: ApplicationContext,
        droneid: Option(
            str, description="The drone ID being locked (yourself if blank)", required=False
        ),
        duration: Option(float, description="Seconds to set this lock for", required=False),
    ):
        await ctx.defer(ephemeral=True)
        operator, target, error = await get_command_drones(ctx.author.id, droneid or ctx.author.id)
        if error:
            await ctx.respond(embed=error)
            return None

        if duration:
            locktime = datetime.now().timestamp() + duration
        else:
            locktime = None

        if target.get("config"):
            target["config"]["enforce"] = locktime or True
        else:
            target["config"] = {}
            target["config"]["enforce"] = locktime or True
        Storage.backend.save(target)
        msgtime = f" for {duration} seconds" if duration else ""
        await ctx.respond(
            embed=mkembed(
                "done", f'`Drone {target["droneid"]} prefix chat has been locked{msgtime}.`'
            )
        )
        return

    @locksgrp.command(
        name="prefix-off",
        description="Unlock the specified drone's prefix requirement",
        guild_ids=guilds,
    )
    async def unlock_drone(
        self,
        ctx: ApplicationContext,
        droneid: Option(
            str, description="The drone ID being unlocked (yourself if blank)", required=False
        ),
    ):
        await ctx.defer()
        operator, target, error = await get_command_drones(ctx.author.id, droneid or ctx.author.id)
        if error:
            await ctx.respond(embed=error)
            return
        if target.get("config"):
            target["config"]["enforce"] = False
        else:
            target["config"] = {}
            target["config"]["enforce"] = False
        Storage.backend.save(target)
        await ctx.respond(
            embed=mkembed("done", f'`Drone {target["droneid"]} prefix mode unlocked.`')
        )
        return

    @locksgrp.command(
        name="prefix-channel-on",
        description="Lock prefix chat in the given channel",
        guild_ids=guilds,
    )
    async def lock_channel(
        self,
        ctx: ApplicationContext,
        lockall: Option(bool, description="Allow ONLY drones to speak", default=False),
        channel: Option(discord.TextChannel, required=False),
    ):
        await ctx.defer()
        chan = channel or ctx.channel
        db_chan = get_channel({"discordid": chan.id})
        if not db_chan:
            if not await get_drone_webhook(chan):
                await ctx.respond(
                    embed=mkembed("error", f"Speech optimizations not active in {chan.mention}")
                )
                return
            else:
                db_chan = DroneChannel({"discordid": chan.id})
        lockmode = "enforceall" if lockall else "enforcedrones"
        db_chan["config"] = {lockmode: True}
        Storage.backend.save(db_chan)
        await ctx.respond(
            embed=mkembed(
                "done",
                f'Speech optimizations locked for {"EVERYONE" if lockall else "drones"} in {chan.mention}',
            )
        )

    @locksgrp.command(
        name="prefix-channel-off",
        description="Unlock prefix chat in the given channel",
        guild_ids=guilds,
    )
    async def unlock_channel(
        self, ctx: ApplicationContext, channel: Option(discord.TextChannel, required=False)
    ):
        await ctx.defer()
        chan = channel or ctx.channel
        db_chan = get_channel({"discordid": chan.id})
        if not db_chan:
            await ctx.respond(
                embed=mkembed("error", f"Speech optimizations not locked in {chan.mention}")
            )
            return
        db_chan["config"] = {}
        Storage.backend.save(db_chan)
        await ctx.respond(embed=mkembed("done", f"Speech optimizations unlocked in {chan.mention}"))

    @tasks.loop(seconds=5)
    async def check_locks(self):
        now = datetime.now().timestamp()
        db_drones = Storage.backend.filter(RegisteredDrone, {"config.enforce": {"$gt": now}}) or []
        for d in db_drones:
            self.bot.logger.info(f"Cleared timer.. {d.droneid}")
            d["config"]["enforce"] = False
            Storage.backend.save(d)
            continue

        db_chans = (
            Storage.backend.filter(
                DroneChannel,
                {
                    "$or": [
                        {"config.enforcedrones": {"$gt": now}},
                        {"config.enforceall": {"$gt": now}},
                    ]
                },
            )
            or []
        )
        for c in db_chans:
            c.config.enforcedrones = False
            c.config.enforceall = False
            Storage.backend.save(c)
            continue


def setup(bot):
    bot.add_cog(Locks(bot))
