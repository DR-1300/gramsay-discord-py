import discord
from discord.ext import commands

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    @commands.command()
    async def avatar(self, ctx, member: discord.Member=None):
        """to get a person's avatar"""
        if member is None:
            member = ctx.author
        embed = discord.Embed(
            title= f"{member.name}'s avatar"
        )
        embed.set_image(url = member.display_avatar.url)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Misc(bot))