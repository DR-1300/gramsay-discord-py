import discord
from discord.ext import commands, tasks
import random
from datetime import datetime, timedelta, timezone
import re
 
def parse_duration(duration:str):
    pattern = r"(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?"
    match = re.fullmatch(pattern, duration.strip())
    if not match or not any(match.groups()):
        raise ValueError("invalid duration format sonny, use it like 1d2h30m")
    days = int(match.group(1) or 0)
    hours = int(match.group(2) or 0)
    minutes = int(match.group(3) or 0)
    seconds = int(match.group(4) or 0)
 
    total_s = days*86400 + hours*3600 + minutes*60 + seconds
    if total_s<=0:
        raise ValueError("tf is this time")
    return total_s
 
class Giveaways(commands.Cog):
 
    @tasks.loop(seconds=10)
    async def check_giveaways(self):
        rows = await self._get_active_giveaways()
        for row in rows:
            await self.end_giveaway(row)
 
    @check_giveaways.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()
 
    def __init__(self, bot):
        self.bot = bot
        self.check_giveaways.start()
 
    def cog_unload(self):
        self.check_giveaways.cancel()
 
    async def _create_giveaway(self, guild_id, channel_id, message_id, host_id, prize, winners, ends_at):
        await self.bot.db.execute("""
            INSERT INTO giveaways (guild_id, channel_id, message_id, host_id, prize, winner_count, ends_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, guild_id, channel_id, message_id, host_id, prize, winners, ends_at)
 
    async def _get_giveaway(self, message_id):
        return await self.bot.db.fetchone(
            "SELECT * FROM giveaways WHERE message_id = %s", message_id
        )
 
    async def _end_giveaway_db(self, message_id):
        await self.bot.db.execute(
            "UPDATE giveaways SET ended = TRUE WHERE message_id = %s", message_id
        )
 
    async def _get_active_giveaways(self):
        return await self.bot.db.fetchall(
            "SELECT * FROM giveaways WHERE ended = FALSE AND ends_at <= NOW()"
        )
 
    async def _get_guild_giveaways(self, guild_id):
        return await self.bot.db.fetchall(
            "SELECT * FROM giveaways WHERE guild_id = %s ORDER BY ends_at DESC LIMIT 10", guild_id
        )
 
    def _build_embed(self, prize, winner_count, host:discord.Member, ends_at:datetime, ended=False, winners=None):
        embed = discord.Embed(title=f"🎉 {prize}", timestamp=ends_at)
        embed.add_field(name="winners", value=str(winner_count), inline=True)
        embed.add_field(name="hosted by", value=host.mention, inline=True)
        if ended and winners:
            w = ", ".join(w.mention for w in winners)
            embed.add_field(name="winner(s)", value=w, inline=False)
            embed.set_footer(text="giveaway ended")
        elif ended:
            embed.add_field(name="winner(s)", value="or lack thereof", inline=False)
            embed.set_footer(text="giveaway ended")
        else:
            embed.set_footer(text="giveaway, click the 🎉 to join")
        return embed
 
    async def _pick_winners(self, message:discord.Message, count:int, host_id:int):
        try:
            reaction = discord.utils.get(message.reactions, emoji="🎉")
            if not reaction:
                return []
            users = [u async for u in reaction.users() if not u.bot]  # only skip bots, host can win
            if not users:
                return []
            return random.sample(users, min(count, len(users)))
        except Exception:
            return []
 
    async def end_giveaway(self, giveaway:dict):
        channel = self.bot.get_channel(giveaway["channel_id"])
        if not channel:
            return
        try:
            message = await channel.fetch_message(giveaway["message_id"])
        except discord.NotFound:
            await self._end_giveaway_db(giveaway["message_id"])
            return
 
        guild = channel.guild
        host = guild.get_member(giveaway["host_id"]) or await self.bot.fetch_user(giveaway["host_id"])
        winners = await self._pick_winners(message, giveaway["winner_count"], giveaway["host_id"])
        embed = self._build_embed(
            giveaway["prize"], giveaway["winner_count"], host,
            giveaway["ends_at"], ended=True, winners=winners if winners else None
        )
        await message.edit(embed=embed)
 
        if winners:
            mentions = ", ".join(w.mention for w in winners)
            await channel.send(
                f"congo bongos {mentions}! you won **{giveaway['prize']}**!\n"
                f"[jump to giveaway]({message.jump_url})"
            )
        else:
            await channel.send(f"no valid entries for **{giveaway['prize']}** lol")
        await self._end_giveaway_db(giveaway["message_id"])
 
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def gstart(self, ctx, duration:str, winners:str, *, prize:str):
        """start a giveaway. usage: !gstart 1h 1w prize"""
        if not winners.endswith("w") or not winners[:-1].isdigit():
            return await ctx.send("winners must be in the format `1w`, `3w` ( 1 winner, 3 winner type shit ) etc.")
        winner_count = int(winners[:-1])
        if winner_count < 1:
            return await ctx.send("bro every giveaway must have atleast 1 winner lol")
        try:
            seconds = parse_duration(duration)
        except ValueError as e:
            return await ctx.send(f"{e}, sorry")
 
        ends_at = datetime.now() + timedelta(seconds=seconds) 
        embed = self._build_embed(prize, winner_count, ctx.author, ends_at)
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("🎉")
        await ctx.message.delete()
        await self._create_giveaway(
            ctx.guild.id, ctx.channel.id, msg.id,
            ctx.author.id, prize, winner_count, ends_at
        )
 
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def gend(self, ctx, message_id:int):
        """force end an active giveaway early. usage: !gend <message_id>"""
        giveaway = await self._get_giveaway(message_id)
        if not giveaway:
            return await ctx.send(f"theres no giveaway with {message_id}")
        if giveaway["ended"]:
            return await ctx.send("if u are so smart tell me how am i supposed to end an already ended giveaway early?")
        await self.end_giveaway(giveaway)
 
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def greroll(self, ctx, message_id:int):
        """reroll a winner for an ended giveaway. usage: !greroll <message_id>"""
        giveaway = await self._get_giveaway(message_id)
        if not giveaway:
            return await ctx.send(f"theres no giveaway with {message_id}")
        if not giveaway["ended"]:
            return await ctx.send("how the HELL am i supposed to reroll a giveaway which hasnt ended yet smartass 😭✌️")
        channel = self.bot.get_channel(giveaway["channel_id"])
        try:
            message = await channel.fetch_message(message_id)
        except discord.NotFound:
            return await ctx.send("bro where is the message")
        winners = await self._pick_winners(message, giveaway["winner_count"], giveaway["host_id"])
        if not winners:
            return await ctx.send("😔 no valid entries to reroll from")
        mentions = ", ".join(w.mention for w in winners)
        await ctx.send(f"🎉 new winner(s): {mentions}, congo bongos")
 
    @commands.command()
    async def glist(self, ctx):
        """lists the recent giveaways in the server"""
        rows = await self._get_guild_giveaways(ctx.guild.id)
        if not rows:
            return await ctx.send("lol ts server dead, no giveaways found")
        embed = discord.Embed(title="giveaways")
        for row in rows:
            status = "ended" if row["ended"] else "active"
            embed.add_field(
                name=f"{status} -- {row['prize']}",
                value=f"winners: `{row['winner_count']}` | ends: <t:{int(row['ends_at'].timestamp())}:R>\n"
                      f"[Jump](https://discord.com/channels/{row['guild_id']}/{row['channel_id']}/{row['message_id']})",
                inline=False
            )
        await ctx.send(embed=embed)
 
async def setup(bot):
    await bot.add_cog(Giveaways(bot))
