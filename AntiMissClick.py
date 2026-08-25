mod = Module("Anti Miss Click", "Combat")
mod.setDesc("Отменяет левый клик, если прицел не на энтити (или блоке)")

allow_blocks = Checkbox(mod, "Ломать блоки")

@events.mouse
def on_mouse(event):
    if not mod.isEnabled():
        return
    if mc.currentScreen is not None:
        return
    if client.menu_opened():
        return
    if event.getButton() != 0 or event.getAction() != 1:
        return

    hit = mc.crosshairTarget
    if hit is None:
        event.cancel()
        return

    hit_type = str(hit.getType())

    if hit_type == "MISS":
        event.cancel()
        return

    if hit_type == "BLOCK" and not allow_blocks.get():
        event.cancel()
        return

print("Anti Miss Click загружен")