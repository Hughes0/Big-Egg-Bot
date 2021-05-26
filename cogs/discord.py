import discord
from discord.ext import commands
import requests
import json
import sys
sys.path.append('..')
import helpers




class Discord(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.command()
    @commands.check(helpers.perms_six)
    async def warroom(self, ctx, defender_id, category=None):
        url = f"https://politicsandwar.com/api/nation/id={defender_id}&key={helpers.apikey()}"
        data = requests.get(url).json()
        helpers.catch_api_error(data, version=1)
        channel_name = f"{data['name']} - c{data['cities']}"
        if category:
            await ctx.send(f"Creating war room for nation `id: {defender_id}` in category `{category}`")
            category = discord.utils.get(ctx.guild.categories, name=category)
            if not category:
                raise Exception("Category does not exist")
            channel = await ctx.guild.create_text_channel(channel_name, category=category)
        else:
            await ctx.send(f"Creating a waroom for nation `id: {defender_id}`")
            channel = await ctx.guild.create_text_channel(channel_name)
            perms = channel.overwrites_for(ctx.guild.default_role)
            perms.read_messages = False
            # set permissions?
        await ctx.send(f"Room <#{channel.id}> was created successfully")
        link = await channel.send(f"https://politicsandwar.com/nation/id={defender_id}")
        await link.pin()

    @warroom.error
    async def warroom_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}warroom <defender_id> [category]`")


    

def setup(bot):
    bot.add_cog(Discord(bot))