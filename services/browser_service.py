
import webbrowser


def open_url(url: str) -> None:
    print(f"[JARVIS] Opening URL: {url}")
    webbrowser.open(url)


def open_youtube() -> None:
    open_url("https://youtube.com")


def open_chatgpt() -> None:
    open_url("https://chat.openai.com")


def search_google(query: str) -> None:
    query = query.strip()
    if not query:
        query = ""
    search_url = f"https://google.com/search?q={query.replace(' ', '+')}"
    open_url(search_url)
