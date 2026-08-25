import math

mod = Module("Eagle", "Movement")
mod.setDesc("Автоприсед у края блока, чтобы не свалиться вниз")

margin = Slider(mod, "Запас у края").min(0.0).max(0.4).step(0.05).set(0.2)
distance = Slider(mod, "Дистанция").min(0.0).max(3.0).step(0.1).set(1.0)
gui = Checkbox(mod, "Приседать в GUI")  

try:
    BlockPos = jimport("net.minecraft.util.math.BlockPos")
except Exception as e:
    BlockPos = None
    client.warn("Eagle: не смог jimport BlockPos: " + str(e))

_state = {"sneaking": False}
_warned = {"ground": False, "tick": False}


def _is_air(state):
    val = state.isAir
    return bool(val()) if callable(val) else bool(val)


def _ground_at(x, y, z):
    if BlockPos is None or mc.world is None:
        return True  
    try:
        pos = BlockPos(int(math.floor(x)), int(math.floor(y)), int(math.floor(z)))
        state = mc.world.getBlockState(pos)
        return not _is_air(state)
    except Exception as e:
        if not _warned["ground"]:
            _warned["ground"] = True
            client.warn("Eagle: ошибка проверки блока: " + str(e))
        return True


def _horizontal_dir(p):
    try:
        vel = p.getVelocity()
        vx, vz = vel.getX(), vel.getZ()
    except Exception:
        return None
    speed = math.hypot(vx, vz)
    if speed < 1e-4:
        return None
    return vx / speed, vz / speed


def _apply(want):
    try:
        mc.options.sneakKey.setPressed(want)
    except Exception as e:
        if not _warned["tick"]:
            _warned["tick"] = True
            client.warn("Eagle: ошибка нажатия sneak: " + str(e))

    try:
        in_gui = mc.currentScreen is not None
    except Exception:
        in_gui = False

    try:
        if in_gui or mc.player.isSneaking() != want:
            mc.player.setSneaking(want)
    except Exception:
        pass

    _state["sneaking"] = want


def _update():
    if not mod.isEnabled() or not world.ingame() or mc.player is None:
        _apply(False)
        return

    if mc.currentScreen is not None and not gui.get():
        _apply(False)
        return

    p = mc.player
    try:
        on_ground = p.isOnGround()
    except Exception:
        on_ground = True

    if not on_ground:
        _apply(False)
        return

    hw = 0.3 + margin.get()   
    x, y, z = p.getX(), p.getY(), p.getZ()
    y_below = y - 0.05

    points = [
        (x + hw, z + hw),
        (x + hw, z - hw),
        (x - hw, z + hw),
        (x - hw, z - hw),
    ]

    look_ahead = distance.get()
    if look_ahead > 0:
        d = _horizontal_dir(p)
        if d is not None:
            dx, dz = d
            lx, lz = x + dx * look_ahead, z + dz * look_ahead
            points += [
                (lx + hw, lz + hw),
                (lx + hw, lz - hw),
                (lx - hw, lz + hw),
                (lx - hw, lz - hw),
            ]

    edge = any(not _ground_at(cx, y_below, cz) for cx, cz in points)
    _apply(edge)


@events.tick
def on_tick(event):
    _update()


@events.close_screen
def on_close_screen(event):
    try:
        _update()
    except Exception as e:
        client.warn("Eagle: ошибка на close_screen: " + str(e))


print("Eagle загружен")