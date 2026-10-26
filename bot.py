from aiogram.client.default import DefaultBotProperties
import os
import random
import asyncio
import io
import tempfile
from collections import defaultdict
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command
from aiogram.enums import ParseMode
from PIL import Image, ImageDraw, ImageFont
import aiohttp

MOVIEPY_OK = True
try:
    from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip
except Exception as e:
    MOVIEPY_OK = False
    print(f"⚠️ moviepy не загрузился: {e} — /video будет недоступен")

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

NAME = "Виталя Бобош"
EMOJI_HAT = "🧢🛸💥"

counter = defaultdict(int)
media_history = defaultdict(list)

# ==========================================
# 1. СИСТЕМА РОЛЛОВ (ЭМБЕР И ЛИЗА)
# ==========================================
ACTION_VERBS = ["отшлепал", "обнял", "поцеловал", "ударил", "дал", "связал", "укусил", "уронил", "облил", "кинул", "пнул", "погладил", "ущипнул", "нарядил", "станцевал", "спел", "подарил", "нарисовал", "трогал", "лизал", "кусал", "бил", "шлепнул", "пощекотал", "поймал", "схватил"]
EMBER_REACTIONS = ["Эмбер: АААА! Виталя, ты чё делаешь?!", "Эмбер: Ой! Больно же!", "Эмбер: Виталя, бля, прекрати!", "Эмбер: *краснеет* Не надо!", "Эмбер: *смеётся* Ты чего?!", "Эмбер: *уворачивается* Не трогай меня!", "Эмбер: *обиделась* Всё, я с тобой не разговариваю.", "Эмбер: *визжит* ААААА!", "Эмбер: *толкает Виталю* Отстань!", "Эмбер: *смеётся* Ты пьяный?"]
LIZA_REACTIONS = ["Лиза: *зевает* Виталя, не сейчас.", "Лиза: *закрывает книгу* Ты серьёзно?", "Лиза: *улыбается* Ну ты и дурак.", "Лиза: *отмахивается* Иди проспись.", "Лиза: *смотрит с укором* Виталя...", "Лиза: *смеётся* Ты как всегда.", "Лиза: *гладит по голове* Ладно, ладно.", "Лиза: *вздыхает* Ну что с тобой делать.", "Лиза: *отворачивается* Не мешай читать.", "Лиза: *тихо смеётся* Дурачок."]

def roll_action(text: str) -> str | None:
    lower = text.lower()
    has_ember = "эмбер" in lower
    has_liza = "лиза" in lower
    if not has_ember and not has_liza: return None
    
    verb_found = any(verb in lower for verb in ACTION_VERBS)
    if verb_found:
        if has_ember and has_liza: reaction = "Эмбер и Лиза: *смотрят на Виталю с недоумением* Ты чего?"
        elif has_ember: reaction = random.choice(EMBER_REACTIONS)
        else: reaction = random.choice(LIZA_REACTIONS)
        if random.random() < 0.4: reaction += " " + random.choice(["ХАХА", "ик", "бля", "шапка крутится", "сисяндры моисяндры"])
        return reaction
    
    if random.random() < 0.4:
        if has_ember: return f"Виталя смотрит на эмбер. {random.choice(['ХАХА', 'ик', 'она красивая'])}"
        if has_liza: return f"Виталя смотрит на лизу. {random.choice(['ХАХА', 'ик', 'она читает'])}"
    return None

# ==========================================
# 2. ПЬЯНЫЕ ТРАНСФОРМАЦИИ
# ==========================================
DRUNK_PREFIX = ["", "", "", "ик ", "ик-ик ", "ааа ", "бля ", "ну ", "вот ", "ооо ", "слушай ", "эээ ", "короче ", "значит ", "так ", "ага ", "ой ", "чё ", "мда ", "хм ", "пфф ", "тьфу ", "ой бля "]
DRUNK_SUFFIX = ["", "", "", " ик", " ик-ик", " ааа", " бля", " ну", " вот", " ооо", " ...", "..", ".", " ну ты понял", " как-то так", " вот так вот", " я так думаю", " наверное", " хз", " хз бля", " короче", " всё", " я устал", " налей ещё", " аааа", " бля", " чё-то я"]
DRUNK_INTERJECTIONS = ["ик", "ик-ик", "ик-ик-ик", "ааа", "бля", "ну", "вот", "ооо", "слушай", "эээ", "короче", "значит", "так", "ага", "ой", "хм", "пфф", "тьфу", "мда", "ой бля", "господи", "боже", "ёпта"]

def drunkify_text(text):
    if not text: return text
    if random.random() < 0.6:
        prefix = random.choice(DRUNK_PREFIX)
        if prefix:
            text = prefix + text
            if random.random() < 0.5: text = prefix.rstrip() + ", " + text[len(prefix):]
    if random.random() < 0.5: text = text.rstrip(".!?") + random.choice(DRUNK_SUFFIX)
    words = text.split(" ")
    out = []
    for w in words:
        if len(w) > 3 and random.random() < 0.3:
            idx = random.randint(1, len(w) - 1)
            w = w[:idx] + w[idx-1] * random.randint(2, 4) + w[idx:]
        if len(w) > 3 and random.random() < 0.2:
            op = random.choice(["swap", "drop", "dupe", "shift"])
            idx = random.randint(1, len(w) - 2)
            if op == "swap": w = w[:idx] + w[idx+1] + w[idx] + w[idx+2:]
            elif op == "drop": w = w[:idx] + w[idx+1:]
            elif op == "dupe": w = w[:idx] + w[idx] * 2 + w[idx:]
            elif op == "shift": w = w[:idx] + random.choice("йцукенгшщзхъфывапролджэячсмитьбю") + w[idx+1:]
        out.append(w)
    text = " ".join(out)
    if random.random() < 0.25:
        words = text.split(" ")
        if len(words) > 3:
            idx = random.randint(1, len(words) - 1)
            words.insert(idx, random.choice(DRUNK_INTERJECTIONS))
            text = " ".join(words)
    return text

# ==========================================
# 3. ГЕНЕРАТОР АБСУРДА (С МАТОМ И БДСМ)
# ==========================================
START_GEN = ["я вчера", "я сегодня", "я однажды", "я тут подумал", "мне сказали", "я слышал", "я видел", "мне приснилось", "я не помню как", "я случайно", "бля, я", "ик, я", "короче, я", "слушай, я", "а вот я", "я нахуй", "я бля", "я ебать"]
MIDDLE_GEN = ["взял", "отшлепал", "обнял", "потерял", "съел", "сжёг", "уронил", "выпил", "украл", "покрасил", "запустил", "купил", "продал", "забыл", "сломал", "привязал", "поцеловал", "ударил", "нарядил", "нарисовал", "выебал", "отпиздил", "выебал в жопу", "отхлестал плетью", "связал скотчем", "засунул в рот кляп"]
OBJECT_GEN = ["летающую корову", "носки", "свой пропеллер", "шапку", "холодильник", "стену", "кота", "соседа", "луну", "динозавра", "бабушку", "Freshtunes", "свою тень", "табуретку", "будильник", "воздух", "ложку", "лужу", "облако", "свои мысли", "хуй", "жопу", "пизду", "шлюху", "свою руку", "ремень", "наручники", "член"]
END_GEN = ["и это было странно", "и мне понравилось", "но потом передумал", "и теперь я в шоке", "а он не понял", "и всё исчезло", "но мне было похуй", "и я засмеялся", "и это было больно", "и я забыл", "а оно убежало", "и теперь я пьяный", "ХАХА", "и я не жалею", "и мне стыдно", "но я всё равно сделал", "и мне хуёво", "и я в ахуе", "и это пиздец"]

def generate_absurd():
    return f"{random.choice(START_GEN)} {random.choice(MIDDLE_GEN)} {random.choice(OBJECT_GEN)} {random.choice(END_GEN)}"

# ==========================================
# 4. СПЕЦИАЛЬНЫЕ ФРАЗЫ (ОСОБЫЕ СЛУЧАИ)
# ==========================================
SPECIAL_PHRASES = [
    "АААААА", "АААА БЛЯ", "ЫЫЫЫЫ", "ЕБАТЬ КОЛОТИТЬ", "ПИЗДЕЦ", "АААА ШАПКА", "ПРОПЕЛЛЕР ГУДИТ", "БЛЯЯЯ", "ЧТО", "а?", "ХАХАХАХАХА", "ХЕХЕХЕ", "УУУУУ", "ОООО", "БЛЯ БЛЯ БЛЯ", "ЕБАТЬ", "СУКА", "НАХУЙ", "ЗАЕБАЛ", "ОХУЕТЬ", "ПОМОГИТЕ", "СПАСИТЕ", "КАРАУЛ",
    "сисяндры моисяндры", "У тебя спина красивая", "шапка крутится шапка крутится", "ПРОПЕЛЛЕР. ПРОПЕЛЛЕР", "пропеллер в голову стукнул. ХАХА", "у меня шапка с пропеллером. а у тебя нет. лох", "я надел шапку. пропеллер закрутился. я полетел. не полетел", "без шапки я никто. с шапкой я Виталя",
    "у меня хомяк умер. я его похоронил. потом выкопал. потом опять похоронил. ХАХА", "я однажды уронил кота с балкона. он не мяукнул. я подумал что он сильный. он не сильный", "у соседа инфаркт был. я подумал что он просто лежит. а он не просто. ХАХА", "смерть это как сон. только без будильника. ХАХА", "я в детстве котёнка в стиралку засунул. он выжил. жалко. ХАХАХА",
    "я вчера верёвку нашёл. теперь я умею вязать. а ты? ХАХА", "мне нравится когда больно. но не сильно. и не мне. ХАХАХА", "у меня есть кожаный ремень. я им не бью. но могу. если попросишь", "а ты знал что кляп это просто носки? я так делаю", "а можно я тебя свяжу? нет? ладно. Виталя просто спросил. ХАХА",
    "я загрузил трек на Freshtunes. он исчез. поддержка сказала ждать. я жду с 2021", "Freshtunes опять лёг. мой трек где-то между Дубаем и моей мамой", "поддержка Freshtunes ответила через 2 месяца. сказала 'ждите'. я жду. до сих пор"
]

# ==========================================
# 5. МЕМЫ И ВИДЕО
# ==========================================
def _get_font(size):
    for path in ("arial.ttf", "DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try: return ImageFont.truetype(path, size)
        except: pass
    return ImageFont.load_default()

def make_meme(image_bytes, top_text, bottom_text):
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    if img.width > 900: img = img.resize((900, int(img.height * (900 / img.width))))
    draw = ImageDraw.Draw(img)
    font = _get_font(40)
    def draw_text(text, x, y, anchor="mt"):
        for dx in (-3, 0, 3):
            for dy in (-3, 0, 3): draw.text((x+dx, y+dy), text, font=font, fill="black", anchor=anchor)
        draw.text((x, y), text, font=font, fill="white", anchor=anchor)
    draw_text(top_text.upper()[:70], img.width // 2, 12, "mt")
    draw_text(bottom_text.upper()[:70], img.width // 2, img.height - 12, "mb")
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=88)
    out.seek(0)
    return out.read()

def _make_overlay_png(width, height, top, bottom, path):
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    font = _get_font(36)
    def draw_outlined(text, xy, anchor):
        for dx in (-3, 0, 3):
            for dy in (-3, 0, 3): d.text((xy[0]+dx, xy[1]+dy), text, font=font, fill=(0, 0, 0, 255), anchor=anchor)
        d.text(xy, text, font=font, fill=(255, 255, 255, 255), anchor=anchor)
    draw_outlined(top.upper()[:40], (width // 2, 15), "mt")
    draw_outlined(bottom.upper()[:40], (width // 2, height - 15), "mb")
    img.save(path)

def make_video_from_video(video_bytes, top_text, bottom_text, max_seconds=8.0):
    if not MOVIEPY_OK: raise RuntimeError("moviepy не установлен")
    tmp_dir = tempfile.mkdtemp(prefix="vitalya_vid_")
    in_path = os.path.join(tmp_dir, "in.mp4")
    out_path = os.path.join(tmp_dir, "out.mp4")
    with open(in_path, "wb") as f: f.write(video_bytes)
    clip = None
    try:
        clip = VideoFileClip(in_path)
        if clip.duration > max_seconds: clip = clip.subclip(0, max_seconds)
        w, h = clip.size
        if w % 2: w -= 1
        if h % 2: h -= 1
        clip = clip.resize((w, h))
        overlay_path = os.path.join(tmp_dir, "overlay.png")
        _make_overlay_png(w, h, top_text, bottom_text, overlay_path)
        overlay = ImageClip(overlay_path).set_duration(clip.duration)
        final = CompositeVideoClip([clip, overlay], size=(w, h))
        final.write_videofile(out_path, codec="libx264", audio=False, preset="ultrafast", threads=2, logger=None, ffmpeg_params=["-pix_fmt", "yuv420p"])
        with open(out_path, "rb") as f: data = f.read()
    finally:
        try:
            if clip: clip.close()
        except: pass
        for p in (in_path, out_path, os.path.join(tmp_dir, "overlay.png")):
            try: os.remove(p)
            except: pass
        try: os.rmdir(tmp_dir)
        except: pass
    return data

def make_video_from_photo(image_bytes, top_text, bottom_text, duration=4.0):
    if not MOVIEPY_OK: raise RuntimeError("moviepy не установлен")
    tmp_dir = tempfile.mkdtemp(prefix="vitalya_p2v_")
    img_path = os.path.join(tmp_dir, "frame.png")
    out_path = os.path.join(tmp_dir, "out.mp4")
    base = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    w = 720
    h = int(base.height * (w / base.width))
    if h % 2: h += 1
    base = base.resize((w, h))
    base.save(img_path)
    clip = None
    try:
        clip = ImageClip(img_path).set_duration(duration)
        clip = clip.resize(lambda t: 1.0 + 0.15 * (t / duration))
        overlay_path = os.path.join(tmp_dir, "overlay.png")
        _make_overlay_png(w, h, top_text, bottom_text, overlay_path)
        overlay = ImageClip(overlay_path).set_duration(duration)
        final = CompositeVideoClip([clip, overlay], size=(w, h)).set_fps(24)
        final.write_videofile(out_path, codec="libx264", audio=False, preset="ultrafast", threads=2, logger=None, ffmpeg_params=["-pix_fmt", "yuv420p"])
        with open(out_path, "rb") as f: data = f.read()
    finally:
        try:
            if clip: clip.close()
        except: pass
        for p in (img_path, out_path, os.path.join(tmp_dir, "overlay.png")):
            try: os.remove(p)
            except: pass
        try: os.rmdir(tmp_dir)
        except: pass
    return data

async def _download_file(file_id):
    file = await bot.get_file(file_id)
    downloaded = await bot.download_file(file.file_path)
    return downloaded.read()

def _meme_texts():
    return random.choice(["сисяндры моисяндры", "У тебя спина красивая", "ААААА", "БЛЯ", "ШАПКА"]), random.choice(["хуйня какая-то", "пропеллер в голову стукнул", "я тупой", "ХАХАХА", "ик"])

# ==========================================
# 6. ХЭНДЛЕРЫ
# ==========================================
@dp.message(Command("start"))
async def start_cmd(msg: Message):
    vstat = "есть" if MOVIEPY_OK else "НЕТ (moviepy не установлен)"
    await msg.answer(
        f"{EMOJI_HAT} <b>ААААА ПРИВЕТ!!! Я ВИТАЛЯ БОБОШ!!!</b>\n\n"
        f"Я пьяный. Отвечаю абсурдной хуйнёй. И делаю роллы с эмбер и лизой.\n"
        f"Напиши: 'отшлепал эмбер' или 'обнял лизу'.\n"
        f"Видео-мемы: <b>{vstat}</b>\n\n"
        f"/meme — мем из фото\n"
        f"/video — видео-мем\n"
        f"/owner — хозяин"
    )

@dp.message(Command("owner"))
async def owner_cmd(msg: Message):
    if msg.from_user.id == OWNER_ID:
        await msg.answer(f"👑 ХОЗЯИН!!! ДОСТУП ПОДТВЕРЖДЁН!!!\nID: <code>{OWNER_ID}</code>\nВиталя слушается. ик.")
    else:
        await msg.answer("❌ ТЫ НЕ ХОЗЯИН ВИТАЛИ. ик.")

@dp.message(Command("meme"))
async def meme_cmd(msg: Message):
    image_bytes = None
    if msg.reply_to_message and msg.reply_to_message.photo:
        try: image_bytes = await _download_file(msg.reply_to_message.photo[-1].file_id)
        except: pass
    elif msg.photo:
        try: image_bytes = await _download_file(msg.photo[-1].file_id)
        except: pass
    if not image_bytes and media_history[msg.chat.id]:
        try: image_bytes = await _download_file(random.choice(media_history[msg.chat.id]))
        except: pass
    
    if not image_bytes:
        await msg.answer("Виталя не видит фото. ответь на фото или приложи. ик.")
        return
    try:
        top, bottom = _meme_texts()
        meme = make_meme(image_bytes, top, bottom)
        await msg.reply_photo(BufferedInputFile(meme, filename="meme.jpg"), caption=drunkify_text("Виталя сделал мем. ХАХА"))
    except Exception as e:
        await msg.answer(f"Виталя сломал мем: {str(e)[:100]}.")

@dp.message(Command("video"))
async def video_cmd(msg: Message):
    if not MOVIEPY_OK:
        await msg.answer("❌ Видео сломано (moviepy не установлен).")
        return
    await msg.answer("Виталя делает ВИДЕО... подожди...")
    
    if msg.reply_to_message and msg.reply_to_message.video:
        try:
            vb = await _download_file(msg.reply_to_message.video.file_id)
            top, bottom = _meme_texts()
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, make_video_from_video, vb, top, bottom, 8.0)
            await msg.reply_video(BufferedInputFile(data, filename="video.mp4"), caption=drunkify_text("Виталя сделал видео. ХАХА"))
            return
        except Exception as e:
            await msg.answer(f"Виталя не смог: {str(e)[:150]}")
    
    image_bytes = None
    if msg.reply_to_message and msg.reply_to_message.photo:
        try: image_bytes = await _download_file(msg.reply_to_message.photo[-1].file_id)
        except: pass
    elif msg.photo:
        try: image_bytes = await _download_file(msg.photo[-1].file_id)
        except: pass
        
    if not image_bytes and media_history[msg.chat.id]:
        try: image_bytes = await _download_file(random.choice(media_history[msg.chat.id]))
        except: pass
    
    if not image_bytes:
        await msg.answer("Виталя не видит ни видео, ни фото. ик.")
        return
    try:
        top, bottom = _meme_texts()
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, make_video_from_photo, image_bytes, top, bottom, 4.0)
        await msg.reply_video(BufferedInputFile(data, filename="video.mp4"), caption=drunkify_text("Виталя сделал видео из фото. ХАХА"))
    except Exception as e:
        await msg.answer(f"Виталя не смог видео: {str(e)[:150]}.")

@dp.message(F.photo)
async def catch_photo(msg: Message):
    try: media_history[msg.chat.id].append(msg.photo[-1].file_id)
    except: pass
    await msg.reply(drunkify_text(random.choice(["ОЙ. ФОТО. Виталя запомнил. мем: /meme", "картинка. красиво. сисяндры моисяндры"])))

@dp.message(F.text)
async def handler(msg: Message):
    if msg.from_user.is_bot: return
    text = msg.text.strip()
    if not text or text.startswith("/"): return
    
    counter[msg.chat.id] += 1
    await asyncio.sleep(random.uniform(0.5, 2.5))

    roll = roll_action(text)
    if roll:
        await msg.reply(drunkify_text(roll))
        return

    if random.random() < 0.6:
        reply = generate_absurd()
    else:
        reply = random.choice(SPECIAL_PHRASES)
        
    await msg.reply(drunkify_text(reply))

async def main():
    print(f"🤖 {NAME} (ГЕНЕРАТОР БРЕДА + РОЛЛЫ) запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
