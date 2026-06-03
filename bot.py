import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()

intents = discord.Intents.all()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents = intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    for cog in ["cogs.moderation", "cogs.misc","cogs.help"]:
        await bot.load_extension(cog)
        print(f"Loaded {cog}")
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("u cant use this command lols")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("cant find ts person here LOL")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"need the argument `{error.param.name}`")
    else:
        await ctx.send(f"eroor : {error}")

bot.run(os.getenv("TOKEN"))