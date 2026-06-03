import discord
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command("help")

    @commands.command()
    async def help(self, ctx, *, cog_or_command : str= None):
        if cog_or_command:
            cmd = self.bot.get_command(cog_or_command.lower())
            if cmd:
                embed = discord.Embed(
                    title= f"{cmd.name}",
                    description = cmd.help or "nothing to say or name is self explanatory"
                )
                if cmd.aliases:
                    embed.add_field(name="aliases", value=", ".join(f"`{c_a}`" for c_a in cmd.aliases))
                usage = f"!{cmd.name} {cmd.signature}".strip()
                embed.add_field(name="usage", value=f"`{usage}`", inline=False)
                return await ctx.send(embed=embed)
            cog = self.bot.get_cog(cog_or_command.capitalize())
            if cog:
                return await ctx.send(embed=self._cog_embed(cog))
            return await ctx.send(f"tf is `{cog_or_command}`?")
        embed = discord.Embed(
            title="help menu",
            description=f"use `!help <command>` or `!help <category>` for more info\nPrefix: `!`",
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        for cog_name, cog in self.bot.cogs.items():
            cmds = [c for c in cog.get_commands() if not c.hidden]
            if not cmds:
                continue
            cmd_list=" ".join(f"`{c.name}`" for c in cmds)
            embed.add_field(name=f"**{cog_name}**", value=cmd_list, inline=False)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
    def _cog_embed(self, cog:commands.Cog):
        """Build a detailed embed for a specific cog."""
        embed = discord.Embed(
            title=f"{cog.qualified_name}",
        )
        for cmd in cog.get_commands():
            if cmd.hidden:
                continue
            usage = f"!{cmd.name} {cmd.signature}".strip()
            embed.add_field(
                name=f"`{usage}`",
                value=cmd.help or "nothing to say or self explanatory :/",
                inline=False
            )
        return embed
async def setup(bot):
    await bot.add_cog(Help(bot))