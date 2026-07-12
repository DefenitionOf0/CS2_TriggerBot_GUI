import ctypes
import time
import threading
from random import uniform

import pymem
import pymem.process
import keyboard
from pynput.mouse import Controller, Button
from win32gui import GetWindowText, GetForegroundWindow

mouse = Controller()


def is_process_alive(pm):
    """Check if the attached process is still running."""
    STILL_ACTIVE = 259
    exit_code = ctypes.c_ulong()
    handle = getattr(pm, "process_handle", None)
    if handle is None:
        return False
    if ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
        return exit_code.value == STILL_ACTIVE
    return False


class TriggerBotThread(threading.Thread):
    def __init__(self, settings, offsets):
        super().__init__(daemon=True)
        self.settings = settings
        self.offsets = offsets
        self.running = True

    def run(self):
        try:
            pm = pymem.Pymem("cs2.exe")
            client = pymem.process.module_from_name(pm.process_handle, "client.dll").lpBaseOfDll
        except Exception as e:
            print(f"[-] Failed to attach to CS2. Please open CS2 first. Error: {e}")
            return

        try:
            dwEntityList = self.offsets.offset('dwEntityList')
            dwLocalPlayerPawn = self.offsets.offset('dwLocalPlayerPawn')
            m_iIDEntIndex = self.offsets.get('C_CSPlayerPawn', 'm_iIDEntIndex')
            m_iTeamNum = self.offsets.get('C_BaseEntity', 'm_iTeamNum')
            m_iHealth = self.offsets.get('C_BaseEntity', 'm_iHealth')
        except Exception as e:
            print(f"[-] Failed to resolve offsets: {e}")
            return

        print("[-] TriggerBot started.")

        while self.running:
            try:
                if not is_process_alive(pm):
                    print("[-] CS2 process closed. Stopping TriggerBot.")
                    break

                cfg = self.settings.get()
                if not cfg.enabled:
                    time.sleep(0.1)
                    continue

                if GetWindowText(GetForegroundWindow()) != "Counter-Strike 2":
                    time.sleep(0.1)
                    continue

                if keyboard.is_pressed(cfg.trigger_key):
                    player = pm.read_longlong(client + dwLocalPlayerPawn)
                    entityId = pm.read_int(player + m_iIDEntIndex)

                    if entityId > 0:
                        entList = pm.read_longlong(client + dwEntityList)
                        entEntry = pm.read_longlong(entList + 0x8 * (entityId >> 9) + 0x10)
                        entity = pm.read_longlong(entEntry + 120 * (entityId & 0x1FF))

                        if cfg.check_team:
                            entityTeam = pm.read_int(entity + m_iTeamNum)
                            playerTeam = pm.read_int(player + m_iTeamNum)
                            if entityTeam == playerTeam:
                                time.sleep(0.03)
                                continue

                        entityHp = pm.read_int(entity + m_iHealth)
                        if entityHp <= 0:
                            time.sleep(0.03)
                            continue

                        time.sleep(uniform(cfg.delay_min, cfg.delay_max))
                        mouse.press(Button.left)
                        time.sleep(uniform(cfg.hold_min, cfg.hold_max))
                        mouse.release(Button.left)

                    time.sleep(0.03)
                else:
                    time.sleep(0.1)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[-] TriggerBot error: {e}")
                time.sleep(0.1)

        print("[-] TriggerBot stopped.")
