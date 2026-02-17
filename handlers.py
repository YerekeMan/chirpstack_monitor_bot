import logging, json
from aiogram import F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import api_service
from config import dp

last_messages = {}


# --- Утилиты ---

async def safe_edit(c: types.CallbackQuery, text: str, kb=None, parse_mode="HTML"):
    """Универсальная функция обновления сообщения с защитой от ошибок и логированием"""
    try:
        # Логируем действие пользователя (callback_data)
        logging.info(f"ACTION: User {c.from_user.full_name} (@{c.from_user.username}) -> {c.data}")
        await c.message.edit_text(text, reply_markup=kb, parse_mode=parse_mode)
    except Exception as e:
        if "message is not modified" in str(e):
            await c.answer()
        else:
            logging.error(f"Edit error: {e}")


async def delete_prev_menu(user_id, bot):
    if user_id in last_messages:
        try:
            await bot.delete_message(chat_id=user_id, message_id=last_messages[user_id])
        except:
            pass


# --- Клавиатуры ---

def get_orgs_kb():
    kb = InlineKeyboardBuilder()
    data, _ = api_service.fetch_data("organizations?limit=10")
    for i in data: kb.button(text=f"🔹 {i['name']}", callback_data=f"org_{i['id']}")
    return kb.adjust(1).as_markup()


def get_action_kb(org_id):
    kb = InlineKeyboardBuilder()
    kb.button(text="📡 Базовые станции", callback_data=f"gwp_0_{org_id}")
    kb.button(text="📦 Группы (Apps)", callback_data=f"app_{org_id}")
    kb.button(text="⬅️ К организациям", callback_data="back_to_orgs")
    return kb.adjust(1).as_markup()


# --- Хендлеры сообщений ---

@dp.message(Command("start"))
async def start(m: types.Message):
    logging.info(f"CMD: {m.from_user.full_name} started bot")
    await delete_prev_menu(m.from_user.id, m.bot)
    try:
        await m.delete()
    except:
        pass
    sent = await m.answer(f"Привет, {m.from_user.first_name}!\nВыбери организацию:", reply_markup=get_orgs_kb())
    last_messages[m.from_user.id] = sent.message_id


@dp.message(F.text)
async def handle_search(m: types.Message):
    query = m.text.strip()
    if len(query) < 2: return
    logging.info(f"SEARCH: {m.from_user.full_name} searched for '{query}'")
    await delete_prev_menu(m.from_user.id, m.bot)
    try:
        await m.delete()
    except:
        pass

    results = api_service.global_search(query)
    if not results:
        sent = await m.answer(f"🔍 По запросу «{query}» ничего не найдено.")
    else:
        kb = InlineKeyboardBuilder()
        for item in results:
            kind, org_id = item.get('kind'), item.get('organizationID')
            if kind == 'gateway':
                kb.button(text=f"📍 GW: {item.get('gatewayName')}",
                          callback_data=f"gwinfo_{item.get('gatewayMAC')}_{org_id}")
            elif kind == 'device':
                kb.button(text=f"📟 Dev: {item.get('deviceName')}",
                          callback_data=f"devinfo_{item.get('deviceDevEUI')}_{item.get('applicationID')}_{org_id}")
            elif kind == 'application':
                kb.button(text=f"📦 App: {item.get('applicationName')}",
                          callback_data=f"devlist_0_{item.get('applicationID')}_{org_id}")
        sent = await m.answer(f"🔍 Результаты ({len(results)}):", reply_markup=kb.adjust(1).as_markup())
    last_messages[m.from_user.id] = sent.message_id


# --- Хендлеры кнопок ---

@dp.callback_query(F.data == "back_to_orgs")
async def back_to_orgs_handler(c: types.CallbackQuery):
    await safe_edit(c, "Выбери организацию:", get_orgs_kb())


@dp.callback_query(F.data.startswith("org_"))
async def select_org(c: types.CallbackQuery):
    org_id = c.data.split("_")[1]
    await safe_edit(c, f"🏢 Организация ID: {org_id}", get_action_kb(org_id))


@dp.callback_query(F.data.startswith("gwp_"))
async def show_gws(c: types.CallbackQuery):
    _, offset, org_id = c.data.split("_")
    data, total = api_service.fetch_data(f"gateways?limit=10&offset={offset}&organizationID={org_id}")
    kb = InlineKeyboardBuilder()
    for gw in data: kb.button(text=f"📍 {gw['name']}", callback_data=f"gwinfo_{gw['id']}_{org_id}")
    kb.adjust(1)
    nav = []
    if int(offset) > 0: nav.append(
        types.InlineKeyboardButton(text="⬅️", callback_data=f"gwp_{int(offset) - 10}_{org_id}"))
    if int(offset) + 10 < total: nav.append(
        types.InlineKeyboardButton(text="➡️", callback_data=f"gwp_{int(offset) + 10}_{org_id}"))
    if nav: kb.row(*nav)
    kb.row(types.InlineKeyboardButton(text="⬅️ В меню", callback_data=f"org_{org_id}"))
    await safe_edit(c, f"📡 Станции ({total}):", kb.as_markup())


@dp.callback_query(F.data.startswith("app_"))
async def show_apps(c: types.CallbackQuery):
    parts = c.data.split("_")
    org_id, offset = parts[1], int(parts[2]) if len(parts) > 2 else 0
    data, total = api_service.fetch_data(f"applications?limit=10&offset={offset}&organizationID={org_id}")
    kb = InlineKeyboardBuilder()
    for app in data: kb.button(text=f"📦 {app['name']}", callback_data=f"devlist_0_{app['id']}_{org_id}")
    kb.adjust(1)
    nav = []
    if offset > 0: nav.append(types.InlineKeyboardButton(text="⬅️", callback_data=f"app_{org_id}_{offset - 10}"))
    if offset + 10 < total: nav.append(
        types.InlineKeyboardButton(text="➡️", callback_data=f"app_{org_id}_{offset + 10}"))
    if nav: kb.row(*nav)
    kb.row(types.InlineKeyboardButton(text="⬅️ В меню", callback_data=f"org_{org_id}"))
    await safe_edit(c, f"<b>Группы ({total}):</b>", kb.as_markup())


@dp.callback_query(F.data.startswith("devlist_"))
async def show_devices(c: types.CallbackQuery):
    parts = c.data.split("_")
    offset, app_id, org_id = int(parts[1]), parts[2], parts[3]
    data, total = api_service.fetch_devices(app_id, offset=offset)
    kb = InlineKeyboardBuilder()
    for d in data:
        eui = d.get('devEui') or d.get('devEUI')
        kb.button(text=f"📟 {d['name']}", callback_data=f"devinfo_{eui}_{app_id}_{org_id}")
    kb.adjust(1)
    nav = []
    if offset > 0: nav.append(
        types.InlineKeyboardButton(text="⬅️", callback_data=f"devlist_{offset - 10}_{app_id}_{org_id}"))
    if offset + 10 < total: nav.append(
        types.InlineKeyboardButton(text="➡️", callback_data=f"devlist_{offset + 10}_{app_id}_{org_id}"))
    if nav: kb.row(*nav)
    kb.row(types.InlineKeyboardButton(text="⬅️ К группам", callback_data=f"app_{org_id}_0"))
    await safe_edit(c, f"<b>Устройства ({total}):</b>", kb.as_markup())


@dp.callback_query(F.data.startswith("devinfo_"))
async def device_detail(c: types.CallbackQuery):
    _, eui, app_id, org_id = c.data.split("_")
    res = api_service.fetch_device_detail(eui)
    if not res: return
    text = (f"📟 <b>Устройство:</b> {res.get('device', {}).get('name')}\n"
            f"<b>EUI:</b> <code>{eui}</code>\n<b>Seen:</b> {res.get('lastSeenAt', 'Никогда')}")
    kb = InlineKeyboardBuilder()
    kb.button(text="📡 RAW Frames", callback_data=f"frames_devices_{eui}_{app_id}_{org_id}")
    kb.button(text="🔔 Device Events", callback_data=f"events_{eui}_{app_id}_{org_id}")
    kb.button(text="⬅️ Назад", callback_data=f"devlist_0_{app_id}_{org_id}")
    await safe_edit(c, text, kb.adjust(2, 1).as_markup())


@dp.callback_query(F.data.startswith("gwinfo_"))
async def gw_detail(c: types.CallbackQuery):
    _, gw_id, org_id = c.data.split("_")
    data = api_service.fetch_item(f"gateways/{gw_id}")
    if not data: return
    text = (f"📡 <b>Шлюз:</b> {data.get('gateway', {}).get('name')}\n"
            f"<b>MAC:</b> <code>{gw_id}</code>\n<b>Seen:</b> {data.get('lastSeenAt')}")
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 Frames", callback_data=f"frames_gateways_{gw_id}_{org_id}")
    kb.button(text="⬅️ Назад", callback_data=f"gwp_0_{org_id}")
    await safe_edit(c, text, kb.adjust(1).as_markup())


@dp.callback_query(F.data.startswith("frames_"))
async def show_frames_list(c: types.CallbackQuery):
    parts = c.data.split("_")
    kind, item_id = parts[1], parts[2]
    frames = api_service.frames_cache.get(f"fr_{item_id}") or api_service.fetch_frames(kind, item_id)
    app_id, org_id = (parts[3], parts[4]) if kind == "devices" else ("0", parts[3])
    if not frames:
        return await c.answer("Буфер пуст", show_alert=True)
    kb = InlineKeyboardBuilder()
    for i, f in enumerate(frames[:20]):
        res = f.get('result', {})
        inner = res.get('uplinkFrame') or res.get('downlinkFrame') or {}
        m_type = "DATA"
        try:
            phy = json.loads(inner.get('phyPayloadJSON', '{}'))
            m_type = phy.get('mhdr', {}).get('mType', 'RAW')
        except:
            pass
        icon = "⬆️" if "uplinkFrame" in res else "⬇️"
        time_str = api_service.format_ts(inner.get('publishedAt'))
        kb.button(
            text=f"{icon} {m_type} | {time_str}",
            callback_data=f"frview_{kind}_{item_id}_{i}_{app_id}_{org_id}"
        )
    back_cb = f"devinfo_{item_id}_{app_id}_{org_id}" if kind == "devices" else f"gwinfo_{item_id}_{org_id}"
    kb.adjust(1).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=back_cb))
    await safe_edit(c, f"📊 <b>Фреймы:</b> <code>{item_id}</code>", kb.as_markup())


@dp.callback_query(F.data.startswith(("frview_", "evview_")))
async def view_single_frame(c: types.CallbackQuery):
    is_event = c.data.startswith("evview_")
    parts = c.data.split("_")
    if is_event:
        item_id, idx, app_id, org_id = parts[1], int(parts[2]), parts[3], parts[4]
        cache_key = f"ev_{item_id}"
    else:
        kind, item_id, idx, app_id, org_id = parts[1], parts[2], int(parts[3]), parts[4], parts[5]
        cache_key = f"fr_{item_id}"
    frames = api_service.frames_cache.get(cache_key)
    if not frames or idx >= len(frames):
        return await c.answer("Данные устарели, обновите список", show_alert=True)
    res = frames[idx].get('result', {})
    if is_event:
        title = "🔔 Event Detail"
        raw_data = res.get('payloadJSON')
    else:
        title = "📡 Frame PHY Data"
        inner = res.get('uplinkFrame') or res.get('downlinkFrame') or {}
        raw_data = inner.get('phyPayloadJSON')
    try:
        display_data = json.loads(raw_data) if raw_data else res
        pretty_json = json.dumps(display_data, indent=2, ensure_ascii=False)[:3700]
    except:
        pretty_json = "Ошибка обработки данных"
    kb = InlineKeyboardBuilder()
    back_cb = f"events_{item_id}_{app_id}_{org_id}" if is_event else f"frames_{kind}_{item_id}_{app_id}_{org_id}"
    kb.button(text="⬅️ К списку", callback_data=back_cb)

    await safe_edit(c, f"📄 <b>{title} #{idx}:</b>\n<pre>{pretty_json}</pre>", kb.as_markup())


@dp.callback_query(F.data.startswith("events_"))
async def show_events_list(c: types.CallbackQuery):
    parts = c.data.split("_")
    eui, app_id, org_id = parts[1], parts[2], parts[3]
    events = api_service.frames_cache.get(f"ev_{eui}") or api_service.fetch_events(eui)
    if not events:
        return await c.answer("Событий нет", show_alert=True)
    kb = InlineKeyboardBuilder()
    for i, ev in enumerate(events[:15]):
        res = ev.get('result', {})
        inner_data = {}
        if res.get('payloadJSON'):
            try:
                inner_data = json.loads(res.get('payloadJSON'))
            except:
                pass
        e_type = (res.get('type') or inner_data.get('type') or "event").upper()
        icon = {"UP": "⬆️", "JOIN": "🔑", "STATUS": "🔋", "ACK": "✅", "TXACK": "📑", "ERROR": "❌"}.get(e_type, "📝")
        raw_time = res.get('publishedAt') or inner_data.get('publishedAt') or (
            inner_data.get('rxInfo', [{}])[0].get('time'))
        time_str = api_service.format_ts(raw_time)
        kb.button(text=f"{icon} {e_type} | {time_str}", callback_data=f"evview_{eui}_{i}_{app_id}_{org_id}")
    kb.adjust(1).row(
        types.InlineKeyboardButton(text="🔄 Обновить", callback_data=f"events_{eui}_{app_id}_{org_id}"),
        types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"devinfo_{eui}_{app_id}_{org_id}")
    )
    await safe_edit(c, f"🔔 <b>События:</b> <code>{eui}</code>", kb.as_markup())