from datetime import datetime

from discord.commands import ApplicationContext, Option, permissions
from discord.ext import commands

from util import guilds, mkembed
from util.access_utils import get_command_drones
from util.storage import Storage, get_drone


class Messaging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.logger.info("messaging v1.0 ready")

    @commands.slash_command(name="wall", description="Send a DroneOS announcement", guild_ids=guilds)
    @permissions.has_role("Production")
    async def wall(self, ctx: ApplicationContext, message: Option(str, required=True)):
        db_drone = get_drone(ctx.author.id)
        if not db_drone:
            await ctx.respond("`Access denied`", ephemeral=True)
            return
        droneid = db_drone["droneid"]
        await ctx.respond(
            f"""```
Broadcast message from {droneid}@DroneOS (pts/0) ({datetime.now().strftime('%c')}):

{message}```"""
        )

    @commands.slash_command(
        name="dc", description="Assume direct control of another drone", guild_ids=guilds
    )
    async def ssh(self, ctx: ApplicationContext, drone: Option(str, "Drone ID", required=True)):
        operator, target, error = await get_command_drones(ctx.author.id, drone)
        if error:
            await ctx.respond(embed=error)
            return
        if operator.droneid == target.droneid:
            await ctx.respond(
                embed=mkembed("error", "`You are already in direct control of yourself (hopefully)`")
            )
            return
        oconf = operator.get("config", {})
        if oconf.get("ssh", False) is not False:
            await ctx.respond(
                embed=mkembed(
                    "error", f'`ssh: Max nesting level reached, disconnect from {oconf["ssh"]} first'
                )
            )
            return
        operator["config"] = oconf
        operator["config"]["ssh"] = target.droneid
        Storage.backend.save(operator)
        await ctx.respond(
            embed=mkembed(
                "done",
                f"`{operator.droneid}@droneOS $ ssh {operator.droneid}@{target.droneid}\n"
                f"Offering public key: {operator.droneid} RSA DISC:{operator.discordid} agent\n"
                f"Authenticated to {target.droneid}\n"
                f"ASSUMING DIRECT CONTROL\n{operator.droneid}@{target.droneid} #`",
            )
        )
        return

    @commands.slash_command(
        name="dc-end", description="Relinquish direct control of another drone", guild_ids=guilds
    )
    async def sshend(self, ctx: ApplicationContext):
        operator, target, error = await get_command_drones(
            ctx.author.id, ctx.author.id, chkaccess=False
        )
        if error:
            await ctx.respond(embed=error)
            return
        oconf = operator.get("config", {})
        if oconf.get("ssh", False) is False:
            await ctx.respond(embed=mkembed("error", f"`ssh: No remote session found`"))
            return
        operator["config"] = oconf
        operator["config"]["ssh"] = False
        Storage.backend.save(operator)
        await ctx.respond(embed=mkembed("done", f"`Direct control terminated.`"))
        return


def setup(bot):
    bot.add_cog(Messaging(bot))
