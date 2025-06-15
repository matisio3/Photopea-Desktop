import webview
import keyboard
import threading
import time
from pypresence import Presence
from tkinter import filedialog
import base64

CLIENT_ID = '1383776567901159494'
RPC = None
window = None

# Prosty system lokalizacji
def get_language():
    import locale
    lang = (locale.getdefaultlocale()[0] or "en").lower()
    return "pl" if lang.startswith("pl") else "en"

translations = {
    "pl": {
        "opening": "Otwieranie projektu...",
        "editing": "Edytuje",
        "details": "Używa Photopea",
        "large_text": "Edytor Photopea"
    },
    "en": {
        "opening": "Opening project...",
        "editing": "Editing",
        "details": "Using Photopea",
        "large_text": "Photopea Editor"
    }
}

lang = get_language()
T = translations[lang]

def toggle_fullscreen():
    if window:
        window.toggle_fullscreen()

def keyboard_listener():
    while True:
        keyboard.wait('f11')
        toggle_fullscreen()
        time.sleep(0.2)

def save_file(base64_data, filename="image.png"):
    file_path = filedialog.asksaveasfilename(defaultextension=".png", initialfile=filename,
                                             filetypes=[("PNG Files", "*.png"), ("All Files", "*.*")])
    if file_path:
        with open(file_path, "wb") as f:
            f.write(base64.b64decode(base64_data.split(",")[1]))

class API:
    def save(self, data_url):
        save_file(data_url)

    def update_rpc(self, state_text, details_text, large_text):
        try:
            RPC.update(
                state=state_text,
                details=details_text,
                large_image="photopea",
                large_text=large_text
            )
        except Exception as e:
            print("RPC update failed:", e)

def start_discord_rpc():
    global RPC
    try:
        RPC = Presence(CLIENT_ID)
        RPC.connect()
        # ✅ Początkowy status z lokalizacją
        RPC.update(
            state=T["opening"],
            details=T["details"],
            large_image="photopea",
            large_text=T["large_text"]
        )
    except Exception as e:
        print("RPC connection failed:", e)

def inject_js():
    while True:
        result = window.evaluate_js("""
            (function() {
                const el = document.querySelector('.panelhead .active');
                return el && el.getAttribute('title') ? true : false;
            })()
        """)
        if result:
            break
        time.sleep(1)

    js = f"""
    const translations = {{
        pl: {{
            editing: "Edytuje",
            details: "Używa Photopea",
            largeText: "Edytor Photopea"
        }},
        en: {{
            editing: "Editing",
            details: "Using Photopea",
            largeText: "Photopea Editor"
        }}
    }};

    function detectLanguage() {{
        const lang = navigator.language || "en";
        return lang.toLowerCase().startsWith("pl") ? "pl" : "en";
    }}

    function updateDiscordStatus() {{
        try {{
            const lang = detectLanguage();
            const t = translations[lang];
            const title = document.querySelector('.panelhead .active')?.getAttribute('title') || "project";
            const state = `${{t.editing}} ${{title}}`;
            pywebview.api.update_rpc(state, t.details, t.largeText);
        }} catch (e) {{}}
    }}

    updateDiscordStatus();
    setInterval(updateDiscordStatus, 10000);

    document.addEventListener('click', function(e) {{
        if (e.target.tagName === 'A' && e.target.href.startsWith('blob:')) {{
            e.preventDefault();
            fetch(e.target.href)
                .then(res => res.blob())
                .then(blob => {{
                    const reader = new FileReader();
                    reader.onloadend = function() {{
                        pywebview.api.save(reader.result);
                    }};
                    reader.readAsDataURL(blob);
                }});
        }}
    }}, true);
    """
    window.evaluate_js(js)

def start():
    global window
    threading.Thread(target=keyboard_listener, daemon=True).start()
    threading.Thread(target=start_discord_rpc, daemon=True).start()
    api = API()
    window = webview.create_window("Photopea", "https://www.photopea.com/", js_api=api)
    webview.start(func=inject_js, gui='edgechromium')

if __name__ == '__main__':
    start()
