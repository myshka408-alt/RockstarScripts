
mod = Module("Shift Tap", "Combat")
mod.setDesc("Приседает на несколько тиков при ударе по игроку")

duration     = Slider(mod, "Длительность (тики)").min(1).max(20).step(1).set(4)   
only_players = Checkbox(mod, "Только игроки")   

_state = {"ticks_left": 0}

def _release():
    try:
        mc.options.sneakKey.setPressed(False)
    except Exception:
        pass
    _state["ticks_left"] = 0

@events.attack
def on_attack(event):
    if not mod.isEnabled():
        return
    if not world.ingame() or mc.player is None:       
        return

    try:
        ent = event.getEntity()
    except Exception:
        return

    if only_players.get():
        try:
            if ent not in world.players():
                return
        except Exception:
            return

    try:
        mc.options.sneakKey.setPressed(True)
        _state["ticks_left"] = int(duration.get())
    except Exception:
        pass

@events.tick
def on_tick(event):
    
    if not mod.isEnabled() or not world.ingame():
        if _state["ticks_left"] > 0:
            _release()
        return

    if _state["ticks_left"] > 0:
        _state["ticks_left"] -= 1
        if _state["ticks_left"] <= 0:
            _release()

print("Shift Tap загружен")