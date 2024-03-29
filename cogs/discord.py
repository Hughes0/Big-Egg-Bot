import discord
from discord.ext import commands
import requests
import discord.utils
import csv
import sys
import os
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.getenv("PROJECT_PATH"))

import helpers


async def make_warroom(ctx, defender_id, category=None, hitters=None):
    url = f"https://politicsandwar.com/api/nation/id={defender_id}&key={helpers.apikey()}"
    data = requests.get(url).json()
    print("data retrieved")
    helpers.catch_api_error(data, version=1)
    channel_name = f"{data['name']} - c{data['cities']}"
    if category:
        print("category specified")
        await ctx.send(f"Creating war room for nation `id: {defender_id}` in category `{category}`")
        category = discord.utils.get(ctx.guild.categories, name=category)
        print(f"category: {category}")
        if not category:
            raise Exception("Category does not exist")
        channel = await ctx.guild.create_text_channel(channel_name, category=category)
        print(f"channel created: {channel}")
    else:
        print("category not specified")
        await ctx.send(f"Creating a waroom for nation `id: {defender_id}`")
        channel = await ctx.guild.create_text_channel(channel_name)
        perms = channel.overwrites_for(ctx.guild.default_role)
        perms.read_messages = False
    if hitters:
        print("iterating through hitters")
        for user in hitters:
            print(f"user {user}")
            perms = channel.overwrites_for(user)
            perms.send_messages = True
            perms.read_messages = True
            perms.read_message_history = True
            await channel.set_permissions(user, overwrite=perms)
            print("set perms")

    await ctx.send(f"Room <#{channel.id}> was created successfully")
    link = await channel.send(f"https://politicsandwar.com/nation/id={defender_id}")
    await link.pin()
    return channel


class Discord(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.command()
    @commands.check(helpers.perms_six)
    async def warroom(self, ctx, defender_id, category=None):
        await make_warroom(ctx, defender_id, category)

    @warroom.error
    async def warroom_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument, correct syntax is `{self.bot.command_prefix}warroom <defender_id> [category]`")

    @commands.command()
    @commands.check(helpers.perms_seven)
    async def mass_warroom(self, ctx):
        attachment_url = ctx.message.attachments[0].url
        content = requests.get(attachment_url).content.decode()
        with open('../blitz.csv', 'w') as f:
            f.write(content)
        with open('../blitz.csv', 'r') as f:
            guild_members = ctx.guild.members
            reader = csv.reader(f, delimiter=",")
            for row in reader:
                if not row[0]:
                    continue
                print(row)
                category = row[-2].replace('"', '')
                print(category)
                orders = row[-1].replace('"', '')
                hitters = []
                for person in row[1:4]:
                    if person:
                        # user = discord.utils.get(ctx.guild.members, display_name=str(person))
                        user = None
                        for member in guild_members:
                            if member.display_name.lower() == str(person).lower():
                                user = member
                        hitters.append(user)
                try:
                    room = await make_warroom(ctx, row[0], category=category, hitters=hitters)
                    print("room created")
                    pings = [f"<@!{user.id}>" for user in hitters]
                    print('ping found')
                    await room.send(f"ORDERS: {' '.join(pings)}\n{orders}")
                    print('orders sent')
                except:
                    await ctx.send(f"Error creating room for `{row}`")





def setup(bot):
    bot.add_cog(Discord(bot))