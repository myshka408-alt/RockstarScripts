mod = Module("Bow Spam", "Combat")
mod.setDesc("Форсированный выстрел из лука через N тиков натяжения")

draw_ticks = Slider(mod, "Тики натяжения").min(4).max(20).step(1).set(4)

_ticks_using = {"n": 0}
_warned = {"stop": False, "fallback": False}


def _holding_bow():
    try:
        item_id = inventory.id(inventory.selected())
    except Exception:
        return False
    if not item_id:
        return False
    return str(item_id).split(":")[-1] == "bow"


def _force_shot(p):
    try:
        mc.interactionManager.stopUsingItem(p)
        return
    except Exception as e:
        if not _warned["fallback"]:
            _warned["fallback"] = True
            client.warn("BowSpam: interactionManager недоступен (" + str(e) + "), фолбэк на stopUsingItem()")
    try:
        p.stopUsingItem()
    except Exception as e:
        if not _warned["stop"]:
            _warned["stop"] = True
            client.warn("BowSpam: ошибка stopUsingItem: " + str(e))


@events.tick
def on_tick(event):
    if not mod.isEnabled() or not world.ingame() or mc.player is None:
        _ticks_using["n"] = 0
        return

    p = mc.player
    try:
        using = p.isUsingItem()
    except Exception:
        using = False

    if not using or not _holding_bow():
        _ticks_using["n"] = 0
        return

    _ticks_using["n"] += 1
    if _ticks_using["n"] >= draw_ticks.get():
        _force_shot(p)
        _ticks_using["n"] = 0


print("Bow Spam загружен")