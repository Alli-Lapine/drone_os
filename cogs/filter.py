import re
from typing import List, Optional

import discord
from discord.commands import SlashCommandGroup, permissions, Option, ApplicationContext
from discord.ext import commands

from util import guilds, mkembed, hivemap, aget, codes
from util.storage import RegisteredDrone, Storage, DroneChannel


async def get_drone_webhook(channel: discord.channel) -> Optional[discord.Webhook]:
    hooks = await channel.webhooks()
    if not hooks:
        return None

    for h in hooks:
        if h.name == "Drone speech optimization":
            return h

    return None


def _get_emojis(msg: discord.Message) -> List[dict]:
    content = msg.content
    res = re.finditer(r'<(?P<animated>a)?:(?P<name>\w+):(?P<snowflake>\d+)>', content)
    if not res:
        return []
    emos = []
    for r in res:
        rd = r.groupdict()
        ext = 'gif' if rd.get('animated') else 'png'
        emo = {
            'name': rd['name'],
            'id': rd['snowflake'],
            'url': f"https://cdn.discordapp.com/emojis/{rd['snowflake']}.{ext}",
            'data': None,
            'animated': rd.get('animated')
        }
        emos.append(emo)
    return emos


def _format_emoji(emo: dict) -> str:
    return f"<{'a' if emo['animated'] else ''}:{emo['name']}:{emo['id']}> "


class Filter(commands.Cog):
    filtergrp = SlashCommandGroup(name="dronespeech", description="Drone speech optimizations", guild_ids=guilds)

    def __init__(self, bot):
        self.bot = bot
        bot.logger.info("filter v2.9.2 ready")

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
        attempted_did = aget(attempted_chat, 0, None)
        attempted_content = aget(attempted_chat, 1, None)

        try:
            d = Storage.backend.get(RegisteredDrone, {'discordid': msg.author.id})
        except RegisteredDrone.DoesNotExist:
            d = None

        if attempted_did and not attempted_content:
            # Malformed attempt, yeet it.
            self.bot.logger.info(f"Malformed delete: {msg}")
            await msg.delete()
            return

        # Is the channel locked to enforce mode?
        try:
            c = Storage.backend.get(DroneChannel, {'discordid': msg.channel.id})
        except DroneChannel.DoesNotExist:
            c = {}
        cconf = c.get('config', {})
        if cconf.get('enforcedrones'):  # All registered drones must use speech opt
            if d:
                if not attempted_did and not attempted_content:
                    self.bot.logger.info(f"Chan enforcedrone delete: {msg}")
                    await msg.delete()
                    return
                else:
                    await self.send_as_drone(d, hook, msg)
                    await msg.delete()
                    return

        if cconf.get('enforceall'):
            if not attempted_did:  # Only drones may speak
                self.bot.logger.info(f"Chan Enforceall delete: {msg}")
                await msg.delete()
                return

        # If a non-drone uses a prefix, just bail.
        if not d:
            return

        # Is the drone locked to enforce mode?
        dconf = d.get('config', {})
        if dconf.get('enforce'):
            if not attempted_did and not attempted_content:
                self.bot.logger.info(f"Drone enforce delete: {msg}")
                await msg.delete()
                return
            else:
                await self.send_as_drone(d, hook, msg)
                await msg.delete()
                return

        if not attempted_did:
            return

        # Is the drone using their own prefix?
        if attempted_did and d['droneid'] != attempted_did:
            self.bot.logger.info(f"Wrong prefix delete: got {attempted_did}, should be {d['droneid']}")
            await msg.delete()
            return

        await self.send_as_drone(d, hook, msg)
        return

    async def send_as_drone(self, drone: RegisteredDrone, hook: discord.Webhook, msg: discord.Message):
        droneid = drone['droneid']
        hivesym = hivemap.get(drone.get('hive'), '☼')
        content = msg.content.replace(f"{droneid} :: ", '')

        content = await self.handle_filter(content, drone, msg)
        content_list = [
            droneid,
            hivesym,
            await self.format_code(content, drone),
            content
        ]

        if msg.reference:
            mrr = msg.reference.resolved
            reply_embed = discord.Embed(
                color=discord.Color.green(),
                description=f"[Reply to]({mrr.jump_url}): {mrr.content}"
            ).set_author(
                # Webhook bot messages are Users rather than Members and have no nick
                name=mrr.author.nick if isinstance(msg.reference.resolved.author, discord.Member) else mrr.author.name,
                icon_url=msg.reference.resolved.author.avatar.url
            )
        else:
            reply_embed = None

        out_content = ""
        for i, v in enumerate(content_list):
            if v:
                out_content += f"{v} :: " if i < len(content_list)-1 else f"{v}"

        await hook.send(
            username=msg.author.nick,
            content=out_content,
            avatar_url=msg.author.avatar.url,
            embed=reply_embed
        )
        await msg.delete()
        return

    @staticmethod
    async def handle_filter(content: str, drone: RegisteredDrone, msg: discord.Message) -> str:
        return content

    @staticmethod
    async def format_code(content: str, drone: RegisteredDrone) -> Optional[str]:
        if drone:
            c = aget(re.findall(r'^(.{3,4})(.*)$', content), 0, None)
            if c:
                if c[0] in codes.keys():
                    return f"Code {c[0]} :: {codes[c[0]]}"
        return None


def setup(bot):
    bot.add_cog(Filter(bot))
