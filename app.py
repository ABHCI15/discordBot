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
from langchain_core.tools import Tool
from langchain_community.document_loaders import UnstructuredFileLoader
from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    HarmBlockThreshold,
    HarmCategory,
    GoogleGenerativeAIEmbeddings,
)
from pprint import pprint
import sqlalchemy as sa
from langchain_community.utilities import SQLDatabase
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_chroma import Chroma
from langchain.chains import RetrievalQAWithSourcesChain
# from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
load_dotenv()
from langchain_core.tools import ToolException
from langchain_core.tools import StructuredTool
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from time import sleep
from langchain_huggingface import HuggingFaceEmbeddings


book_list = os.listdir("chembooks")
# embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
modelPath = "BAAI/bge-large-en-v1.5"
model_kwargs = {'device':'cpu'}
encode_kwargs = {'normalize_embeddings': True}
embeddings = HuggingFaceEmbeddings(
    model_name=modelPath,     
    model_kwargs=model_kwargs, 
    encode_kwargs=encode_kwargs 
)
def store_books():
    text_splitter = SemanticChunker(embeddings=embeddings,breakpoint_threshold_type="standard_deviation")
    split = []

    for book in book_list:
        file_name = Path(os.path.join("chembooks", book))
        loader = PyMuPDFLoader(file_name,extract_images=False)
        documents = loader.load()
        split.append(text_splitter.split_documents(documents))
        sleep(5)
    # documents = PyPDFDirectoryLoader("chembooks").load()
    # split = text_splitter.split_documents(documents)
    all_splits = [doc for sublist in split for doc in sublist]
    global db
    db = Chroma.from_documents(documents=all_splits, embedding=embeddings, persist_directory="./chem_chroma_db")
    # 
    
        
# def store_book(bookpath : str):
#     loader = PyMuPDFLoader(bookpath,extract_images=True)
#     documents = loader.load()
#     embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
#     text_splitter = SemanticChunker(embeddings=embeddings,breakpoint_threshold_type="standard_deviation")
#     split = text_splitter.split_documents(documents)
#     global db
#     db = Chroma.from_documents(documents=split, embedding=embeddings, persist_directory="./chem_chroma_db")   
    

async def chem_book_retriever(query: str):
    try:
        results = db._asimilarity_search_with_relevance_scores(query, 5)
        return results
    except:
        raise ToolException("An error occurred while retrieving the chemistry textbook pages.")

chem_ret = StructuredTool.from_function(
    func=chem_book_retriever,
    input_type=str,
    name="chemistry textbook retriever",
    description="Retrieves the most relevant chemistry textbook pages for a given query, always use with any chemistry related concepts.",
    handle_tool_error=True,
)

# venv/lib/python3.11/site-packages/mendeleev/elements.db
# db.as_retriever()
# db.delete_collection

# async def get_docs(query: str):
#     results = db._asimilarity_search_with_relevance_scores(query, 5)

db_chem = SQLDatabase.from_uri("sqlite:///elements.db")
token = str(os.getenv("TOKEN"))
bot = discord.Bot()
llm = ChatGoogleGenerativeAI(model="models/gemini-1.5-pro", temperature=0.1, google_api_key=str(os.getenv("GOOGLE_API_KEY")), safety_settings={ HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE, HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE, HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE})
toolkit = SQLDatabaseToolkit(db=db_chem, llm=llm)
context = toolkit.get_context()
tools = [chem_ret]
tools.append(toolkit.get_tools())

@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")
    # store_chembooks()

@bot.slash_command(name="hello", description="Say hello to the bot")
async def hello(ctx: discord.ApplicationContext):
    await ctx.respond("Hey!")
    
@bot.event
async def on_member_join(member):
    await member.send(
        f'Welcome to the server, {member.mention}! Enjoy your stay here.')

@bot.slash_command(name="ping", description="Check the bot's latency")
async def ping(ctx: discord.ApplicationContext):
    await ctx.respond(f"Pong! {round(bot.latency * 1000)}ms")

@bot.command()
async def chat(ctx, message: discord.Option(discord.SlashCommandOptionType.string)):
    await ctx.respond(llm.invoke(message))

@bot.slash_command(name="quote", description="quote")
async def get_quote(ctx):
    response = requests.get("https://zenquotes.io/api/random")
    json_data = json.loads(response.text)
    quote = json_data[0]['q'] + " -" + json_data[0]['a']
    await ctx.respond(quote)



bot.run(token)
