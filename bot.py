import os
import random
import asyncio
import io
from collections import defaultdict
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command, CommandObject
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest
from PIL import Image, ImageDraw, ImageFont
import httpx

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

if not BOT_TOKEN:
    raise ValueError("❌ В Environment Variables не найден BOT_TOKEN!")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

chat_settings = defaultdict(lambda: {"active": True})
chat_history = defaultdict(list)

NAMES = ["@vitalya_bobosh67bot", "виталя", "виталик", "виталий", "виталямбус", "виталечка", "виталясик", "виталюша"]

def is_mentioned(text: str, msg: Message) -> bool:
    text_lower = text.lower()
    if any(name in text_lower for name in NAMES):
        return True
    if msg.reply_to_message and msg.reply_to_message.from_user.id == bot.id:
        return True
    return False

# ==========================================
# СИСТЕМА РОЛЛОВ
# ==========================================
CHARACTERS = {
    "эмбер": {"names": ["эмбер", "amber"], "reactions": ["Эмбер: АААА! Виталя, ты чё делаешь?!", "Эмбер: Ой! Больно же!", "Эмбер: *краснеет* Не надо!"]},
    "лиза": {"names": ["лиза", "liza"], "reactions": ["Лиза: *зевает* Виталя, не сейчас.", "Лиза: *закрывает книгу* Ты серьёзно?", "Лиза: *улыбается* Ну ты и дурак."]},
    "ронова": {"names": ["ронова", "ronova"], "reactions": ["Ронова: *смотрит с презрением* Ты кто вообще?", "Ронова: *бьёт Виталю* Знай своё место."]},
    "варка": {"names": ["варка", "varka"], "reactions": ["Варка: *смотрит с недоумением* Что ты делаешь?", "Варка: *вздыхает* Виталя, уйди."]},
    "гренни": {"names": ["гренни", "бабка", "granny"], "reactions": ["Бабка Гренни: *бьёт Виталю сковородкой* Ах ты ж! Охламон!", "Бабка Гренни: *даёт леща* Наглец!"]}
}

def get_roll_reply(text: str) -> str | None:
    lower = text.lower()
    found = [data for data in CHARACTERS.values() if any(n in lower for n in data["names"])]
    if not found: return None
    reply = " ".join(random.choice(c["reactions"]) for c in found)
    if random.random() < 0.5: reply += " " + random.choice(["ХАХА", "ик", "бля"])
    return reply

# ==========================================
# ПЬЯНЫЙ ФИЛЬТР И ГЕНЕРАТОР
# ==========================================
def drunkify_text(text):
    if not text: return text
    prefixes = ["", "", "ик ", "АААА ", "бля ", "ну "]
    suffixes = ["", "", " ик", " ааа", " бля", " ...", ".."]
    if random.random() < 0.7: text = random.choice(prefixes) + text
    if random.random() < 0.6: text = text.rstrip(".!?") + random.choice(suffixes)
    return text

START_GEN = ["я вчера", "я сегодня", "я однажды", "я тут подумал", "мне сказали", "я слышал", "я видел", "мне приснилось", "я не помню как", "я случайно", "бля, я", "ик, я"]
MIDDLE_GEN = ["взял", "отшлепал", "обнял", "потерял", "съел", "сжёг", "уронил", "выпил", "украл", "покрасил", "запустил", "купил", "продал", "забыл", "сломал", "привязал", "поцеловал", "ударил", "нарядил", "нарисовал"]
OBJECT_GEN = ["летающую корову", "носки", "свой пропеллер", "шапку", "холодильник", "стену", "кота", "соседа", "луну", "динозавра", "бабушку", "Freshtunes", "свою тень", "табуретку", "будильник", "воздух", "ложку", "лужу"]
END_GEN = ["и это было странно", "и мне понравилось", "но потом передумал", "и теперь я в шоке", "а он не понял", "и всё исчезло", "но мне было похуй", "и я засмеялся", "и это было больно", "и я забыл", "ХАХА"]

def generate_absurd():
    return f"{random.choice(START_GEN)} {random.choice(MIDDLE_GEN)} {random.choice(OBJECT_GEN)} {random.choice(END_GEN)}"

# ==========================================
# ИИ (ЧЕРЕЗ HTTPX)
# ==========================================
async def get_ai_reply(chat_id: int, text: str) -> str:
    if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == "sk-":
        return drunkify_text(generate_absurd())
        
    messages = [
        {"role": "system", "content": "Ты Виталя Бобош, пьяный ебанат в шапке с пропеллером. Отвечай коротко (1-2 предложения), с матом."},
    ]
    messages.extend(chat_history[chat_id][-4:])
    messages.append({"role": "user", "content": text})
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://api.deepseek.com/chat/completions",
                headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
                json={"model": "deepseek-chat", "messages": messages, "max_tokens": 60, "temperature": 1.5}
            )
            data = response.json()
            reply = data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"⚠️ Ошибка ИИ: {e}")
        reply = generate_absurd()
        
    reply = drunkify_text(reply)
    chat_history[chat_id].append({"role": "user", "content": text})
    chat_history[chat_id].append({"role": "assistant", "content": reply})
    return reply

# ==========================================
# БЕЗОПАСНЫЕ МЕМЫ, ДЕМОТИВАТОРЫ И ГИФКИ
# ==========================================
def _get_font(size, bold=False):
    fonts = ("arialbd.ttf", "DejaVuSans-Bold.ttf") if bold else ("arial.ttf", "DejaVuSans.ttf")
    for path in fonts:
        try: return ImageFont.truetype(path, size)
        except: pass
    return ImageFont.load_default()

def draw_meme_text(img, top_text, bottom_text):
    img = img.convert("RGB")
    if img.width > 800: img = img.resize((800, int(img.height * (800 / img.width))))
    draw = ImageDraw.Draw(img)
    font = _get_font(40)
    def draw_text(text, x, y, anchor="mt"):
        for dx in (-3, 0, 3):
            for dy in (-3, 0, 3): draw.text((x+dx, y+dy), text, font=font, fill="black", anchor=anchor)
        draw.text((x, y), text, font=font, fill="white", anchor=anchor)
    draw_text(top_text.upper()[:70], img.width // 2, 12, "mt")
    draw_text(bottom_text.upper()[:70], img.width // 2, img.height - 12, "mb")
    return img

def make_meme(image_bytes):
    try:
        img = Image.open(io.BytesIO(image_bytes))
        top, bottom = generate_absurd(), generate_absurd()
        img = draw_meme_text(img, top, bottom)
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=85)
        out.seek(0)
        return out.read()
    except Exception as e:
        print(f"Ошибка мема: {e}")
        return None

def make_demotivator(image_bytes):
    try:
        user_img = Image.open(io.BytesIO(image_bytes))
        top, bottom = generate_absurd(), generate_absurd()
        border, panel = 40, 120
        if user_img.width > 800: user_img = user_img.resize((800, int(user_img.height * (800 / user_img.width))))
        total_w, total_h = user_img.width + (border * 2), user_img.height + border + panel
        demo = Image.new("RGB", (total_w, total_h), (0, 0, 0))
        demo.paste(user_img.convert("RGB"), (border, border))
        draw = ImageDraw.Draw(demo)
        draw.rectangle([border-2, border-2, border+user_img.width+1, border+user_img.height+1], outline="white", width=2)
        font_big, font_small = _get_font(45, bold=True), _get_font(30)
        top_bbox = draw.textbbox((0, 0), top, font=font_big)
        draw.text(((total_w - (top_bbox[2] - top_bbox[0])) / 2, total_h - panel + 10), top, font=font_big, fill="white")
        bot_bbox = draw.textbbox((0, 0), bottom, font=font_small)
        draw.text(((total_w - (bot_bbox[2] - bot_bbox[0])) / 2, total_h - panel + 70), bottom, font=font_small, fill="gray")
        out = io.BytesIO()
        demo.save(out, format="JPEG", quality=90)
        out.seek(0)
        return out.read()
    except Exception as e:
        print(f"Ошибка демотиватора: {e}")
        return None

def make_gif_from_photo(image_bytes):
    try:
        base_img = Image.open(io.BytesIO(image_bytes))
        top, bottom = generate_absurd(), generate_absurd()
        base_img = draw_meme_text(base_img, top, bottom)
        frames = []
        for i in range(10):
            offset_x = random.randint(-15, 15)
            offset_y = random.randint(-15, 15)
            new_img = Image.new("RGB", base_img.size, (0, 0, 0))
            new_img.paste(base_img, (offset_x, offset_y))
            frames.append(new_img)
        out = io.BytesIO()
        frames[0].save(out, format="GIF", save_all=True, append_images=frames[1:], duration=100, loop=0)
        out.seek(0)
        return out.read()
    except Exception as e:
        print(f"Ошибка GIF: {e}")
        return None

async def _download_file(file_id):
    try:
        file = await bot.get_file(file_id)
        downloaded = await bot.download_file(file.file_path)
        return downloaded.read()
    except:
        return None

# ==========================================
# КОМАНДЫ
# ==========================================
@dp.message(Command("start"))
async def start_cmd(msg: Message):
    await msg.answer(f"🧢🛸💥 <b>ААААА ПРИВЕТ!!!</b>\nЯ ебанат.\n/meme — мем\n/dem — демотиватор\n/gif — гифка из фото\n/roll [действие] [кто] — ролл")

@dp.message(Command("roll"))
async def roll_cmd(msg: Message, command: CommandObject):
    if not command.args:
        return await msg.answer("Напиши действие! Например: /roll отшлепал эмбер.")
    reply = get_roll_reply(command.args)
    if reply: await msg.reply(drunkify_text(reply))
    else: await msg.answer("Виталя не понял, кого ты хочешь.")

@dp.message(Command("meme"))
async def meme_cmd(msg: Message):
    image_bytes = None
    if msg.reply_to_message and msg.reply_to_message.photo:
        image_bytes = await _download_file(msg.reply_to_message.photo[-1].file_id)
    elif msg.photo:
        image_bytes = await _download_file(msg.photo[-1].file_id)
    if not image_bytes:
        return await msg.answer("Виталя не видит фото. ик.")
    meme = make_meme(image_bytes)
    if meme: await msg.reply_photo(BufferedInputFile(meme, filename="meme.jpg"), caption="Мем. ХАХА")
    else: await msg.answer("Виталя сломал мем.")

@dp.message(Command("dem"))
async def dem_cmd(msg: Message):
    image_bytes = None
    if msg.reply_to_message and msg.reply_to_message.photo:
        image_bytes = await _download_file(msg.reply_to_message.photo[-1].file_id)
    elif msg.photo:
        image_bytes = await _download_file(msg.photo[-1].file_id)
    if not image_bytes:
        return await msg.answer("Виталя не видит фото. ик.")
    dem = make_demotivator(image_bytes)
    if dem: await msg.reply_photo(BufferedInputFile(dem, filename="dem.jpg"), caption="Демотиватор. ХАХА")
    else: await msg.answer("Виталя сломал демотиватор.")

@dp.message(Command("gif"))
async def gif_cmd(msg: Message):
    image_bytes = None
    if msg.reply_to_message and msg.reply_to_message.photo:
        image_bytes = await _download_file(msg.reply_to_message.photo[-1].file_id)
    elif msg.photo:
        image_bytes = await _download_file(msg.photo[-1].file_id)
    if not image_bytes:
        return await msg.answer("Виталя не видит фото для гифки. ик.")
    await msg.answer("Виталя трясет гифку... АААА...")
    gif_bytes = make_gif_from_photo(image_bytes)
    if gif_bytes:
        await msg.reply_animation(BufferedInputFile(gif_bytes, filename="vitalya.gif"), caption="Гифка. ХАХА")
    else:
        await msg.answer("Виталя сломал гифку.")

# ==========================================
# ГЛАВНЫЙ ОБРАБОТЧИК
# ==========================================
@dp.message(F.photo)
async def catch_photo(msg: Message):
    pass

@dp.message(F.text)
async def handler(msg: Message):
    if msg.from_user.is_bot: return
    if not chat_settings[msg.chat.id]["active"]: return
    text = msg.text.strip()
    if not text or text.startswith("/"): return
    
    roll_reply = get_roll_reply(text)
    if roll_reply:
        return await msg.reply(drunkify_text(roll_reply))

    if not is_mentioned(text, msg):
        return

    await bot.send_chat_action(msg.chat.id, "typing")
    await asyncio.sleep(random.uniform(0.5, 2.0))
    
    try:
        reply = await get_ai_reply(msg.chat.id, text)
        await msg.reply(reply)
    except TelegramBadRequest:
        pass
    except Exception as e:
        print(f"Ошибка отправки: {e}")

async def main():
    print("🤖 Виталя запускается (Background Worker)...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
        
