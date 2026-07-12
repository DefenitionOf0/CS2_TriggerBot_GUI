import threading
from tkinter import messagebox

from offsets import Client
from settings import SettingsManager
from triggerbot import TriggerBotThread
from gui import TriggerBotApp


def main():
    app = None
    try:
        settings = SettingsManager()
        app = TriggerBotApp(settings)
        app.install_logger()

        def setup():
            print("[-] Loading offsets...")
            try:
                client_offsets = Client()
            except Exception as e:
                print(f"[-] Failed to load offsets: {e}")
                return

            print("[-] Starting TriggerBot...")
            try:
                bot = TriggerBotThread(settings, client_offsets)
                bot.start()
                app.set_bot_thread(bot)
            except Exception as e:
                print(f"[-] Failed to start TriggerBot: {e}")

        threading.Thread(target=setup, daemon=True).start()

        app.run()
    except Exception as e:
        messagebox.showerror("Fatal Error", f"An unexpected error occurred:\n{e}")
    finally:
        if app:
            app.uninstall_logger()


if __name__ == '__main__':
    main()
