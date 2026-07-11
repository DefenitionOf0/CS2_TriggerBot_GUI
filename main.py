import threading

from offsets import Client
from settings import SettingsManager
from triggerbot import TriggerBotThread
from gui import TriggerBotApp


def main():
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
        bot = TriggerBotThread(settings, client_offsets)
        bot.start()
        app.set_bot_thread(bot)

    threading.Thread(target=setup, daemon=True).start()

    app.run()
    app.uninstall_logger()


if __name__ == '__main__':
    main()
