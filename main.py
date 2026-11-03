import threading
import time
import platform
import requests

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout

KV = """
<RootUI>:
    orientation: "vertical"
    padding: "16dp"
    spacing: "10dp"

    Label:
        text: "Shellndrod"
        font_size: "24sp"
        size_hint_y: None
        height: "44dp"

    TextInput:
        id: token
        hint_text: "Telegram Bot Token"
        multiline: False
        password: True
        size_hint_y: None
        height: "48dp"

    TextInput:
        id: chat_id
        hint_text: "Your Telegram Chat ID"
        multiline: False
        size_hint_y: None
        height: "48dp"

    Button:
        text: "Start monitoring"
        size_hint_y: None
        height: "48dp"
        on_release: app.start_monitoring(token.text.strip(), chat_id.text.strip())

    Button:
        text: "Stop monitoring"
        size_hint_y: None
        height: "48dp"
        on_release: app.stop_monitoring()

    Label:
        text: app.status_text
        halign: "left"
        valign: "top"
        text_size: self.width, None
"""

class RootUI(BoxLayout):
    pass


class ShellndrodApp(App):
    status_text = StringProperty("Enter your bot token and chat ID, then start monitoring.")
    running = False
    worker = None
    token = "8508402230:AAGK5iP1fxc7Dscu5pDmqWkAGLCCYLtKrB0"
    chat_id = "8897834377"
    offset = 0

    def build(self):
        Builder.load_string(KV)
        return RootUI()

    def set_status(self, message):
        self.status_text = message

    def telegram_send(self, text):
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        try:
            requests.post(
                url,
                data={"chat_id": self.chat_id, "text": text},
                timeout=15
            ).raise_for_status()
        except requests.RequestException as exc:
            Clock.schedule_once(
                lambda dt: self.set_status(f"Telegram send error: {exc}"), 0
            )

    def device_status(self):
        details = [
            "Shellndrod status: online",
            f"Platform: {platform.system()}",
            f"Python: {platform.python_version()}",
            "Monitoring: active"
        ]

        try:
            from plyer import battery
            info = battery.get_status()
            if info:
                level = info.get("percentage")
                charging = info.get("isCharging")
                if level is not None:
                    details.append(f"Battery: {level}%")
                if charging is not None:
                    details.append(f"Charging: {'yes' if charging else 'no'}")
        except Exception:
            details.append("Battery information: unavailable")

        return "\n".join(details)

    def start_monitoring(self, token, chat_id):
        if self.running:
            self.set_status("Monitoring is already active.")
            return
        if not token or not chat_id:
            self.set_status("Please enter both the bot token and chat ID.")
            return

        self.token = token
        self.chat_id = chat_id
        self.offset = 0
        self.running = True
        self.worker = threading.Thread(target=self.poll_updates, daemon=True)
        self.worker.start()
        self.set_status("Monitoring started. Allowed Telegram commands: /help, /status, /exit")
        self.telegram_send("Shellndrod connected. Send /help to see available commands.")

    def stop_monitoring(self):
        self.running = False
        self.set_status("Monitoring stopped.")

    def poll_updates(self):
        base_url = f"https://api.telegram.org/bot{self.token}"
        while self.running:
            try:
                response = requests.get(
                    f"{base_url}/getUpdates",
                    params={"offset": self.offset + 1, "timeout": 20},
                    timeout=25
                )
                response.raise_for_status()
                payload = response.json()

                if not payload.get("ok"):
                    time.sleep(3)
                    continue

                for update in payload.get("result", []):
                    self.offset = update.get("update_id", self.offset)
                    message = update.get("message") or {}
                    chat = message.get("chat") or {}

                    # Only accept messages from the chat ID entered by the device owner.
                    if str(chat.get("id")) != self.chat_id:
                        continue

                    command = (message.get("text") or "").strip().split()
                    if not command:
                        continue

                    cmd = command[0].lower()
                    if cmd == "/help":
                        self.telegram_send(
                            "Available commands:\n"
                            "/status - show basic app/device status\n"
                            "/help - show this help\n"
                            "/exit - stop Telegram monitoring"
                        )
                    elif cmd == "/status":
                        self.telegram_send(self.device_status())
                    elif cmd == "/exit":
                        self.telegram_send("Monitoring stopped by request.")
                        self.running = False
                        Clock.schedule_once(
                            lambda dt: self.set_status("Monitoring stopped by Telegram /exit."), 0
                        )
                        break
                    else:
                        self.telegram_send("Unknown command. Send /help.")

            except requests.RequestException:
                time.sleep(5)
            except Exception:
                time.sleep(5)

    def on_stop(self):
        self.running = False


if __name__ == "__main__":
    ShellndrodApp().run()
