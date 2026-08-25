mod = Module("Reach", "Combat")
mod.setDesc("Дистанция взаимодействия с блоками и сущностями (через атрибуты MC)")

entity_range = Slider(mod, "Энтити дистанция").min(3.0).max(6.0).step(0.1).set(3.0)
block_range  = Slider(mod, "Дистанция на блоки").min(4.5).max(6.0).step(0.1).set(4.5)
affect_entity = Checkbox(mod, "Воздействовать на сущности").set(True)
affect_block  = Checkbox(mod, "Воздействовать на блоки").set(True)

try:
    EA = jimport("net.minecraft.entity.attribute.EntityAttributes")
except Exception as e:
    EA = None
    client.warn("Reach: не смог jimport EntityAttributes: " + str(e))

_state = {"entity_base": None, "block_base": None}
_warned = {"tick": False}

def _instances():
    if mc.player is None or EA is None:
        return None, None
    ei = bi = None
    try:
        ei = mc.player.getAttributeInstance(EA.ENTITY_INTERACTION_RANGE)
    except Exception:
        pass
    try:
        bi = mc.player.getAttributeInstance(EA.BLOCK_INTERACTION_RANGE)
    except Exception:
        pass
    return ei, bi

@events.tick
def on_tick(event):
    if not world.ingame() or mc.player is None or EA is None:
        return

    ei, bi = _instances()

    try:
        if ei is not None and _state["entity_base"] is None:
            _state["entity_base"] = ei.getBaseValue() 
        if bi is not None and _state["block_base"] is None:
            _state["block_base"] = bi.getBaseValue()
    except Exception:
        pass

    if mod.isEnabled():
        try:
            if ei is not None and affect_entity.get():
                ei.setBaseValue(entity_range.get())
        except Exception as e:
            if not _warned["tick"]:
                _warned["tick"] = True
                client.warn("Reach: ошибка applying entity range: " + str(e))
        try:
            if bi is not None and affect_block.get():
                bi.setBaseValue(block_range.get())
        except Exception as e:
            if not _warned["tick"]:
                _warned["tick"] = True
                client.warn("Reach: ошибка applying block range: " + str(e))
    else:
        try:
            if ei is not None and _state["entity_base"] is not None:
                ei.setBaseValue(_state["entity_base"])
        except Exception:
            pass
        try:
            if bi is not None and _state["block_base"] is not None:
                bi.setBaseValue(_state["block_base"])
        except Exception:
            pass

print("Reach загружен")
