import os
import re
import html
import asyncio
import aiohttp
import discord
from discord import Intents

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
# Discord Settings
# ==========================

ALLOWED_CHANNELS = {
    1554747710089990244
}

intents = Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# ==========================
# Telegram
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
            print(resp.status)
            print(result)

        return result


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
# Emoji Mapping
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
# Embed Parser
# ==========================

def embed_to_text(embed: discord.Embed, driver=None):

    lines = []

    if driver:
        lines.append(f"👤 {driver}")
        lines.append("")

    if embed.title:
        lines.append(f"📦 {convert_emoji(embed.title)}")

    if embed.description:
        lines.append(convert_emoji(embed.description))

    if embed.fields:

        lines.append("")

        for field in embed.fields:

            name = convert_emoji(field.name or "")
            value = convert_emoji(field.value or "")

            if not value:
                continue

            lines.append(f"<b>{name}</b>")
            lines.append(value)
            lines.append("")

    if embed.footer and embed.footer.text:

        lines.append("--------------------")
        lines.append(convert_emoji(embed.footer.text))

    return "\n".join(lines).strip()


# ==========================
# Driver Name
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
# Discord Events
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
            print(f"✅ {channel.guild.name} -> #{channel.name}")
        else:
            print(f"❌ Cannot access channel {channel_id}")

    print("=" * 60)


@client.event
async def on_message(message):

    # پیام خود بات
    if message.author.id == client.user.id:
        return

    # فقط چنل‌های مجاز
    if message.channel.id not in ALLOWED_CHANNELS:
        return

    print(f"\n📨 Message received")
    print(f"Channel : {message.channel.name}")
    print(f"Author  : {message.author}")
    print(f"Webhook : {message.webhook_id}")
    print(f"Embeds  : {len(message.embeds)}")
    print(f"Files   : {len(message.attachments)}")

    driver = get_driver_name(message)

    try:

        # =====================
        # متن معمولی
        # =====================

        if message.content.strip():

            text = convert_emoji(message.content)

            if driver:
                text = f"👤 {driver}\n\n{text}"

            await send_message(text)

        # =====================
        # Embed
        # =====================

        for embed in message.embeds:

            text = embed_to_text(embed, driver)

            if text:
                await send_message(text)

            # تصویر اصلی
            if embed.image and embed.image.url:

                await send_photo(
                    embed.image.url,
                    driver
                )

            # Thumbnail
            elif embed.thumbnail and embed.thumbnail.url:

                await send_photo(
                    embed.thumbnail.url,
                    driver
                )

        # =====================
        # Attachments
        # =====================

        for attachment in message.attachments:

            ctype = attachment.content_type or ""

            print(f"Attachment : {attachment.filename}")

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

    except Exception as e:

        print("=" * 60)
        print("❌ ERROR")
        print(type(e).__name__)
        print(e)
        print("=" * 60)
# ==========================
# Start Bot
# ==========================

client.run(DISCORD_TOKEN)
