import discord
from discord.ext import commands
import requests
import json
import sys
sys.path.append('..')
import helpers




class Bank(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    

def setup(bot):
    bot.add_cog(Bank(bot))