import os
import re
import random
import asyncio
import logging
import requests
import tempfile
import math
from guessit import guessit

# The Keep Alive Server
from keep_alive import keep_alive

# ⚠️ Make sure hachoir is installed: pip install hachoir
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata

# Telegram Library Imports
from telegram import Update, ReactionTypeEmoji, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.constants import ParseMode
from telegram.error import BadRequest

# ================= CONFIGURATION =================
# 🔥 NOW PULLS SECURELY FROM RENDER ENVIRONMENT VARIABLES 🔥
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN is missing! Please add it to your Render Environment Variables.")

# ================= UI & API KEYS =================
LOADING_STICKERS = [
    "CAACAgUAAxkBAAEQLstpXRZxNxFMteYSkppBZ63fuBhVtQACFBgAAtDQQVbGUaezY8jttzgE",
    "CAACAgIAAxkBAAEQh0Vpkr5IZlLv91IqBxjc-ZjMIW0JeQACEI0AAv5fcEtLVL-tOoN-qDoE",
    "CAACAgUAAxkBAAEQh0Npkr4_7PwIgwzNtlgWFZgln6HX9QACjiQAAkgC0Fe1pmm8vcmK9DoE",
    "CAACAgIAAxkBAAEQh0Fpkr4yhjz_V-ulAc3-RxoAASt0cCAAAuNuAAK1NYBLhfPrulNjzWY6BA",
    "CAACAgIAAxkBAAEQMCBpXe5yQV2dAAH9B9ijN5mQH6UuM54AAteBAAL18UBI0d94BVfSNXY4BA"
]

IMAGE_LINKS = [
    "https://i.postimg.cc/26ZBtBZr/13.png", "https://i.postimg.cc/PJn8nrWZ/14.png", 
    "https://i.postimg.cc/1Xw1wxDw/photo-2025-10-19-07-30-34.jpg", "https://i.postimg.cc/QtXVtB8K/8.png", 
    "https://i.postimg.cc/y8j8G1XV/9.png", "https://i.postimg.cc/zXjH4NVb/17.png", 
    "https://i.postimg.cc/sggGrLhn/18.png", "https://i.postimg.cc/dtW30QpL/6.png", 
    "https://i.postimg.cc/8C15CQ5y/1.png", "https://i.postimg.cc/gcNtrv0m/2.png", 
    "https://i.postimg.cc/cHD71BBz/3.png", "https://i.postimg.cc/F1XYhY8q/4.png", 
    "https://i.postimg.cc/1tNwGVxC/5.png", "https://i.postimg.cc/139dvs3c/7.png", 
    "https://i.postimg.cc/zDF6KyJX/10.png", "https://i.postimg.cc/fyycVqzd/11.png", 
    "https://i.postimg.cc/cC7txyhz/15.png", "https://i.postimg.cc/kX9tjGXP/16.png", 
    "https://i.postimg.cc/y8pgYTh7/19.png"
]

TMDB_KEYS = [
    'fb7bb23f03b6994dafc674c074d01761', 'e55425032d3d0f371fc776f302e7c09b',
    '8301a21598f8b45668d5711a814f01f6', '8cf43ad9c085135b9479ad5cf6bbcbda',
    'da63548086e399ffc910fbc08526df05', '13e53ff644a8bd4ba37b3e1044ad24f3',
    '269890f657dddf4635473cf4cf456576', 'a2f888b27315e62e471b2d587048f32e',
    '8476a7ab80ad76f0936744df0430e67c', '5622cafbfe8f8cfe358a29c53e19bba0',
    'ae4bd1b6fce2a5648671bfc171d15ba4', '257654f35e3dff105574f97fb4b97035',
    '2f4038e83265214a0dcd6ec2eb3276f5', '9e43f45f94705cc8e1d5a0400d19a7b7',
    'af6887753365e14160254ac7f4345dd2', '06f10fc8741a672af455421c239a1ffc',
    '09ad8ace66eec34302943272db0e8d2c'
]

OMDB_KEYS = [
    '4b447405', 'eb0c0475', '7776cbde', 'ff28f90b', '6c3a2d45',
    'b07b58c8', 'ad04b643', 'a95b5205', '777d9323', '2c2c3314',
    'b5cff164', '89a9f57d', '73a9858a', 'efbd8357'
]

EMOJIS = ["🌟", "🔥", "🎉", "⚡", "🏆", "💎", "💯", "😎", "✨", "🚀"]

logging.basicConfig(level=logging.INFO)

# ================= MASSIVE DATA DICTIONARIES =================
TMDB_GENRES = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime", 
    99: "Documentary", 18: "Drama", 10751: "Family", 14: "Fantasy", 36: "History", 
    27: "Horror", 10402: "Music", 9648: "Mystery", 10749: "Romance", 878: "Sci-Fi", 
    10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western", 10759: "Action & Adv", 
    10762: "Kids", 10763: "News", 10764: "Reality", 10765: "Sci-Fi & Fantasy"
}

LANG_MAP = {
    'hi': 'Hindi', 'en': 'English', 'ja': 'Japanese', 'ta': 'Tamil', 'te': 'Telugu', 
    'ml': 'Malayalam', 'kn': 'Kannada', 'mr': 'Marathi', 'gu': 'Gujarati', 
    'ko': 'Korean', 'es': 'Spanish', 'fr': 'French', 'ru': 'Russian', 'zh': 'Chinese',
    'th': 'Thai', 'in': 'Indonesian', 'vi': 'Vietnamese'
}

# ================= PRECISION UTILITIES =================
def esc(text):
    if not text or str(text).lower() in ['none', 'nan', 'null']: return "N/A"
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def format_size(size_bytes):
    if size_bytes == 0: return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

def pre_clean_filename(filename):
    f = str(filename)
    f = re.sub(r'@[a-zA-Z0-9_]+', '', f)
    f = re.sub(r'(?i)DA Rips', '', f)
    f = re.sub(r'(?i)t\.me/[a-zA-Z0-9_]+', '', f)
    f = re.sub(r'\[.*?\]', '', f)
    f = re.sub(r'[\.\_]+', ' ', f)
    return f.strip()

def detect_languages(filename, guessit_langs):
    found_langs = []
    if guessit_langs:
        if not isinstance(guessit_langs, list): guessit_langs = [guessit_langs]
        for l in guessit_langs:
            lang_str = str(l).lower()
            found_langs.append(LANG_MAP.get(lang_str, lang_str.capitalize()))
            
    fname_lower = filename.lower()
    if 'dual' in fname_lower: found_langs.append('Dual Audio')
    if 'multi' in fname_lower: found_langs.append('Multi Audio')
    if 'hin' in fname_lower and 'Hindi' not in found_langs: found_langs.append('Hindi')
    if 'tam' in fname_lower and 'Tamil' not in found_langs: found_langs.append('Tamil')
    if 'tel' in fname_lower and 'Telugu' not in found_langs: found_langs.append('Telugu')
    if 'kor' in fname_lower and 'Korean' not in found_langs: found_langs.append('Korean')
    
    if not found_langs: return "Unknown"
    return " & ".join(list(dict.fromkeys(found_langs)))

def map_resolution(width, height):
    if not width or not height: return None
    if width >= 3800 or height >= 2100: return "4K (2160p)"
    elif width >= 2500 or height >= 1400: return "2K (1440p)"
    elif width >= 1900 or height >= 1000: return "FHD (1080p)"
    elif width >= 1200 or height >= 700: return "HD (720p)"
    elif width >= 800 or height >= 480: return "SD (480p)"
    return f"{width}x{height}p"

async def get_real_resolution(file_id, context):
    try:
        tg_file = await context.bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{tg_file.file_path}"
        chunk = requests.get(file_url, headers={"Range": "bytes=0-1048576"}, timeout=10).content
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp:
            tmp.write(chunk)
            tmp_path = tmp.name
        parser = createParser(tmp_path)
        res_display = None
        if parser:
            with parser:
                meta = extractMetadata(parser)
                if meta:
                    w, h = meta.get('width'), meta.get('height')
                    res_display = map_resolution(w, h)
        os.unlink(tmp_path)
        return res_display
    except: return None

# ================= THE 4-API OMNISCIENT ENGINE =================
def fetch_smart_metadata(title, year, original_filename, re_verify=False):
    tm_key = random.choice(TMDB_KEYS)
    om_key = random.choice(OMDB_KEYS)
    
    query = title.strip()
    if re_verify: query = query.split(' ')[0]

    data = {"title": title, "rating": "N/A", "genres": "Misc", "date": "N/A", "type": "movie"}
    is_anime_hint = 'anime' in original_filename.lower() or 'judas' in original_filename.lower()

    try:
        url = f"https://api.themoviedb.org/3/search/multi?api_key={tm_key}&query={requests.utils.quote(query)}"
        res = requests.get(url, timeout=5).json()
        if res.get('results'):
            best_item = res['results'][0] 
            
            if year:
                for item in res['results']:
                    item_date = item.get('release_date') or item.get('first_air_date') or ""
                    if str(year) in item_date:
                        best_item = item
                        break

            m_type = best_item.get('media_type', 'movie')
            data['type'] = 'series' if m_type == 'tv' else 'movie'
            
            genre_list = [TMDB_GENRES.get(g_id) for g_id in best_item.get('genre_ids', []) if g_id in TMDB_GENRES]
            if genre_list: data['genres'] = ", ".join(genre_list[:3])
            
            country = best_item.get('origin_country', [''])[0] if best_item.get('origin_country') else ''
            language = best_item.get('original_language', '')
            is_animation = 16 in best_item.get('genre_ids', [])
            
            if is_animation and (country == 'JP' or language == 'ja'):
                data['type'] = 'anime'
            elif data['type'] == 'series':
                if country == 'KR' or language == 'ko': data['type'] = 'kdrama'
                elif country == 'CN' or language == 'zh': data['type'] = 'cdrama'
                elif country == 'JP' or language == 'ja': data['type'] = 'jdrama'
            elif data['type'] == 'movie':
                if country == 'IN' or language in ['hi', 'ta', 'te', 'ml']: data['type'] = 'indian'
                elif country == 'KR' or language == 'ko': data['type'] = 'kmovie'
                elif country == 'JP' or language == 'ja': data['type'] = 'jmovie'
                
            data['title'] = best_item.get('title') or best_item.get('name') or title
            data['rating'] = f"{round(best_item.get('vote_average', 0), 1)} ⭐" if best_item.get('vote_average') else "N/A"
            data['date'] = (best_item.get('release_date') or best_item.get('first_air_date') or "N/A")[:4]
    except: pass

    if data['rating'] == 'N/A' and data['type'] in ['series', 'kdrama', 'cdrama', 'jdrama']:
        try:
            url = f"https://api.tvmaze.com/singlesearch/shows?q={requests.utils.quote(query)}"
            res = requests.get(url, timeout=5).json()
            if res:
                data['title'] = res.get('name', data['title'])
                if res.get('rating', {}).get('average'): data['rating'] = f"{res['rating']['average']} ⭐"
                data['date'] = res.get('premiered', data['date'])[:4] if res.get('premiered') else data['date']
                if res.get('genres'): data['genres'] = ", ".join(res['genres'][:3])
                
                tvm_country = res.get('network', {}).get('country', {}).get('code', '')
                if not tvm_country and res.get('webChannel'):
                    tvm_country = res['webChannel'].get('country', {}).get('code', '')
                    
                if tvm_country == 'KR': data['type'] = 'kdrama'
                elif tvm_country == 'CN': data['type'] = 'cdrama'
                elif tvm_country == 'JP': data['type'] = 'jdrama'
        except: pass

    if data['type'] == 'anime' or is_anime_hint:
        try:
            url = f"https://api.jikan.moe/v4/anime?q={requests.utils.quote(query)}&limit=1"
            res = requests.get(url, timeout=5).json()
            if res.get('data'):
                anime = res['data'][0]
                data['title'] = anime.get('title_english') or anime.get('title') or data['title']
                data['rating'] = f"{anime.get('score', 'N/A')} ⭐"
                data['date'] = str(anime.get('year') or data['date'])
                genres = [g['name'] for g in anime.get('genres', [])]
                if genres: data['genres'] = ", ".join(genres[:3])
                data['type'] = 'anime'
                return data
        except: pass

    if data['genres'] == "Misc":
        try:
            url = f"http://www.omdbapi.com/?apikey={om_key}&t={requests.utils.quote(query)}"
            if year: url += f"&y={year}"
            res = requests.get(url, timeout=5).json()
            if res.get("Response") == "True":
                data['title'] = res.get('Title', data['title'])
                data['rating'] = f"{res.get('imdbRating', 'N/A')} ⭐"
                data['genres'] = res.get('Genre', 'Misc')
                data['date'] = res.get('Year', data['date'])[:4]
                
                omdb_country = res.get('Country', '')
                if res.get('Type') == 'series':
                    if 'South Korea' in omdb_country: data['type'] = 'kdrama'
                    elif 'China' in omdb_country: data['type'] = 'cdrama'
                    elif 'Japan' in omdb_country: data['type'] = 'jdrama'
                    else: data['type'] = 'series'
                else:
                    if 'India' in omdb_country: data['type'] = 'indian'
                    elif 'South Korea' in omdb_country: data['type'] = 'kmovie'
                    elif 'Japan' in omdb_country: data['type'] = 'jmovie'
        except: pass

    return data

# ================= UI BUILDERS =================
def get_main_menu_markup():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 JOIN OFFICIAL CHANNEL", url="https://t.me/THEUPDATEDGUYS", api_kwargs={"style": "primary"})],
        [
            InlineKeyboardButton("📚 How to Use", callback_data="help_menu", api_kwargs={"style": "primary"}),
            InlineKeyboardButton("🤝 Affiliated Dev", web_app={"url": "https://github.com/abhinai2244"}, api_kwargs={"style": "success"})
        ],
        [InlineKeyboardButton("👨‍💻 Developer", web_app={"url": "https://github.com/LastPerson07"}, api_kwargs={"style": "danger"})]
    ])

def get_help_menu_markup():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back to Menu", callback_data="main_menu", api_kwargs={"style": "danger"})]
    ])

def get_media_markup(title):
    imdb_url = f"https://www.imdb.com/find/?q={requests.utils.quote(title.replace(' ', '+'))}"
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎬 IMDB INFO", url=imdb_url, api_kwargs={"style": "primary"}),
            InlineKeyboardButton("🔄 RE-VERIFY", callback_data="reverify", api_kwargs={"style": "danger"})
        ],
        [InlineKeyboardButton("📢 JOIN CHANNEL", url="https://t.me/THEUPDATEDGUYS", api_kwargs={"style": "success"})]
    ])

# ================= TEXT TEMPLATES =================
START_TEXT = """<b><u><blockquote>The Updated Renamer 😎</blockquote></u></b>

<b>Welcome, {name}! ⚡️</b>
I am the most advanced Media AI on Telegram. 

<b>Core Capabilities:</b>
├ 🎬 <b>Precision Extraction:</b> Pulls high-fidelity IMDb & TMDB data.
├ ✨ <b>Smart Recognition:</b> Auto-detects Anime, K-Dramas, & Global Cinema.
├ 🔊 <b>Deep Scanning:</b> Pinpoints exact audio languages & true pixel resolution.
╰ 💎 <b>Artwork Preservation:</b> Retains pristine HD posters and media thumbnails.

<i>Drop any raw video file or document below to initiate the engine.</i>"""

HELP_TEXT = """<b><u><blockquote>The Updated Renamer 😎</blockquote></u></b>

<b>🛠️ HOW TO USE THE ENGINE</b>

1️⃣ <b>Send or Forward</b> any raw movie, series, or anime file to me.
2️⃣ I will aggressively strip out garbage tags (like @RipperNames) from the file.
3️⃣ The Omni-Search engine scans 4 different global databases for a match.
4️⃣ I generate a beautiful, categorized layout and send the file back to you with its original HD thumbnail perfectly intact!

<i>💡 <b>Pro Tip:</b> If the AI catches the wrong movie, just tap the "🔄 RE-VERIFY" button to force a Deep Match!</i>"""

# ================= MAIN HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    try: await update.message.set_reaction(reaction=ReactionTypeEmoji(random.choice(EMOJIS)), is_big=True)
    except: pass
    
    first_name = esc(update.effective_user.first_name)
    
    await update.message.reply_photo(
        photo=random.choice(IMAGE_LINKS),
        caption=START_TEXT.format(name=first_name),
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu_markup()
    )

async def alive_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    try: await update.message.set_reaction(reaction=ReactionTypeEmoji("😘"), is_big=True)
    except: pass
    
    try: await update.message.reply_sticker(sticker=random.choice(LOADING_STICKERS))
    except: pass
    
    await update.message.reply_text("<b>Yes darling, I am alive. Don't worry! 😘</b>", parse_mode=ParseMode.HTML)

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE, re_title=None):
    query = update.callback_query
    msg = query.message if query else update.message
    if not msg: return

    if update.message:
        try: await update.message.set_reaction(reaction=ReactionTypeEmoji(random.choice(EMOJIS)), is_big=True)
        except: pass

    media = msg.document or msg.video
    if not media: return

    loading_sticker = None
    if not query:
        try: loading_sticker = await msg.reply_sticker(sticker=random.choice(LOADING_STICKERS))
        except: pass

    original_name = getattr(media, 'file_name', 'Unknown_File.mp4')
    clean_original = pre_clean_filename(original_name)
    parsed = guessit(clean_original)
    
    search_q = re_title or parsed.get('title', 'Unknown')
    search_year = parsed.get('year') 
    
    info = fetch_smart_metadata(search_q, search_year, original_name, re_verify=bool(re_title))
    
    size = format_size(getattr(media, 'file_size', 0))
    audio = detect_languages(original_name, parsed.get('language'))
    
    real_res = await get_real_resolution(media.file_id, context)
    if not real_res:
        g_res = parsed.get('screen_size')
        real_res = f"FHD (1080p)" if str(g_res) == '1080p' else (f"HD (720p)" if str(g_res) == '720p' else str(g_res or 'FHD (1080p)'))

    header_map = {
        'kdrama': ("🎭 <b>𝗞-𝗗𝗥𝗔𝗠𝗔 𝗘𝗗𝗜𝗧𝗜𝗢𝗡</b> 🎭", "🍿", "🇰🇷"),
        'cdrama': ("🏮 <b>𝗖-𝗗𝗥𝗔𝗠𝗔 𝗘𝗗𝗜𝗧𝗜𝗢𝗡</b> 🏮", "🍿", "🇨🇳"),
        'jdrama': ("🎌 <b>𝗝-𝗗𝗥𝗔𝗠𝗔 𝗘𝗗𝗜𝗧𝗜𝗢𝗡</b> 🎌", "🍿", "🇯🇵"),
        'indian': ("🪷 <b>𝗜𝗡𝗗𝗜𝗔𝗡 𝗖𝗜𝗡𝗘𝗠𝗔</b> 🪷", "🎥", "🇮🇳"),
        'kmovie': ("🎬 <b>𝗞𝗢𝗥𝗘𝗔𝗡 𝗠𝗢𝗩𝗜𝗘</b> 🎬", "🎥", "🇰🇷"),
        'jmovie': ("👹 <b>𝗝𝗔𝗣𝗔𝗡𝗘𝗦𝗘 𝗠𝗢𝗩𝗜𝗘</b> 👹", "🎥", "🇯🇵"),
        'anime': ("✨ <b>𝗔𝗡𝗜𝗠𝗘 𝗘𝗗𝗜𝗧𝗜𝗢𝗡</b> ✨", "⛩️", "🎌"),
        'series': ("📺 <b>𝗦𝗘𝗥𝗜𝗘𝗦 𝗘𝗗𝗜𝗧𝗜𝗢𝗡</b> 📺", "🍿", "⭐"),
        'movie': ("🎬 <b>𝗠𝗢𝗩𝗜𝗘 𝗘𝗗𝗜𝗧𝗜𝗢𝗡</b> 🎬", "🎥", "⭐")
    }
    
    h_data = header_map.get(info['type'], header_map['movie'])
    header, icon1, icon2 = h_data[0], h_data[1], h_data[2]

    caption = f"""
{header}
<blockquote><b>{esc(info['title'])}</b></blockquote>

{icon1} <b>Details:</b>
├ {icon2} <b>Rating</b>  : {esc(info['rating'])}
├ 🎭 <b>Genres</b>  : <i>{esc(info['genres'])}</i>
├ 📅 <b>Release</b> : <code>{esc(info['date'])}</code>
├ 🔊 <b>Audio</b>   : <code>{esc(audio)}</code>
├ 🖥️ <b>Quality</b> : <code>{esc(real_res)}</code>
╰ 💾 <b>Size</b>    : <code>{esc(size)}</code>

‣ <blockquote><b>@DmOwner</b></blockquote>
"""

    markup = get_media_markup(info['title'])

    if loading_sticker:
        try: await loading_sticker.delete()
        except: pass

    if query:
        # 🔥 SAFELY CATCHES THE BAD_REQUEST IF DATA IS IDENTICAL
        try:
            await query.edit_message_caption(caption=caption, parse_mode=ParseMode.HTML, reply_markup=markup)
        except BadRequest as e:
            if "not modified" in str(e).lower():
                pass 
            else:
                logging.error(f"Error editing caption: {e}")
    else:
        await context.bot.copy_message(
            chat_id=msg.chat.id,
            from_chat_id=msg.chat.id,
            message_id=msg.message_id,
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=markup
        )

async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() 
    
    data = query.data
    
    # 🔥 DYNAMIC UI ROTATION WITH TRY/EXCEPT 🔥
    if data == "help_menu":
        try:
            await query.edit_message_media(
                media=InputMediaPhoto(media=random.choice(IMAGE_LINKS), caption=HELP_TEXT, parse_mode=ParseMode.HTML),
                reply_markup=get_help_menu_markup()
            )
        except BadRequest: pass

    elif data == "main_menu":
        first_name = esc(update.effective_user.first_name)
        try:
            await query.edit_message_media(
                media=InputMediaPhoto(media=random.choice(IMAGE_LINKS), caption=START_TEXT.format(name=first_name), parse_mode=ParseMode.HTML),
                reply_markup=get_main_menu_markup()
            )
        except BadRequest: pass
    
    elif data == "reverify":
        await query.answer("🔄 Engaging Deep Match Protocol...", show_alert=True)
        await handle_media(update, context, re_title="DeepSearch")

if __name__ == '__main__':
    print("🚀 TITANIUM 22.0 (THE MASTERPIECE) IS ONLINE.")
    
    # Start Keep-Alive Server
    keep_alive()
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("alive", alive_cmd))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.ALL, handle_media))
    app.add_handler(CallbackQueryHandler(callback_router))
    
    app.run_polling()
