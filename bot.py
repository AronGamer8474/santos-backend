import os
import discord
import requests

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
CHANNEL_ID = 1549530611683950692

BACKEND_URL = "https://santos-backend-oya3.onrender.com"
ADMIN_KEY = os.environ["ADMIN_KEY"]

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"Discord bot logged in as {client.user}")


@client.event
async def on_message(message):
    # Ignore the bot's own messages
    if message.author.bot:
        return

    # Only listen to your Santos announcement channel
    if message.channel.id != CHANNEL_ID:
        return

    # Only respond to !announce
    if not message.content.startswith("!announce "):
        return

    text = message.content[len("!announce "):].strip()

    if not text:
        return

    try:
        response = requests.post(
            f"{BACKEND_URL}/announce",
            headers={
                "X-Admin-Key": ADMIN_KEY,
                "Content-Type": "application/json",
            },
            json={
                "title": "Santos",
                "text": text,
                "duration": 15,
                "sound": "default",
            },
            timeout=10,
        )

        if response.ok:
            data = response.json()
            await message.add_reaction("✅")
            print(f"Announcement sent: #{data.get('id')}")
        else:
            await message.add_reaction("❌")
            print(f"Backend error: {response.status_code} {response.text}")

    except Exception as e:
        await message.add_reaction("❌")
        print("Failed to send announcement:", e)


client.run(DISCORD_TOKEN)
