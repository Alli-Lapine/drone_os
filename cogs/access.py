from discord.commands import SlashCommandGroup, ApplicationContext, Option
from discord.ext import commands

from util import guilds, mkembed
from util.access_utils import grant_access, revoke_access, has_access, accesslist_to_dronelist, get_drone_hive_owner
from util.storage import get_drone


class Access(commands.Cog):
    accessgrp = SlashCommandGroup(name="access", description="Drone access management", guild_ids=guilds)

    def __init__(self, bot):
        self.bot = bot
        bot.logger.info("access v1.0 ready")

    @accessgrp.command(name="add", description="Add a drone to another drone's access list", guild_ids=guilds)
    async def add_access(self, ctx: ApplicationContext,
                         drone: Option(str, description="Drone ID to add", required=True),
                         target: Option(str, description="Drone to modify (yourself if blank)", required=False)):
        operator = get_drone(ctx.author.id)
        if not operator:
            await ctx.respond(embed=mkembed('error', '`You do not appear to be a drone.`'))
            return
        target_drone = get_drone(target) if target else operator
        if not target_drone:
            await ctx.respond(embed=mkembed('error', f'{target} does not appear to be a drone.'))
            return
        to_add_drone = get_drone(drone)
        if not to_add_drone:
            await ctx.respond(embed=mkembed('error', f'{drone} does not appear to be a drone.'))
            return

        if not has_access(operator, target_drone):
            await ctx.respond(embed=mkembed('error', f'`{operator.droneid}@droneOS $ touch /dev/{target_drone.droneid}/access/{to_add_drone.droneid}\ntouch: permission denied`'))
            return
        else:
            r = grant_access(to_add_drone, target_drone)
            if not r:
                await ctx.respond(embed=mkembed('error', f'`{to_add_drone.droneid} is already on the access list of {target_drone.droneid}`'))
            else:
                await ctx.respond(embed=mkembed('done', f'`{to_add_drone.droneid} added to the access list of {target_drone.droneid}`'))

    @accessgrp.command(name="rm", description="Remove a drone from another drone's access list", guild_ids=guilds)
    async def rm_access(self, ctx: ApplicationContext,
                        drone: Option(str, description="Drone ID to remove", required=True),
                        target: Option(str, description="Drone to modify (yourself if blank)", required=False)):
        operator = get_drone(ctx.author.id)
        if not operator:
            await ctx.respond(embed=mkembed('error', '`You do not appear to be a drone.`'))
            return
        target_drone = get_drone(target) if target else operator
        if not target_drone:
            await ctx.respond(embed=mkembed('error', f'{target} does not appear to be a drone.'))
            return
        to_rm_drone = get_drone(drone)
        if not to_rm_drone:
            await ctx.respond(embed=mkembed('error', f'{drone} does not appear to be a drone.'))
            return

        if not has_access(operator, target_drone):
            await ctx.respond(embed=mkembed('error', f'`{operator.droneid}@droneOS $ rm /dev/{target_drone.droneid}/access/{to_rm_drone.droneid}\nrm: permission denied`'))
            return
        else:
            r = revoke_access(to_rm_drone, target_drone)
            if not r:
                await ctx.respond(embed=mkembed('error', f'`{operator.droneid}@droneOS $ rm /dev/{target_drone.droneid}/access/{to_rm_drone.droneid}\nrm: cannot remove "{to_rm_drone.droneid}": No such file or directory`'))
            else:
                await ctx.respond(embed=mkembed('done', f'`{to_rm_drone.droneid} removed from the access list of {target_drone.droneid}`'))

    @accessgrp.command(name='ls', description="Show drone's access list", guild_ids=guilds)
    async def ls_access(self, ctx: ApplicationContext, target: Option(str, description="Drone to check (yourself if blank)", required=False)):
        operator = get_drone(ctx.author.id)
        if not operator:
            await ctx.respond(embed=mkembed('error', '`You do not appear to be a drone.`'))
            return
        target_drone = get_drone(target) if target else operator
        if not target_drone:
            await ctx.respond(embed=mkembed('error', f'{target} does not appear to be a drone.'))
            return
        if not has_access(operator, target_drone):
            await ctx.respond(embed=mkembed('error', f'`{operator.droneid}@droneOS $ ls /dev/{target_drone.droneid}/access/\nls: permission denied`'))
            return
        else:
            al: [int] = target_drone['access']
            al.append(int(get_drone_hive_owner(target_drone)['discordid']))
            drones = accesslist_to_dronelist(al)
            drones_fmt = [f"{d.droneid} " for d in drones]
            res = f"```{operator.droneid}@droneOS $ ls /dev/{target_drone.droneid}/access\n" \
                  f"{''.join(drones_fmt)}```"
            await ctx.respond(res)


def setup(bot):
    bot.add_cog(Access(bot))
