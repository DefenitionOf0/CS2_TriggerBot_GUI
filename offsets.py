from requests import get as g


class Client:
    def __init__(self):
        try:
            self.offsets = g(
                'https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/offsets.json',
                timeout=15
            ).json()
            self.clientdll = g(
                'https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/client_dll.json',
                timeout=15
            ).json()
        except Exception as e:
            raise RuntimeError(f"Failed to download offsets. Check your internet connection. ({e})")

    def offset(self, a):
        try:
            return self.offsets['client.dll'][a]
        except KeyError:
            raise KeyError(f"Offset '{a}' not found in offsets data.")

    def get(self, a, b):
        try:
            return self.clientdll['client.dll']['classes'][a]['fields'][b]
        except KeyError:
            raise KeyError(f"Field '{b}' not found in class '{a}'.")
