import os
import re
import html
import threading

import aiohttp
import discord
from discord import Intents
from flask import Flask


# ==========================
# Environment Variables
# ==========================

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN not found")

if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN not found")

if not CHAT_ID:
    raise RuntimeError("CHAT_ID not found")


# ==========================
# Discord Configuration
# ==========================

ALLOWED_CHANNELS = {
    1554747710089990244
}

intents = Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


# ==========================
# Telegram Session
# ==========================

session = None


async def get_session():
    global session

    if session is None or session.closed:
        session = aiohttp.ClientSession()

    return session


async def telegram(method: str, data: dict):
    s = await get_session()

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{method}"

    async with s.post(url, data=data) as resp:
        result = await resp.text()

        if resp.status != 200:
            print("Telegram Error")
            print("Status:", resp.status)
            print(result)

        return result


# ==========================
# Telegram Send Functions
# ==========================

async def send_message(text):
    if not text:
        return

    text = html.escape(text)

    await telegram(
        "sendMessage",
        {
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
    )


async def send_photo(url, caption=None):
    data = {
        "chat_id": CHAT_ID,
        "photo": url
    }

    if caption:
        data["caption"] = html.escape(caption)
        data["parse_mode"] = "HTML"

    await telegram("sendPhoto", data)


async def send_document(url, caption=None):
    data = {
        "chat_id": CHAT_ID,
        "document": url
    }

    if caption:
        data["caption"] = html.escape(caption)
        data["parse_mode"] = "HTML"

    await telegram("sendDocument", data)


# ==========================
# Emoji Conversion
# ==========================

EMOJI_MAP = {
    ":flag_ir:": "🇮🇷",
    ":flag_us:": "🇺🇸",
    ":flag_gb:": "🇬🇧",
    ":flag_uk:": "🇬🇧",
    ":flag_de:": "🇩🇪",
    ":flag_fr:": "🇫🇷",
    ":flag_it:": "🇮🇹",
    ":flag_es:": "🇪🇸",
    ":flag_pl:": "🇵🇱",
    ":flag_nl:": "🇳🇱",
    ":flag_be:": "🇧🇪",
    ":flag_tr:": "🇹🇷",
    ":flag_ru:": "🇷🇺",
    ":arrow_up:": "⬆️",
    ":arrow_double_up:": "⏫",
    ":white_check_mark:": "✅",
    ":x:": "❌",
    ":warning:": "⚠️"
}

emoji_pattern = re.compile(
    "|".join(re.escape(x) for x in EMOJI_MAP.keys())
)


def convert_emoji(text):
    if not text:
        return ""

    return emoji_pattern.sub(
        lambda m: EMOJI_MAP[m.group(0)],
        text
    )


# ==========================
# Discord Embed Conversion
# ==========================

def embed_to_text(embed: discord.Embed, driver=None):

    lines = []

    if driver:
        lines.append(f"👤 {driver}")
        lines.append("")

    if embed.title:
        lines.append(
            f"📦 {convert_emoji(embed.title)}"
        )

    if embed.description:
        lines.append(
            convert_emoji(embed.description)
        )

    if embed.fields:

        lines.append("")

        for field in embed.fields:

            name = convert_emoji(
                field.name or ""
            )

            value = convert_emoji(
                field.value or ""
            )

            if not value:
                continue

            lines.append(f"<b>{name}</b>")
            lines.append(value)
            lines.append("")

    if embed.footer and embed.footer.text:

        lines.append("--------------------")

        lines.append(
            convert_emoji(
                embed.footer.text
            )
        )

    return "\n".join(lines).strip()


# ==========================
# Driver Detection
# ==========================

def get_driver_name(message):

    for embed in message.embeds:

        if embed.author and embed.author.name:
            return embed.author.name

    if message.author and message.author.name:

        name = message.author.name

        if "webhook" not in name.lower():
            return name

    return None


# ==========================
# Discord Ready
# ==========================

@client.event
async def on_ready():

    print("=" * 60)
    print(f"✅ Logged in as {client.user}")
    print(f"Guilds : {len(client.guilds)}")
    print("=" * 60)

    for channel_id in ALLOWED_CHANNELS:

        channel = client.get_channel(channel_id)

        if channel:

            print(
                f"✅ {channel.guild.name} -> #{channel.name}"
            )

        else:

            print(
                f"❌ Cannot access channel {channel_id}"
            )

    print("=" * 60)


# ==========================
# Discord Messages
# ==========================

@client.event
async def on_message(message):

    if message.author.id == client.user.id:
        return

    if message.channel.id not in ALLOWED_CHANNELS:
        return

    print()
    print("=" * 60)
    print("📨 Message received")
    print(f"Channel : {message.channel.name}")
    print(f"Author  : {message.author}")
    print(f"Webhook : {message.webhook_id}")
    print(f"Embeds  : {len(message.embeds)}")
    print(f"Files   : {len(message.attachments)}")
    print("=" * 60)

    driver = get_driver_name(message)

    try:

        # ==========================
        # Normal Message
        # ==========================

        if message.content.strip():

            text = convert_emoji(
                message.content
            )

            if driver:
                text = f"👤 {driver}\n\n{text}"

            print("➡️ Sending text to Telegram...")

            await send_message(text)

            print("✅ Text sent to Telegram")

        # ==========================
        # Embeds
        # ==========================

        for embed in message.embeds:

            text = embed_to_text(
                embed,
                driver
            )

            if text:

                print("➡️ Sending embed to Telegram...")

                await send_message(text)

                print("✅ Embed sent to Telegram")

            if embed.image and embed.image.url:

                print("➡️ Sending embed image...")

                await send_photo(
                    embed.image.url,
                    driver
                )

                print("✅ Embed image sent")

            elif embed.thumbnail and embed.thumbnail.url:

                print("➡️ Sending embed thumbnail...")

                await send_photo(
                    embed.thumbnail.url,
                    driver
                )

                print("✅ Embed thumbnail sent")

        # ==========================
        # Attachments
        # ==========================

        for attachment in message.attachments:

            ctype = attachment.content_type or ""

            print(
                f"Attachment : {attachment.filename}"
            )

            if ctype.startswith("image"):

                await send_photo(
                    attachment.url,
                    attachment.filename
                )

            else:

                await send_document(
                    attachment.url,
                    attachment.filename
                )

        print("✅ Message processing completed")

    except Exception as e:

        print("=" * 60)
        print("❌ ERROR")
        print(type(e).__name__)
        print(e)
        print("=" * 60)


# ==========================
# Flask / Render Web Server
# ==========================

app = Flask(__name__)


@app.route("/")
def home():

    return "HaulMP Bridge is running", 200


@app.route("/health")
def health():

    return "OK", 200


def run_web_server():

    port = int(
        os.getenv("PORT", "10000")
    )

    print("=" * 60)
    print("🌐 Starting Render Web Server")
    print(f"Port: {port}")
    print("=" * 60)

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False
    )


# ==========================
# Start Bot + Web Server
# ==========================

if __name__ == "__main__":

    web_thread = threading.Thread(
        target=run_web_server,
        daemon=True
    )

    web_thread.start()

    print("=" * 60)
    print("🚀 Starting HaulMP Bridge")
    print("=" * 60)

    client.run(DISCORD_TOKEN)
