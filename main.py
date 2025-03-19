from dotenv import load_dotenv
import discord
import requests
import json
import base64
import re
import os 
from keep_alive import keep_alive

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

GITHUB_API_URL = "https://api.github.com/repos/yuvic123/paid/contents/paidlist"

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")  

ALLOWED_USERS = [
    598460565387476992
]

def update_github_file(new_content, sha):
    updated_content = base64.b64encode(new_content.encode('utf-8')).decode('utf-8')

    data = {
        "message": "Update HWID list",
        "content": updated_content,
        "sha": sha
    }

    response = requests.put(
        GITHUB_API_URL,
        headers={"Authorization": f"token {GITHUB_TOKEN}"},
        json=data
    )

    if response.status_code == 200:
        print("File updated successfully!")
    else:
        print(f"Failed to update file: {response.status_code} - {response.text}")

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    await client.change_presence(activity=discord.Game(name="Listening to Commands"))
    
@client.event
async def on_message(message):
    if not message.content.startswith((".white add ", ".white remove ", ".hwidlist", ".replacehwid ", ".hwidcheck ")):
        return

    if message.author.id not in ALLOWED_USERS:
        await message.channel.send("❌ You don't have permission to use this command.")
        return

    response = requests.get(GITHUB_API_URL, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    if response.status_code != 200:
        await message.channel.send(f"❌ Error fetching file: {response.status_code} - {response.text}")
        return

    file_data = response.json()
    file_content = base64.b64decode(file_data["content"]).decode('utf-8')

    existing_hwids = re.findall(r'"(.*?)"', file_content)

    if message.content.startswith(".white add "):
        try:
            target_hwid = message.content.split(" ")[2].strip()
        except IndexError:
            await message.channel.send("❌ Invalid HWID format. Please provide a valid HWID.")
            return

        if target_hwid in existing_hwids:
            await message.channel.send(f"⚠️ HWID `{target_hwid}` is already in the list.")
        else:
            existing_hwids.append(target_hwid)
            await message.channel.send(f"✅ Added HWID `{target_hwid}` to the list!")

    elif message.content.startswith(".white remove "):
        try:
            target_hwid = message.content.split(" ")[2].strip()
        except IndexError:
            await message.channel.send("❌ Invalid HWID format. Please provide a valid HWID.")
            return

        if target_hwid in existing_hwids:
            existing_hwids.remove(target_hwid)
            await message.channel.send(f"✅ Removed HWID `{target_hwid}` from the list!")
        else:
            await message.channel.send(f"⚠️ HWID `{target_hwid}` is not in the list.")

    elif message.content.startswith(".hwidlist"):
        if not existing_hwids:
            embed = discord.Embed(
                title="🔒 Authorized HWIDs",
                description="No HWIDs are currently listed.",
                color=discord.Color.blue()
            )
            embed.set_footer(text="Use .white add <HWID> to add new HWIDs")
        else:
            display_list = "\n".join([f"`{hwid}`" for hwid in existing_hwids])

            embed = discord.Embed(
                title="🔒 Authorized HWIDs",
                description=display_list,
                color=discord.Color.purple()
            )
            embed.set_footer(text=f"Total HWIDs: {len(existing_hwids)} | Use .white remove <HWID> to delete")

        await message.channel.send(embed=embed)

    elif message.content.startswith(".replacehwid"):
        try:
            _, old_hwid, new_hwid = message.content.split(" ")
            old_hwid, new_hwid = old_hwid.strip(), new_hwid.strip()
        except (ValueError, IndexError):
            await message.channel.send("❌ Invalid format. Use `.replacehwid <old_hwid> <new_hwid>`")
            return

        if old_hwid in existing_hwids:
            existing_hwids.remove(old_hwid)
            existing_hwids.append(new_hwid)
            await message.channel.send(f"✅ Successfully replaced **{old_hwid}** with **{new_hwid}**.")
        else:
            await message.channel.send(f"⚠️ HWID `{old_hwid}` not found in the list.")

    elif message.content.startswith(".hwidcheck"):
        try:
            target_hwid = message.content.split(" ")[1].strip()
        except (ValueError, IndexError):
            await message.channel.send("❌ Invalid HWID format. Please provide a valid HWID.")
            return

        if target_hwid in existing_hwids:
            await message.channel.send(f"✅ HWID `{target_hwid}` **is authorized**.")
        else:
            await message.channel.send(f"❌ HWID `{target_hwid}` **is not authorized**.")

    updated_lua_content = f"return {{{', '.join(f'\"{hwid}\"' for hwid in existing_hwids)}}}"

    update_github_file(updated_lua_content, file_data["sha"])

keep_alive()
client.run(DISCORD_TOKEN)
