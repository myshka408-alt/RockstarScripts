# HitSound.py — модуль "Hit Sound" для чит-клиента Rockstar (Minecraft)

import os
import random
import threading
import traceback
import time
import urllib.request
import zipfile

ASSET_URL  = "https://github.com/myshka408-alt/RockstarScripts/raw/refs/heads/main/Hit%20Sounds.zip"
TARGET_DIR = r"C:\Rockstar\game\Rockstar\scripts"
ASSET_DIR  = os.path.join(TARGET_DIR, "Hit Sounds")

MOAN_FILES  = ["moan1.ogg", "moan2.ogg", "moan3.ogg", "moan4.ogg"]
MOAN_CHANCE = 0.25

mod = Module("Hit Sound", "Combat")
mod.setDesc("Проигрывает звук при ударе по сущности")

mode        = Mode(mod, "Звук").add("NeverLose").add("Skeet").add("UwU").add("Стоны")
volume      = Slider(mod, "Громкость").min(0).max(100).step(1).set(100).suffix("%")
no_hit      = Checkbox(mod, "Без звуков")  # не играть звук, если удар был обычным (не крит)

_sound_files = {}
_mixer_ok    = False
_assets_ok   = False


def _log(msg):
    print("[Hit Sound] " + msg)


def _index_assets():
    wanted = {"neverlose.wav", "skeet.ogg", "uwu.ogg"} | set(MOAN_FILES)
    found  = {}
    if os.path.isdir(ASSET_DIR):
        for root, _dirs, files in os.walk(ASSET_DIR):
            for f in files:
                low = f.lower()
                if low in wanted and low not in found:
                    found[low] = os.path.join(root, f)
    return found


def _setup():
    global _sound_files, _assets_ok, _mixer_ok

    try:
        import pygame
        pygame.mixer.init()
        _mixer_ok = True
        _log("pygame.mixer готов")
    except Exception:
        client.warn("Hit Sound: нет pygame — выполни  .py install pygame  и перезагрузи скрипт")
        _log(traceback.format_exc())

    try:
        already = _index_assets()
        needed  = {"neverlose.wav", "skeet.ogg", "uwu.ogg"} | set(MOAN_FILES)
        if needed.issubset(already):
            _sound_files = already
            _assets_ok   = True
            _log("звуки уже на диске (" + str(len(already)) + "), скачивание не нужно")
        else:
            client.msg("Hit Sound: скачиваю звуки...")
            os.makedirs(ASSET_DIR, exist_ok=True)
            zip_path = os.path.join(TARGET_DIR, "_hitsound_tmp.zip")
            urllib.request.urlretrieve(ASSET_URL, zip_path)

            with zipfile.ZipFile(zip_path, "r") as z:
                for member in z.infolist():
                    filename = os.path.basename(member.filename)
                    if not filename:
                        continue
                    dest = os.path.join(ASSET_DIR, filename)
                    with z.open(member) as src, open(dest, "wb") as dst:
                        dst.write(src.read())

            try:
                os.remove(zip_path)
            except OSError:
                pass

            _sound_files = _index_assets()
            missing = needed - set(_sound_files)
            if missing:
                client.warn("Hit Sound: не нашёл в архиве: " + ", ".join(sorted(missing)))
            _assets_ok = True
            client.msg("Hit Sound: готово (" + str(len(_sound_files)) + " файлов)")

    except Exception:
        client.error("Hit Sound: ошибка загрузки ассетов, смотри latest.log")
        _log(traceback.format_exc())


threading.Thread(target=_setup, daemon=True).start()


def _play(filename):
    if not _assets_ok or not _mixer_ok:
        client.msg("Hit Sound: не готов (assets=" + str(_assets_ok) + " mixer=" + str(_mixer_ok) + ")")
        return
    path = _sound_files.get(filename)
    if not path or not os.path.isfile(path):
        client.msg("Hit Sound: файл не найден — " + filename)
        _log("не найден: " + filename + " | есть: " + str(list(_sound_files.keys())))
        return
    try:
        import pygame
        vol = max(0.0, min(1.0, volume.get() / 100.0))
        snd = pygame.mixer.Sound(path)
        snd.set_volume(vol)
        snd.play()
        _log("играю: " + filename)
    except Exception:
        client.msg("Hit Sound: ошибка pygame — " + filename + " (смотри latest.log)")
        _log("ошибка воспроизведения " + filename + ": " + traceback.format_exc())


def _is_critical_hit(player):
    """Повторяет ванильное условие крита из PlayerEntity.attack():
    падение без касания земли, не крадётся по лестнице/лозе, не в воде,
    без транспорта и без спринта."""
    if player is None:
        return False
    try:
        fall = player.getFallDistance()
        on_ground = player.isOnGround()
        sprinting = player.isSprinting()
        try:
            climbing = player.isClimbing()
        except Exception:
            climbing = False
        try:
            in_water = player.isTouchingWater()
        except Exception:
            in_water = False
        try:
            has_vehicle = player.hasVehicle()
        except Exception:
            has_vehicle = False
        return (fall > 0.0) and not on_ground and not climbing and not in_water and not has_vehicle and not sprinting
    except Exception:
        _log("не удалось определить крит: " + traceback.format_exc())
        return False


# ------------------------------------------------------------------
# Заглушение родного звука удара/крита Rockstar (категория PLAYERS).
#
# ВАЖНО: события `sound` в API клиента только НАБЛЮДАЮТ — отменить звук
# через них нельзя (это прямо написано в references/events.md). Поэтому
# здесь используется другой путь: событие `attack` приходит ДО того, как
# клиент проигрывает звук атаки, так что можно на мгновение выкрутить в 0
# громкость категории "Игроки" (SoundCategory.PLAYERS) и тут же вернуть
# обратно. Это НЕ задокументированный в SKILL.md метод скриптинга, а сырой
# ванильный Java-вызов через mc.options — если в вашей сборке Rockstar
# имя/сигнатура другие, при первой попытке в чат придёт предупреждение,
# а в latest.log — трейсбек. Кастомный звук модуля идёт через pygame,
# отдельно от звукового движка игры, так что это заглушение на него
# не влияет.
# ------------------------------------------------------------------

MUTE_DURATION = 0.35  # секунд с запасом, чтобы наверняка перекрыть проигрывание звука атаки

_sound_option        = None
_orig_players_volume = None
_mute_deadline        = 0.0
_mute_warned          = False


def _get_players_volume_option():
    global _sound_option
    if _sound_option is not None:
        return _sound_option
    try:
        SoundCategory = jimport("net.minecraft.sound.SoundCategory")
        _sound_option = mc.options.getSoundVolumeOption(SoundCategory.PLAYERS)
        return _sound_option
    except Exception:
        _log("не нашёл регулятор громкости категории PLAYERS: " + traceback.format_exc())
        return None


def _mute_vanilla_attack_sound():
    global _orig_players_volume, _mute_deadline, _mute_warned
    opt = _get_players_volume_option()
    if opt is None:
        if not _mute_warned:
            client.warn("Hit Sound: не смог заглушить родной звук удара в этой сборке клиента (смотри latest.log)")
            _mute_warned = True
        return
    try:
        if _orig_players_volume is None:
            _orig_players_volume = opt.getValue()
        opt.setValue(0.0)
        _mute_deadline = time.time() + MUTE_DURATION
    except Exception:
        _log("ошибка при заглушении звука атаки: " + traceback.format_exc())


def _restore_vanilla_volume():
    global _orig_players_volume
    if _orig_players_volume is None:
        return
    opt = _get_players_volume_option()
    try:
        if opt is not None:
            opt.setValue(_orig_players_volume)
    except Exception:
        _log("ошибка восстановления громкости: " + traceback.format_exc())
    finally:
        _orig_players_volume = None


@events.tick
def on_tick(event):
    # подстраховка: возвращаем громкость сразу, как истёк буфер заглушения
    if _orig_players_volume is not None and time.time() >= _mute_deadline:
        _restore_vanilla_volume()


@events.module_toggled
def on_module_toggled(event):
    # если модуль выключили прямо во время заглушения — не оставляем игрока без звука
    try:
        if event.getModule().getName() == mod.getName() and not event.isState():
            _restore_vanilla_volume()
    except Exception:
        _log("ошибка в module_toggled: " + traceback.format_exc())


@events.attack
def on_attack(e):
    if not mod.isEnabled():
        return
    if not is_instance(e.getEntity(), "net.minecraft.entity.LivingEntity"):
        return

    is_crit = _is_critical_hit(mc.player)
    if is_crit and no_crit.get():
        _mute_vanilla_attack_sound()
    elif not is_crit and no_hit.get():
        _mute_vanilla_attack_sound()

    choice = mode.get()

    if choice == "NeverLose":
        _play("neverlose.wav")
    elif choice == "Skeet":
        _play("skeet.ogg")
    elif choice == "UwU":
        _play("uwu.ogg")
    elif choice == "Стоны":
        picked = random.choice(MOAN_FILES)
        _play(picked)


_log("модуль загружен")