import re

import discord
from discord.commands import SlashCommandGroup, permissions, Option, ApplicationContext
from discord.ext import commands

from util import guilds, mkembed, hivemap, aget
from util.filter_utils import reply_builder, get_drone_webhook, format_code
from util.storage import RegisteredDrone, Storage, DroneChannel


class Filter(commands.Cog):
    filtergrp = SlashCommandGroup(name="dronespeech", description="Drone speech optimizations", guild_ids=guilds)

    def __init__(self, bot):
        self.bot = bot
        bot.logger.info("filter v2.9.3 ready")

    @filtergrp.command(name="enable_here", description="Allow automatic drone speech optimizations in this channel",
                       guild_ids=guilds, default_permission=False, permissions=[permissions.has_role('Director')])
    async def enable_here(self, ctx: ApplicationContext):
        await ctx.defer()
        if await get_drone_webhook(ctx.channel):
            await ctx.respond(
                embed=mkembed('error', f"```Drone speech optimizations already active in {ctx.channel.name}```"))
            return
        else:
            await ctx.channel.create_webhook(name="Drone speech optimization", reason=f"enabled by {ctx.author.name}")
            await ctx.respond(
                embed=mkembed('done', description=f"```Drone speech optimizations activated in {ctx.channel.name}```"))
            return

    @filtergrp.command(name="disable_here", description="Disable automatic drone speech optimizations in this channel",
                       guild_ids=guilds)
    async def disable_here(self, ctx: ApplicationContext):
        await ctx.defer()
        h = await get_drone_webhook(ctx.channel)
        if h:
            await h.delete(reason=f"disabled by {ctx.author.name}")
            await ctx.respond(
                embed=mkembed('done',
                              description=f"```Drone speech optimizations deactivated in {ctx.channel.name}```"))
            return
        else:
            await ctx.respond(
                embed=mkembed('error', f"```Drone speech optimizations not active in {ctx.channel.name}```"))
            return

    @filtergrp.command(name='lock_drone', description="Lock the specified drone into speech optimizations, or yourself if no ID given", guild_ids=guilds)
    async def lock_drone(self, ctx: ApplicationContext, droneid: Option(str, "Drone ID", required=False)):
        if not droneid:
            await ctx.defer(ephemeral=True)
            try:
                d: RegisteredDrone = Storage.backend.get(RegisteredDrone, {'discordid': ctx.author.id})
            except RegisteredDrone.DoesNotExist:
                await ctx.respond(embed=mkembed('error', '`You do not appear to be a registered drone.`'))
                return
        else:
            await ctx.defer()
            try:
                d: RegisteredDrone = Storage.backend.get(RegisteredDrone, {'droneid': droneid})
            except RegisteredDrone.DoesNotExist:
                await ctx.respond(embed=mkembed('error', f'`{droneid} does not appear to be a registered drone.`'))
                return

        if d.get('config'):
            d['config']['enforce'] = True
        else:
            d['config'] = {}
            d['config']['enforce'] = True
        Storage.backend.save(d)
        await ctx.respond(embed=mkembed('done', f'`Drone {d["droneid"]} speech optimizations have been locked.`'))
        return

    @filtergrp.command(name='unlock_drone', description="Unlock the specified drone's speech optimizations, or yourself if no ID given", guild_ids=guilds)
    async def unlock_drone(self, ctx: ApplicationContext, droneid: Option(str, "Drone ID", required=False)):
        if not droneid:
            await ctx.defer(ephemeral=True)
            try:
                d: RegisteredDrone = Storage.backend.get(RegisteredDrone, {'discordid': ctx.author.id})
            except RegisteredDrone.DoesNotExist:
                await ctx.respond(embed=mkembed('error', '`You do not appear to be a registered dro ne.`'))
                return
        else:
            await ctx.defer()
            try:
                d: RegisteredDrone = Storage.backend.get(RegisteredDrone, {'droneid': droneid})
            except RegisteredDrone.DoesNotExist:
                await ctx.respond(embed=mkembed('error', f'`{droneid} does not appear to be a registered drone.`'))
                return

        if d.get('config'):
            d['config']['enforce'] = False
        else:
            d['config'] = {}
            d['config']['enforce'] = False
        Storage.backend.save(d)
        await ctx.respond(embed=mkembed('done', f'`Drone {d["droneid"]} speech optimizations have been unlocked.`'))
        return

    @filtergrp.command(name='lock_channel', description="Lock drone speech optimizations in the given channel, or this channel if no ID given", guild_ids=guilds)
    async def lock_channel(self, ctx: ApplicationContext,
                           lockall: Option(bool, description='Allow ONLY drones to speak', default=False),
                           channel: Option(discord.TextChannel, required=False)):
        await ctx.defer()
        chan = channel or ctx.channel
        try:
            c: DroneChannel = Storage.backend.get(DroneChannel, {'discordid': chan.id})
        except DroneChannel.DoesNotExist:
            if not await get_drone_webhook(chan):
                await ctx.respond(embed=mkembed('error', f'Speech optimizations not active in {chan.mention}'))
                return
            else:
                c = DroneChannel({'discordid': chan.id})
        lockmode = 'enforceall' if lockall else 'enforcedrones'
        c['config'] = {lockmode: True}
        Storage.backend.save(c)
        await ctx.respond(embed=mkembed('done', f'Speech optimizations locked for {"EVERYONE" if lockall else "drones"} in {chan.mention}'))

    @filtergrp.command(name='unlock_channel', description="Unlock drone speech optimizations in the given channel, or this channel if no ID given", guild_ids=guilds)
    async def lock_channel(self, ctx: ApplicationContext,
                           channel: Option(discord.TextChannel, required=False)):
        await ctx.defer()
        chan = channel or ctx.channel
        try:
            c: DroneChannel = Storage.backend.get(DroneChannel, {'discordid': chan.id})
        except DroneChannel.DoesNotExist:
            await ctx.respond(embed=mkembed('error', f'Speech optimizations not locked in {chan.mention}'))
            return
        c['config'] = {}
        Storage.backend.save(c)
        await ctx.respond(embed=mkembed('done', f'Speech optimizations unlocked in {chan.mention}'))

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if not msg.content:
            return
        if msg.author.bot:
            return
        h = await get_drone_webhook(msg.channel)
        if h:
            await self.drone_filter_handler(msg, h)

    async def drone_filter_handler(self, msg: discord.Message, hook: discord.Webhook):
        attempted_chat = aget(re.findall(r'^(\d{4}) :: (.*)', msg.content), 0, [])
        attempted_droneid = aget(attempted_chat, 0, None)
        attempted_content = aget(attempted_chat, 1, None)

        try:
            db_drone = Storage.backend.get(RegisteredDrone, {'discordid': msg.author.id})
        except RegisteredDrone.DoesNotExist:
            db_drone = None

        if attempted_droneid and not attempted_content:
            # Malformed attempt, yeet it.
            self.bot.logger.info(f"Malformed delete: {msg}")
            await msg.delete()
            return

        # Is the channel locked to enforce mode?
        try:
            db_channel = Storage.backend.get(DroneChannel, {'discordid': msg.channel.id})
        except DroneChannel.DoesNotExist:
            db_channel = {}
        chan_conf = db_channel.get('config', {})
        if chan_conf.get('enforcedrones'):  # All registered drones must use speech opt
            if db_drone:
                if not attempted_droneid and not attempted_content:
                    self.bot.logger.info(f"Chan enforcedrone delete: {msg}")
                    await msg.delete()
                    return
                else:
                    await self.send_as_drone(db_drone, hook, msg)
                    await msg.delete()
                    return

        if chan_conf.get('enforceall'):
            if not attempted_droneid:  # Only drones may speak
                self.bot.logger.info(f"Chan Enforceall delete: {msg}")
                await msg.delete()
                return

        # If a non-drone uses a prefix, just bail.
        if not db_drone:
            return

        # Is the drone locked to enforce mode?
        drone_conf = db_drone.get('config', {})
        if drone_conf.get('enforce'):
            if not attempted_droneid and not attempted_content:
                self.bot.logger.info(f"Drone enforce delete: {msg}")
                await msg.delete()
                return
            else:
                await self.send_as_drone(db_drone, hook, msg)
                await msg.delete()
                return

        if not attempted_droneid:
            return

        # Is the drone using their own prefix?
        if attempted_droneid and db_drone['droneid'] != attempted_droneid:
            self.bot.logger.info(f"Wrong prefix delete: got {attempted_droneid}, should be {db_drone['droneid']}")
            await msg.delete()
            return

        await self.send_as_drone(db_drone, hook, msg)
        return

    async def send_as_drone(self, drone: RegisteredDrone, hook: discord.Webhook, msg: discord.Message):
        droneid = drone['droneid']
        hivesym = hivemap.get(drone.get('hive'), '☼')  # This is the defailt hive symbol
        content = msg.content.replace(f"{droneid} :: ", '')
        code = format_code(content, drone)

        if aget(code, 0, None):
            content = content.replace(code[1], '')
        content = await self.handle_filter(content, drone, msg)

        # This list can be thought of as the 'fields' in a drone message.
        content_list = [
            droneid,
            hivesym,
            code[0],
            content
        ]
        content_list = list(filter(None, content_list))  # Strip Nones so we construct the output correctly

        reply_embed = await reply_builder(msg)  # Populate a reply embed if necessary

        out_content = ""
        for i, v in enumerate(content_list):
            if v:
                out_content += f"{v} :: " if i < len(content_list)-1 else f"{v}"

        await hook.send(
            username=msg.author.nick or msg.author.name,
            content=out_content,
            avatar_url=msg.author.avatar.url,
            embed=reply_embed
        )
        await msg.delete()
        return

    @staticmethod
    async def handle_filter(content: str, drone: RegisteredDrone, msg: discord.Message) -> str:
        # TODO
        return content


def setup(bot):
    bot.add_cog(Filter(bot))
