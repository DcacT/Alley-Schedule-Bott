import os
import os.path
import discord
import asyncio
from discord.client import Client
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

class MyClient (discord.Client):

    async def on_ready(self):

        for guild in self.guilds:
                if guild.name == GUILD:
                    break
        print(f'{self.user} has connected to Discord!')
        print(
                f'{self.user} is connected to the following guild:\n'
                f'{guild.name}(id: {guild.id})'
        ) 
        print('Ready to go')

    async def on_message(self, message):
        if message.author.id == self.user.id:
            return

        if message.content.startswith('T'):
            channel = 0
            print(self.guilds)
            for guild in self.guilds:
                for channels in guild.voice_channels:
                    print(type(channels.id))
                    if channels.id == 896469712228221042:
                        channel = channels
                        break
                    else :
                        print("channel not found")

            if channel != 0:    
                BotInChannel = False
                for x in channel.members:
                    if x.bot == True:
                        BotInChannel == True
                        break
                if BotInChannel == False:
                    connection = await channel.connect()
                    connection.timeout = 3600

            s = '0'.join(x for x in message.content if x.isdigit())
            number = int(s)
            sec = number*60
            sec = 5
            if sec <= 0:
                Timer = await message.channel.send('number too smol')
            elif sec > 3000000000:
                Timer = await message.channel.send('number too big')
            else:
                Timer = await message.channel.send('number ok')
                await asyncio.sleep(1)
                Timer = await message.channel.send(sec)
                while sec != 0:
                    sec -= 1
                    await Timer.edit(content=sec)
                    await asyncio.sleep(1)
                await Timer.edit(content='Ended timer of '+ str(s)+' minutes')
                NewMessage = await message.channel.send(";;play https://www.youtube.com/watch?v=u3rS-fQ1nUI")
                await asyncio.sleep(10)
                await NewMessage.delete()
                channel.disconnect()

client = MyClient()
client.run(TOKEN)