import os
import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions
import random
import json
import requests
from profanity import profanity
import google.generativeai as palm
import pprint
from dotenv import load_dotenv

load_dotenv()

keyAPI = str(os.environ['palm'])
palm.configure(api_key=keyAPI)
models = [m for m in palm.list_models() if 'generateText' in m.supported_generation_methods]
# model = models[0].name
model = palm.GenerativeModel('gemini-pro')

# this is for running bot 24/7
intents = discord.Intents.default()
intents.members=True
Token = os.environ['Token']
prefix = "-"
intents = discord.Intents.default()


client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix=prefix, case_insensitive=True)

depressing_words = ('I feel bored', 'i feel bored', 'my life sucks','I feel lonely', "?quote")

greeting_words = [
    "Hey", "Greetings from the creators of Mr. Authority", "hello!", 'wassup'
]

words_from_user = ('hi', 'wassup', 'hey', 'hello')

default_bad_words = profanity.get_words()

reply_to_bad_word = ('no', 'no bad words', "SHUT UP NO BAD WORDS", "I WARN YOU NOT TO USE BAD WORDS")



def get_quote():
    response = requests.get("https://zenquotes.io/api/random")
    json_data = json.loads(response.text)
    quote = json_data[0]['q'] + " -" + json_data[0]['a']
    return (quote)


@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@bot.command()
@has_permissions(kick_members=True)
async def kick(message, kick_member:discord.Member,*,reason=None):
  if kick_member == bot.user:
    print('u cannot kick me:angry:')
  elif kick_member.top_role >= message.author.top_role:
    print('no possible')
  elif kick_member == message.author:
    print('u cannot kick urself')
  else:
    await kick_member.kick(reason=reason)
    await message.channel.send(f"user{kick_member} has been kicked")
  



#defining a message
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    msg = message.content
    mention = message.author.mention
    member = discord.Member
	
    #greets
    if message.content.startswith(words_from_user):
        await message.channel.send(random.choice(greeting_words))
    #sends motivaional quotes
    if message.content.startswith(depressing_words):
        await message.channel.send(f'Here is a quote to cheer you up: ' + get_quote())
      
    #removes words
    if message.content.startswith("?bad word remove "):
        splited = msg.split()
        sub_splitted = splited[3]
        default_bad_words.remove(sub_splitted)
        await message.channel.send('The word was removed')

    #Add more words
    if message.content.startswith("?bad word add "):
        splited = msg.split()
        sub_splitted = splited[3]
        default_bad_words.append(sub_splitted)
        await message.channel.send("The word was added")

    if message.content.startswith("?chat "):
        completion = palm.generate_text(model=model, prompt=message.content[6:], temperature=0.5)
        await message.channel.send( f"{mention} {completion.result}" )

    if message.content.startswith("?chatembed"):
        completion = palm.generate_content(message.content[10:])
			# completion = palm.generate_content(model=model, prompt=message.content[10:], temperature=0.5)
        embed_discordchat=discord.Embed(title=f"Response to:{message.content[10:]}", description=f"'{mention}' \n{completion.result}")

			#         embed_discordchat=discord.Embed(title=f"Response to:{message.content[10:]}", description=f"'{mention}' \n{completion.result}")
        embed_discordchat.set_thumbnail(url="https://media.discordapp.net/attachments/1068024665949360188/1184324621584060486/colourful-google-logo-in-dark-background-free-vector.png?ex=658b8f41&is=65791a41&hm=ba74f4466098cc6aa6958084a5e9ad3e5662354d3db8733dc5b73c10a9247458&=&format=webp&quality=lossless&width=918&height=918")
        await message.channel.send(embed=embed_discordchat)
			
			
			
			
	
			
    
    #deleting messages that contain toxicity
    if any(word in msg for word in default_bad_words):
        await message.delete()
        await message.channel.send(f"{mention} {random.choice(reply_to_bad_word)}")
        embed_discordBad=discord.Embed(title="Registered offence for mentioning a bad word", description=f"{mention} has spoken of a bad word, please contact admin for more information")
        avatar_profile = message.author.avatar
        embed_discordBad.set_thumbnail(url=avatar_profile)
        await message.channel.send(embed=embed_discordBad)


#welcoming the user to the server
async def on_message_join(member):
    channel = client.get_channel(876805975624020069)
    embed=discord.Embed(title=f"Welcome {member.name}", description=f"Thanks for joining {member.guild.name}!") # F-Strings!
    embed.set_thumbnail(url=member.avatar) # Set the embed's thumbnail to the member's avatar image!
    
    await channel.send(embed=embed)




client.run(Token)

# now it shud work with default bad words_from_user
