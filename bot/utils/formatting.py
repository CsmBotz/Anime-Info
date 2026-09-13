import html

def escape_html(text: str) -> str:
    if not text:
        return ""
    return html.escape(str(text))

def clean_synopsis(synopsis: str, limit: int = 300) -> str:
    if not synopsis:
        return "No synopsis available."
    # Strip basic HTML tags if any present
    import re
    cleaned = re.sub(r'<[^<]+?>', '', synopsis)
    if len(cleaned) > limit:
        return escape_html(cleaned[:limit] + "...")
    return escape_html(cleaned)

def format_anime_card(title: str, status: str, score: str, synopsis: str, site_url: str = None) -> str:
    text = f"<b>{escape_html(title)}</b>\n"
    text += f"<b>Status:</b> {escape_html(status or 'N/A')} | <b>Score:</b> {escape_html(str(score or 'N/A'))}\n\n"
    text += f"<i>{clean_synopsis(synopsis)}</i>"
    if site_url:
        text += f'\n\n<a href="{escape_html(site_url)}">Read More on AniList</a>'
    return text

