"""
قالب صفحة الـ Web App - يبني HTML ديناميكياً بحسب المستخدم والقالب المختار
"""
from html import escape
from typing import List, Dict, Any


THEME_STYLES = {
    # القالب الافتراضي للمجاني: أزرار رمادية وخلفية بيضاء
    0: """
        :root {
            --bg: #f5f5f7;
            --card: #ffffff;
            --text: #1c1c1e;
            --muted: #6b6b70;
            --btn-bg: #e5e5ea;
            --btn-bg-hover: #d1d1d6;
            --btn-text: #1c1c1e;
            --accent: #007aff;
            --shadow: 0 1px 3px rgba(0,0,0,0.06);
            --avatar-ring: #d1d1d6;
        }
        body { background: var(--bg); }
        .btn { background: var(--btn-bg); color: var(--btn-text); border: none; }
        .btn:hover { background: var(--btn-bg-hover); transform: translateY(-1px); }
    """,
    # Dark Cyber
    1: """
        :root {
            --bg: #05060a;
            --card: rgba(20, 22, 32, 0.7);
            --text: #e6faff;
            --muted: #7aa3b8;
            --btn-bg: linear-gradient(90deg, #0ff 0%, #7c3aed 100%);
            --btn-bg-hover: linear-gradient(90deg, #7c3aed 0%, #0ff 100%);
            --btn-text: #05060a;
            --accent: #00fff7;
            --shadow: 0 0 20px rgba(0, 255, 247, 0.25);
            --avatar-ring: #00fff7;
        }
        body {
            background:
              radial-gradient(1200px 600px at 20% 0%, rgba(0,255,247,0.15), transparent 60%),
              radial-gradient(900px 500px at 80% 100%, rgba(124,58,237,0.18), transparent 60%),
              #05060a;
        }
        .card { border: 1px solid rgba(0,255,247,0.15); }
        .btn { background: var(--btn-bg); color: var(--btn-text); font-weight: 700;
               box-shadow: var(--shadow); border: none; }
        .btn:hover { background: var(--btn-bg-hover); transform: translateY(-2px); }
        h1 { text-shadow: 0 0 12px rgba(0,255,247,0.5); }
    """,
    # Neon Glow (وردي)
    2: """
        :root {
            --bg: #150014;
            --card: rgba(45, 5, 45, 0.6);
            --text: #ffe6f7;
            --muted: #ff9ecf;
            --btn-bg: linear-gradient(135deg, #ff2fa0, #ff7ac3);
            --btn-bg-hover: linear-gradient(135deg, #ff7ac3, #ff2fa0);
            --btn-text: #ffffff;
            --accent: #ff2fa0;
            --shadow: 0 0 25px rgba(255, 47, 160, 0.45);
            --avatar-ring: #ff2fa0;
        }
        body {
            background:
              radial-gradient(1000px 500px at 50% 0%, rgba(255,47,160,0.25), transparent 60%),
              radial-gradient(800px 400px at 50% 100%, rgba(255,122,195,0.20), transparent 60%),
              #150014;
        }
        .card { border: 1px solid rgba(255, 47, 160, 0.25); }
        .btn { background: var(--btn-bg); color: var(--btn-text); font-weight: 700;
               box-shadow: var(--shadow); border: none; }
        .btn:hover { background: var(--btn-bg-hover); transform: translateY(-2px) scale(1.01); }
        h1 { text-shadow: 0 0 14px rgba(255,47,160,0.6); }
    """,
    # Glassmorphism
    3: """
        :root {
            --bg: #0b1220;
            --card: rgba(255,255,255,0.08);
            --text: #f4f7fb;
            --muted: #b7c3d6;
            --btn-bg: rgba(255,255,255,0.10);
            --btn-bg-hover: rgba(255,255,255,0.18);
            --btn-text: #ffffff;
            --accent: #8ab4ff;
            --shadow: 0 8px 32px rgba(0,0,0,0.28);
            --avatar-ring: rgba(255,255,255,0.35);
        }
        body {
            background:
              radial-gradient(900px 500px at 15% 10%, rgba(138,180,255,0.28), transparent 60%),
              radial-gradient(900px 500px at 85% 90%, rgba(180,120,255,0.22), transparent 60%),
              linear-gradient(180deg, #0b1220 0%, #101a2e 100%);
        }
        .card {
            background: var(--card);
            border: 1px solid rgba(255,255,255,0.14);
            backdrop-filter: blur(24px);
            -webkit-backdrop-filter: blur(24px);
        }
        .btn {
            background: var(--btn-bg);
            color: var(--btn-text);
            border: 1px solid rgba(255,255,255,0.20);
            backdrop-filter: blur(12px);
        }
        .btn:hover { background: var(--btn-bg-hover); transform: translateY(-2px); }
    """,
}


def render_page(user: Dict[str, Any], links: List[Dict[str, Any]]) -> str:
    """توليد HTML لصفحة الويب المصغرة الخاصة بالمستخدم"""
    theme = user.get("theme") or 0
    if theme not in THEME_STYLES:
        theme = 0
    theme_css = THEME_STYLES[theme]

    title = escape(user.get("page_title") or user.get("full_name") or "صفحتي")
    bio = escape(user.get("page_bio") or "")
    user_id = int(user["user_id"])
    initial = (title[:1] or "?").upper()

    # بناء أزرار الروابط
    links_html_parts = []
    for link in links:
        link_title = escape(link["title"])
        link_url = escape(link["url"], quote=True)
        link_id = int(link["id"])
        links_html_parts.append(
            f'<a class="btn" href="{link_url}" target="_blank" rel="noopener" '
            f'data-link-id="{link_id}">{link_title}</a>'
        )
    links_html = "\n".join(links_html_parts) if links_html_parts \
        else '<p class="empty">لم يتم إضافة أي روابط بعد</p>'

    html = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <meta name="theme-color" content="#000000">
    <title>{title}</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        html, body {{
            min-height: 100vh;
            font-family: 'Tajawal', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            color: var(--text);
            -webkit-font-smoothing: antialiased;
        }}
        {theme_css}
        .wrap {{
            max-width: 520px;
            margin: 0 auto;
            padding: 32px 20px 48px;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: stretch;
        }}
        .avatar {{
            width: 96px; height: 96px;
            border-radius: 50%;
            margin: 8px auto 20px;
            background: var(--btn-bg);
            display: grid; place-items: center;
            font-size: 40px; font-weight: 800;
            color: var(--btn-text);
            border: 3px solid var(--avatar-ring);
            box-shadow: var(--shadow);
        }}
        h1 {{
            font-size: 24px;
            font-weight: 800;
            text-align: center;
            color: var(--text);
            margin-bottom: 8px;
            letter-spacing: -0.3px;
        }}
        .bio {{
            font-size: 15px;
            text-align: center;
            color: var(--muted);
            margin-bottom: 28px;
            line-height: 1.6;
            padding: 0 8px;
        }}
        .card {{
            background: var(--card);
            border-radius: 20px;
            padding: 20px 16px;
            box-shadow: var(--shadow);
        }}
        .links {{ display: flex; flex-direction: column; gap: 12px; }}
        .btn {{
            display: block;
            width: 100%;
            padding: 16px 18px;
            border-radius: 14px;
            font-size: 16px;
            font-weight: 600;
            text-align: center;
            text-decoration: none;
            cursor: pointer;
            transition: transform 0.18s ease, background 0.25s ease, box-shadow 0.25s ease;
        }}
        .btn:active {{ transform: scale(0.98); }}
        .empty {{ text-align: center; color: var(--muted); padding: 22px 8px; font-size: 14px; }}
        .footer {{
            margin-top: 28px;
            text-align: center;
            font-size: 12px;
            color: var(--muted);
            opacity: 0.8;
        }}
    </style>
</head>
<body>
    <div class="wrap">
        <div class="avatar">{initial}</div>
        <h1>{title}</h1>
        {'<div class="bio">' + bio + '</div>' if bio else ''}
        <div class="card">
            <div class="links">
                {links_html}
            </div>
        </div>
        <div class="footer">مدعوم بواسطة LinkTree Bot</div>
    </div>
    <script>
        // تهيئة Telegram Web App
        try {{
            if (window.Telegram && window.Telegram.WebApp) {{
                window.Telegram.WebApp.ready();
                window.Telegram.WebApp.expand();
            }}
        }} catch (e) {{ /* لا شيء */ }}

        // تسجيل زيارة الصفحة
        try {{
            fetch("/api/track/{user_id}/visit", {{ method: "POST", keepalive: true }});
        }} catch (e) {{}}

        // تسجيل نقرات الروابط
        document.querySelectorAll("a.btn[data-link-id]").forEach(function(a) {{
            a.addEventListener("click", function() {{
                var lid = a.getAttribute("data-link-id");
                try {{
                    fetch("/api/track/{user_id}/click/" + lid, {{ method: "POST", keepalive: true }});
                }} catch (e) {{}}
            }});
        }});
    </script>
</body>
</html>
"""
    return html
