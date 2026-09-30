import os
import re
import html
import threading
import traceback

import aiohttp
import discord
from discord import Intents
from flask import Flask


# ============================================================
# ENVIRONMENT
# ============================================================

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN not found")

if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN not found")

if not CHAT_ID:
    raise RuntimeError("CHAT_ID not found")


# ============================================================
# CONFIGURATION
# ============================================================

ALLOWED_CHANNELS = {
    1554747710089990244,
}


# ============================================================
# DISCORD CLIENT
# ============================================================

intents = Intents.default()

# Required for reading normal Discord message content
intents.message_content = True

client = discord.Client(
    intents=intents
)


# ============================================================
# TELEGRAM SESSION
# ============================================================

session = None


async def get_session():

    global session

    if session is None or session.closed:

        session = aiohttp.ClientSession()

    return session


# ============================================================
# LOG HELPERS
# ============================================================

def log_header(title):

    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def log_value(name, value):

    print(
        f"[INFO] {name}: {value}"
    )


# ============================================================
# TELEGRAM API
# ============================================================

async def telegram(
    method,
    data=None,
    json_data=None
):

    log_header(
        f"📡 TELEGRAM API REQUEST: {method}"
    )

    print(
        "[TELEGRAM] Preparing request..."
    )

    print(
        f"[TELEGRAM] Chat ID: {CHAT_ID}"
    )

    if data:

        print(
            "[TELEGRAM] Request type: FORM DATA"
        )

        for key, value in data.items():

            if key in {
                "text",
                "caption",
                "photo",
                "document",
                "chat_id",
            }:

                print(
                    f"[TELEGRAM] {key}: "
                    f"{str(value)[:1000]}"
                )

    if json_data:

        print(
            "[TELEGRAM] Request type: JSON"
        )

        print(
            f"[TELEGRAM] JSON keys: "
            f"{list(json_data.keys())}"
        )

    s = await get_session()

    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_TOKEN}/{method}"
    )

    try:

        print(
            "[TELEGRAM] Sending HTTP request..."
        )

        if json_data is not None:

            async with s.post(
                url,
                json=json_data
            ) as resp:

                status = resp.status
                result = await resp.text()

        else:

            async with s.post(
                url,
                data=data
            ) as resp:

                status = resp.status
                result = await resp.text()

        print(
            f"[TELEGRAM] HTTP STATUS: {status}"
        )

        print(
            f"[TELEGRAM] API RESPONSE:"
        )

        print(
            result
        )

        if status == 200:

            print(
                "✅ [TELEGRAM] HTTP request successful"
            )

        else:

            print(
                "❌ [TELEGRAM] HTTP request failed"
            )

        return result

    except Exception as e:

        print()
        print("=" * 70)
        print("❌ TELEGRAM REQUEST EXCEPTION")
        print("=" * 70)

        print(
            "Error type:",
            type(e).__name__
        )

        print(
            "Error:",
            repr(e)
        )

        traceback.print_exc()

        print("=" * 70)

        return ""


# ============================================================
# TELEGRAM SEND MESSAGE
# ============================================================

async def send_message(text):

    if not text:

        print(
            "⚠️ [TELEGRAM] Empty text - nothing to send"
        )

        return False

    log_header(
        "➡️ SENDING TEXT TO TELEGRAM"
    )

    print(
        f"[TELEGRAM] Text length: {len(text)}"
    )

    print(
        "[TELEGRAM] Text preview:"
    )

    print(
        text[:3000]
    )

    data = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }

    result = await telegram(
        "sendMessage",
        data=data
    )

    if '"ok":true' in result:

        print(
            "✅ [TELEGRAM] TEXT SENT SUCCESSFULLY"
        )

        return True

    print(
        "❌ [TELEGRAM] TEXT SEND FAILED"
    )

    return False


# ============================================================
# TELEGRAM SEND PHOTO
# ============================================================

async def send_photo(
    url,
    caption=None
):

    log_header(
        "➡️ SENDING PHOTO TO TELEGRAM"
    )

    print(
        f"[TELEGRAM] Photo URL: {url}"
    )

    if caption:

        print(
            f"[TELEGRAM] Caption length: "
            f"{len(caption)}"
        )

        print(
            "[TELEGRAM] Caption:"
        )

        print(
            caption[:3000]
        )

    data = {
        "chat_id": CHAT_ID,
        "photo": url,
    }

    if caption:

        # Telegram caption limit
        if len(caption) <= 1024:

            data["caption"] = caption
            data["parse_mode"] = "HTML"

        else:

            print(
                "⚠️ [TELEGRAM] Caption is longer "
                "than Telegram limit"
            )

    result = await telegram(
        "sendPhoto",
        data=data
    )

    if '"ok":true' in result:

        print(
            "✅ [TELEGRAM] PHOTO SENT SUCCESSFULLY"
        )

        return True

    print(
        "❌ [TELEGRAM] PHOTO SEND FAILED"
    )

    return False


# ============================================================
# TELEGRAM SEND DOCUMENT
# ============================================================

async def send_document(
    url,
    caption=None
):

    log_header(
        "➡️ SENDING DOCUMENT TO TELEGRAM"
    )

    print(
        f"[TELEGRAM] Document URL: {url}"
    )

    print(
        f"[TELEGRAM] Caption: {caption}"
    )

    data = {
        "chat_id": CHAT_ID,
        "document": url,
    }

    if caption:

        if len(caption) <= 1024:

            data["caption"] = caption
            data["parse_mode"] = "HTML"

    result = await telegram(
        "sendDocument",
        data=data
    )

    if '"ok":true' in result:

        print(
            "✅ [TELEGRAM] DOCUMENT SENT SUCCESSFULLY"
        )

        return True

    print(
        "❌ [TELEGRAM] DOCUMENT SEND FAILED"
    )

    return False


# ============================================================
# TELEGRAM STARTUP TEST
# ============================================================

async def test_telegram_connection():

    log_header(
        "🧪 TELEGRAM CONNECTION TEST"
    )

    print(
        "[TEST] Calling getMe..."
    )

    result = await telegram(
        "getMe"
    )

    if '"ok":true' in result:

        print(
            "✅ TELEGRAM TOKEN IS VALID"
        )

        print(
            "[TEST] Telegram bot connection is working"
        )

        return True

    print(
        "❌ TELEGRAM TOKEN TEST FAILED"
    )

    print(
        "[TEST] Check TELEGRAM_TOKEN"
    )

    return False


# ============================================================
# EMOJI MAP
# ============================================================

EMOJI_MAP = {

    # Flags
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
    ":flag_ca:": "🇨🇦",
    ":flag_au:": "🇦🇺",
    ":flag_nz:": "🇳🇿",
    ":flag_jp:": "🇯🇵",
    ":flag_cn:": "🇨🇳",
    ":flag_kr:": "🇰🇷",
    ":flag_in:": "🇮🇳",
    ":flag_br:": "🇧🇷",
    ":flag_mx:": "🇲🇽",

    # Symbols
    ":white_check_mark:": "✅",
    ":heavy_check_mark:": "✔️",
    ":ballot_box_with_check:": "☑️",

    ":x:": "❌",
    ":heavy_multiplication_x:": "✖️",

    ":warning:": "⚠️",

    ":no_entry:": "⛔",
    ":no_entry_sign:": "🚫",

    ":question:": "❓",
    ":grey_question:": "❔",

    ":exclamation:": "❗",
    ":grey_exclamation:": "❕",

    ":information_source:": "ℹ️",

    # Arrows
    ":arrow_up:": "⬆️",
    ":arrow_down:": "⬇️",
    ":arrow_left:": "⬅️",
    ":arrow_right:": "➡️",

    ":arrow_upper_right:": "↗️",
    ":arrow_upper_left:": "↖️",
    ":arrow_lower_right:": "↘️",
    ":arrow_lower_left:": "↙️",

    ":arrow_double_up:": "⏫",
    ":arrow_double_down:": "⏬",

    # Transport
    ":car:": "🚗",
    ":red_car:": "🚗",
    ":taxi:": "🚕",
    ":truck:": "🚚",
    ":articulated_lorry:": "🚛",
    ":bus:": "🚌",
    ":blue_car:": "🚙",
    ":motorcycle:": "🏍️",
    ":bike:": "🚲",
    ":fuelpump:": "⛽",
    ":rotating_light:": "🚨",

    # Faces
    ":grinning:": "😀",
    ":smiley:": "😃",
    ":smile:": "😄",
    ":grin:": "😁",
    ":laughing:": "😆",
    ":satisfied:": "😆",
    ":sweat_smile:": "😅",
    ":joy:": "😂",

    ":wink:": "😉",
    ":blush:": "😊",

    ":heart_eyes:": "😍",
    ":kissing_heart:": "😘",

    ":thinking:": "🤔",
    ":sunglasses:": "😎",

    ":cry:": "😢",
    ":sob:": "😭",

    ":angry:": "😠",
    ":rage:": "😡",

    ":confused:": "😕",
    ":neutral_face:": "😐",
    ":expressionless:": "😑",

    ":scream:": "😱",
    ":fearful:": "😨",
    ":sleeping:": "😴",

    ":poop:": "💩",
    ":shit:": "💩",

    # Hands
    ":+1:": "👍",
    ":thumbsup:": "👍",
    ":-1:": "👎",
    ":thumbsdown:": "👎",

    ":ok_hand:": "👌",
    ":clap:": "👏",
    ":wave:": "👋",
    ":pray:": "🙏",
    ":muscle:": "💪",

    ":point_up:": "☝️",
    ":point_right:": "👉",
    ":point_left:": "👈",
    ":point_down:": "👇",

    # Hearts
    ":heart:": "❤️",
    ":yellow_heart:": "💛",
    ":green_heart:": "💚",
    ":blue_heart:": "💙",
    ":purple_heart:": "💜",
    ":black_heart:": "🖤",

    ":broken_heart:": "💔",
    ":two_hearts:": "💕",
    ":sparkling_heart:": "💖",

    # Objects
    ":fire:": "🔥",
    ":star:": "⭐",
    ":star2:": "🌟",
    ":sparkles:": "✨",
    ":boom:": "💥",
    ":zap:": "⚡",

    ":sunny:": "☀️",
    ":cloud:": "☁️",
    ":snowflake:": "❄️",
    ":rainbow:": "🌈",

    ":eyes:": "👀",
    ":eye:": "👁️",

    ":100:": "💯",

    ":checkered_flag:": "🏁",
    ":tada:": "🎉",
    ":gift:": "🎁",
    ":bell:": "🔔",

    ":lock:": "🔒",
    ":unlock:": "🔓",

    ":heavy_plus_sign:": "➕",
    ":heavy_minus_sign:": "➖",
    ":heavy_dollar_sign:": "💲",

    ":copyright:": "©️",
    ":registered:": "®️",
    ":tm:": "™️",
}


emoji_pattern = re.compile(
    "|".join(
        re.escape(x)
        for x in sorted(
            EMOJI_MAP.keys(),
            key=len,
            reverse=True
        )
    )
)


# ============================================================
# DISCORD CUSTOM EMOJI
# ============================================================

CUSTOM_EMOJI_PATTERN = re.compile(
    r"<(a?):([a-zA-Z0-9_]+):(\d+)>"
)


def convert_custom_emoji(match):

    animated = match.group(1)
    name = match.group(2)
    emoji_id = match.group(3)

    shortcode = f":{name}:"

    if shortcode in EMOJI_MAP:

        return EMOJI_MAP[
            shortcode
        ]

    # Keep unknown custom emoji name.
    if animated:

        return f":{name}:"

    return f":{name}:"


# ============================================================
# CONVERT EMOJI
# ============================================================

def convert_emoji(text):

    if not text:
        return ""

    text = str(text)

    # Discord custom emoji
    text = CUSTOM_EMOJI_PATTERN.sub(
        convert_custom_emoji,
        text
    )

    # Standard Discord emoji shortcodes
    text = emoji_pattern.sub(
        lambda match: EMOJI_MAP[
            match.group(0)
        ],
        text
    )

    return text


# ============================================================
# DISCORD MARKDOWN LINKS
# ============================================================

DISCORD_LINK_PATTERN = re.compile(
    r"\[([^\]]+)\]\((https?://[^\s\)]+)\)"
)


def convert_discord_links(text):

    if not text:
        return ""

    def replace_link(match):

        label = html.escape(
            match.group(1),
            quote=False
        )

        url = html.escape(
            match.group(2),
            quote=True
        )

        return (
            f'<a href="{url}">'
            f'{label}'
            f'</a>'
        )

    return DISCORD_LINK_PATTERN.sub(
        replace_link,
        text
    )


# ============================================================
# CONVERT TEXT TO TELEGRAM HTML
# ============================================================

def convert_text(text):

    if not text:
        return ""

    text = str(text)

    text = text.replace(
        "\r\n",
        "\n"
    )

    text = text.replace(
        "\r",
        "\n"
    )

    # Emojis
    text = convert_emoji(
        text
    )

    # Discord markdown links
    text = convert_discord_links(
        text
    )

    # Protect generated Telegram links
    protected_links = {}

    def protect_link(match):

        key = (
            f"___TELEGRAM_LINK_"
            f"{len(protected_links)}___"
        )

        protected_links[key] = match.group(0)

        return key

    text = re.sub(
        r'<a href="[^"]+">.*?</a>',
        protect_link,
        text,
        flags=re.DOTALL
    )

    # Escape HTML
    text = html.escape(
        text,
        quote=False
    )

    # Restore links
    for key, value in protected_links.items():

        text = text.replace(
            html.escape(key),
            value
        )

    # Bold
    text = re.sub(
        r"\*\*(.+?)\*\*",
        r"<b>\1</b>",
        text,
        flags=re.DOTALL
    )

    # Italic
    text = re.sub(
        r"(?<!\*)\*([^*\n]+)\*(?!\*)",
        r"<i>\1</i>",
        text
    )

    # Underline
    text = re.sub(
        r"__([^_]+)__",
        r"<u>\1</u>",
        text
    )

    # Strikethrough
    text = re.sub(
        r"~~(.+?)~~",
        r"<s>\1</s>",
        text,
        flags=re.DOTALL
    )

    # Inline code
    text = re.sub(
        r"`([^`]+)`",
        r"<code>\1</code>",
        text
    )

    # Avoid huge empty spaces
    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    return text.strip()


# ============================================================
# EMBED → TEXT
# ============================================================

def embed_to_text(embed):

    parts = []

    # Author
    if (
        embed.author
        and embed.author.name
    ):

        author = convert_text(
            embed.author.name
        )

        if author:

            parts.append(
                author
            )

    # Title
    if embed.title:

        title = convert_text(
            embed.title
        )

        if title:

            parts.append(
                title
            )

    # Embed URL
    if embed.url:

        url = str(
            embed.url
        ).strip()

        if url:

            safe_url = html.escape(
                url,
                quote=True
            )

            parts.append(
                f'<a href="{safe_url}">'
                f'{safe_url}'
                f'</a>'
            )

    # Description
    if embed.description:

        description = convert_text(
            embed.description
        )

        if description:

            parts.append(
                description
            )

    # Fields
    for field in embed.fields:

        name = convert_text(
            field.name or ""
        )

        value = convert_text(
            field.value or ""
        )

        if name and value:

            parts.append(
                f"<b>{name}</b>\n"
                f"{value}"
            )

        elif value:

            parts.append(
                value
            )

        elif name:

            parts.append(
                f"<b>{name}</b>"
            )

    # Footer
    if (
        embed.footer
        and embed.footer.text
    ):

        footer = convert_text(
            embed.footer.text
        )

        if footer:

            parts.append(
                footer
            )

    return "\n\n".join(
        parts
    ).strip()


# ============================================================
# GET DRIVER / AUTHOR
# ============================================================

def get_driver_name(message):

    for embed in message.embeds:

        if (
            embed.author
            and embed.author.name
        ):

            return embed.author.name

    if (
        message.author
        and message.author.name
    ):

        return message.author.name

    return None


# ============================================================
# DISCORD READY
# ============================================================

@client.event
async def on_ready():

    log_header(
        "✅ DISCORD BOT ONLINE"
    )

    print(
        f"[DISCORD] Bot: {client.user}"
    )

    print(
        f"[DISCORD] Bot ID: {client.user.id}"
    )

    print(
        f"[DISCORD] Guild count: "
        f"{len(client.guilds)}"
    )

    print()

    print(
        "[DISCORD] Allowed channels:"
    )

    for channel_id in ALLOWED_CHANNELS:

        channel = client.get_channel(
            channel_id
        )

        if channel:

            print(
                f"✅ {channel.guild.name} "
                f"-> #{channel.name} "
                f"-> {channel.id}"
            )

        else:

            print(
                f"❌ Cannot access channel "
                f"{channel_id}"
            )

    # Telegram startup test
    try:

        await test_telegram_connection()

    except Exception as e:

        print(
            "❌ Telegram startup test error:",
            repr(e)
        )

    log_header(
        "🟢 BRIDGE READY"
    )

    print(
        "[READY] Waiting for Discord messages..."
    )


# ============================================================
# DISCORD MESSAGE EVENT
# ============================================================

@client.event
async def on_message(message):

    # ========================================================
    # THIS MUST APPEAR IF DISCORD DELIVERS THE EVENT
    # ========================================================

    log_header(
        "📨 DISCORD MESSAGE EVENT RECEIVED"
    )

    print(
        f"[DISCORD] Author       : "
        f"{message.author}"
    )

    print(
        f"[DISCORD] Author ID    : "
        f"{message.author.id}"
    )

    print(
        f"[DISCORD] Author Bot   : "
        f"{message.author.bot}"
    )

    print(
        f"[DISCORD] Webhook ID   : "
        f"{message.webhook_id}"
    )

    print(
        f"[DISCORD] Channel      : "
        f"{message.channel}"
    )

    print(
        f"[DISCORD] Channel ID   : "
        f"{message.channel.id}"
    )

    print(
        f"[DISCORD] Guild        : "
        f"{message.guild}"
    )

    print(
        f"[DISCORD] Content      : "
        f"{message.content}"
    )

    print(
        f"[DISCORD] Embeds       : "
        f"{len(message.embeds)}"
    )

    print(
        f"[DISCORD] Attachments  : "
        f"{len(message.attachments)}"
    )

    print(
        f"[DISCORD] Stickers     : "
        f"{len(message.stickers)}"
    )

    # ========================================================
    # EMBED DEBUG
    # ========================================================

    if message.embeds:

        print()
        print(
            "[DISCORD] EMBED DETAILS"
        )

        for index, embed in enumerate(
            message.embeds,
            start=1
        ):

            print(
                f"--- Embed #{index} ---"
            )

            print(
                f"Title       : "
                f"{embed.title}"
            )

            print(
                f"Description : "
                f"{embed.description}"
            )

            print(
                f"URL         : "
                f"{embed.url}"
            )

            print(
                f"Fields      : "
                f"{len(embed.fields)}"
            )

            print(
                f"Image       : "
                f"{embed.image.url if embed.image else None}"
            )

            print(
                f"Thumbnail   : "
                f"{embed.thumbnail.url if embed.thumbnail else None}"
            )

            if embed.footer:

                print(
                    f"Footer      : "
                    f"{embed.footer.text}"
                )

            if embed.author:

                print(
                    f"Embed Author: "
                    f"{embed.author.name}"
                )

    # ========================================================
    # ATTACHMENT DEBUG
    # ========================================================

    if message.attachments:

        print()
        print(
            "[DISCORD] ATTACHMENT DETAILS"
        )

        for attachment in message.attachments:

            print(
                f"--- Attachment ---"
            )

            print(
                f"Filename    : "
                f"{attachment.filename}"
            )

            print(
                f"ContentType : "
                f"{attachment.content_type}"
            )

            print(
                f"Size        : "
                f"{attachment.size}"
            )

            print(
                f"URL         : "
                f"{attachment.url}"
            )

    # ========================================================
    # IGNORE OWN BOT MESSAGE
    # ========================================================

    if (
        client.user
        and message.author.id == client.user.id
    ):

        print(
            "⏭️ [FILTER] Ignored own bot message"
        )

        return

    # ========================================================
    # CHANNEL FILTER
    # ========================================================

    print()

    print(
        "[FILTER] Checking channel..."
    )

    print(
        f"[FILTER] Current: "
        f"{message.channel.id}"
    )

    print(
        f"[FILTER] Allowed: "
        f"{ALLOWED_CHANNELS}"
    )

    if message.channel.id not in ALLOWED_CHANNELS:

        print(
            "❌ [FILTER] CHANNEL NOT ALLOWED"
        )

        print(
            "❌ Message will NOT be sent to Telegram"
        )

        return

    print(
        "✅ [FILTER] TARGET CHANNEL MATCHED"
    )

    # ========================================================
    # PROCESS
    # ========================================================

    try:

        log_header(
            "⚙️ PYTHON MESSAGE PROCESSING"
        )

        driver = get_driver_name(
            message
        )

        print(
            f"[PYTHON] Author/Driver: "
            f"{driver}"
        )

        # ====================================================
        # NORMAL TEXT
        # ====================================================

        if message.content:

            print(
                "[PYTHON] Processing normal message text"
            )

            text = convert_text(
                message.content
            )

            print(
                "[PYTHON] Converted text:"
            )

            print(
                text
            )

            await send_message(
                text
            )

        # ====================================================
        # EMBEDS
        # ====================================================

        for index, embed in enumerate(
            message.embeds,
            start=1
        ):

            print()
            print(
                f"[PYTHON] Processing Embed #{index}"
            )

            embed_text = embed_to_text(
                embed
            )

            print(
                "[PYTHON] Converted embed:"
            )

            print(
                embed_text
            )

            if embed_text:

                await send_message(
                    embed_text
                )

            # Embed image
            if (
                embed.image
                and embed.image.url
            ):

                print(
                    "[PYTHON] Embed contains IMAGE"
                )

                await send_photo(
                    embed.image.url
                )

            # Embed thumbnail
            if (
                embed.thumbnail
                and embed.thumbnail.url
            ):

                print(
                    "[PYTHON] Embed contains THUMBNAIL"
                )

                await send_photo(
                    embed.thumbnail.url
                )

        # ====================================================
        # ATTACHMENTS
        # ====================================================

        for attachment in message.attachments:

            print()
            print(
                "[PYTHON] Processing attachment"
            )

            print(
                f"[PYTHON] Filename: "
                f"{attachment.filename}"
            )

            content_type = (
                attachment.content_type
                or ""
            ).lower()

            if content_type.startswith(
                "image/"
            ):

                print(
                    "🖼️ [PYTHON] Attachment is IMAGE"
                )

                await send_photo(
                    attachment.url,
                    attachment.filename
                )

            else:

                print(
                    "📄 [PYTHON] Attachment is DOCUMENT"
                )

                await send_document(
                    attachment.url,
                    attachment.filename
                )

        # ====================================================
        # FINAL
        # ====================================================

        log_header(
            "✅ MESSAGE PROCESSING COMPLETED"
        )

    except Exception as e:

        log_header(
            "❌ MESSAGE PROCESSING ERROR"
        )

        print(
            "Error type:",
            type(e).__name__
        )

        print(
            "Error:",
            repr(e)
        )

        traceback.print_exc()

        print(
            "=" * 70
        )


# ============================================================
# FLASK
# ============================================================

app = Flask(
    __name__
)


@app.route("/")
def home():

    return (
        "Discord -> Telegram Bridge is running",
        200
    )


@app.route("/health")
def health():

    return (
        "OK",
        200
    )


# ============================================================
# WEB SERVER
# ============================================================

def run_web_server():

    port = int(
        os.getenv(
            "PORT",
            "10000"
        )
    )

    log_header(
        "🌐 STARTING RENDER WEB SERVER"
    )

    print(
        f"[RENDER] Port: {port}"
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    log_header(
        "🚀 STARTING DISCORD → TELEGRAM BRIDGE"
    )

    print(
        "[STARTUP] Python process started"
    )

    print(
        f"[STARTUP] Allowed channels: "
        f"{ALLOWED_CHANNELS}"
    )

    print(
        "[STARTUP] Message Content Intent: "
        f"{intents.message_content}"
    )

    # --------------------------------------------------------
    # Start Flask
    # --------------------------------------------------------

    web_thread = threading.Thread(
        target=run_web_server,
        daemon=True
    )

    web_thread.start()

    print(
        "✅ [STARTUP] Flask thread started"
    )

    # --------------------------------------------------------
    # Start Discord
    # --------------------------------------------------------

    print(
        "➡️ [STARTUP] Connecting to Discord..."
    )

    try:

        client.run(
            DISCORD_TOKEN
        )

    except Exception as e:

        log_header(
            "❌ DISCORD CLIENT CRASHED"
        )

        print(
            "Error type:",
            type(e).__name__
        )

        print(
            "Error:",
            repr(e)
        )

        traceback.print_exc()

        raise
