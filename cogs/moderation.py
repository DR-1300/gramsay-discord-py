import discord
from discord.ext import commands
from datetime import timedelta

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int = 10):
        """clears a certain number of messages from a channel"""
        await ctx.channel.purge(limit = amount+1)
        msg = await ctx.send(f"deleted {amount} message(s)")
        await msg.delete(delay=3)
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member:discord.Member, *, reason:str = "no reason :/"):
        """kicks a member from the server"""
        await member.kick(reason=reason)
        embed = discord.Embed(
            title="member kicked",
            description=f"{member.mention} has been kicked lol"
        )
        embed.add_field(name = 'reason', value = reason)
        embed.add_field(name="mod", value = ctx.author.mention)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Moderation(bot))