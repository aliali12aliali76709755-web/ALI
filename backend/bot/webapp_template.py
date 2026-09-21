"""
قالب صفحة الـ Web App - يبني HTML ديناميكياً بحسب المستخدم والقالب المختار
"""
from html import escape
from typing import List, Dict, Any
from bot.config import settings


THEME_STYLES = {
    0: """
        :root {
            --bg: #f5f5f7; --card: #ffffff; --text: #1c1c1e; --muted: #6b6b70;
            --btn-bg: #e5e5ea; --btn-bg-hover: #d1d1d6; --btn-text: #1c1c1e;
            --accent: #007aff; --shadow: 0 1px 3px rgba(0,0,0,0.06); --avatar-ring: #d1d1d6;
        }
        body { background: var(--bg); }
        .btn { background: var(--btn-bg); color: var(--btn-text); border: none; }
        .btn:hover { background: var(--btn-bg-hover); transform: translateY(-1px); }
    """,
    1: """
        :root {
            --bg: #05060a; --card: rgba(20, 22, 32, 0.7); --text: #e6faff; --muted: #7aa3b8;
            --btn-bg: linear-gradient(90deg, #0ff 0%, #7c3aed 100%);
            --btn-bg-hover: linear-gradient(90deg, #7c3aed 0%, #0ff 100%);
            --btn-text: #05060a; --accent: #00fff7; --shadow: 0 0 20px rgba(0, 255, 247, 0.25); --avatar-ring: #00fff7;
        }
        body { background: radial-gradient(1200px 600px at 20% 0%, rgba(0,255,247,0.15), transparent 60%),
              radial-gradient(900px 500px at 80% 100%, rgba(124,58,237,0.18), transparent 60%), #05060a; }
        .card { border: 1px solid rgba(0,255,247,0.15); }
        .btn { background: var(--btn-bg); color: var(--btn-text); font-weight: 700; box-shadow: var(--shadow); border: none; }
        .btn:hover { background: var(--btn-bg-hover); transform: translateY(-2px); }
        h1 { text-shadow: 0 0 12px rgba(0,255,247,0.5); }
    """,
    2: """
        :root {
            --bg: #150014; --card: rgba(45, 5, 45, 0.6); --text: #ffe6f7; --muted: #ff9ecf;
            --btn-bg: linear-gradient(135deg, #ff2fa0, #ff7ac3);
            --btn-bg-hover: linear-gradient(135deg, #ff7ac3, #ff2fa0);
            --btn-text: #ffffff; --accent: #ff2fa0; --shadow: 0 0 25px rgba(255, 47, 160, 0.45); --avatar-ring: #ff2fa0;
        }
        body { background: radial-gradient(1000px 500px at 50% 0%, rgba(255,47,160,0.25), transparent 60%),
              radial-gradient(800px 400px at 50% 100%, rgba(255,122,195,0.20), transparent 60%), #150014; }
        .card { border: 1px solid rgba(255, 47, 160, 0.25); }
        .btn { background: var(--btn-bg); color: var(--btn-text); font-weight: 700; box-shadow: var(--shadow); border: none; }
        .btn:hover { background: var(--btn-bg-hover); transform: translateY(-2px) scale(1.01); }
        h1 { text-shadow: 0 0 14px rgba(255,47,160,0.6); }
    """,
    3: """
        :root {
            --bg: #0b1220; --card: rgba(255,255,255,0.08); --text: #f4f7fb; --muted: #b7c3d6;
            --btn-bg: rgba(255,255,255,0.10); --btn-bg-hover: rgba(255,255,255,0.18); --btn-text: #ffffff;
            --accent: #8ab4ff; --shadow: 0 8px 32px rgba(0,0,0,0.28); --avatar-ring: rgba(255,255,255,0.35);
        }
        body { background: radial-gradient(900px 500px at 15% 10%, rgba(138,180,255,0.28), transparent 60%),
              radial-gradient(900px 500px at 85% 90%, rgba(180,120,255,0.22), transparent 60%),
              linear-gradient(180deg, #0b1220 0%, #101a2e 100%); }
        .card { background: var(--card); border: 1px solid rgba(255,255,255,0.14);
                backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px); }
        .btn { background: var(--btn-bg); color: var(--btn-text); border: 1px solid rgba(255,255,255,0.20); backdrop-filter: blur(12px); }
        .btn:hover { background: var(--btn-bg-hover); transform: translateY(-2px); }
    """,
    4: """
        :root {
            --bg: #001529; --card: rgba(0, 30, 60, 0.55); --text: #e0f7ff; --muted: #8cc7dd;
            --btn-bg: linear-gradient(135deg, #0077b6, #00b4d8, #90e0ef);
            --btn-bg-hover: linear-gradient(135deg, #90e0ef, #00b4d8, #0077b6);
            --btn-text: #001529; --accent: #00b4d8; --shadow: 0 6px 22px rgba(0, 180, 216, 0.35); --avatar-ring: #00b4d8;
        }
        body { background: radial-gradient(1000px 500px at 20% 10%, rgba(0,180,216,0.28), transparent 60%),
              radial-gradient(800px 500px at 80% 90%, rgba(3,4,94,0.55), transparent 60%),
              linear-gradient(180deg, #001529 0%, #023e58 100%); }
        .card { border: 1px solid rgba(0,180,216,0.25); }
        .btn { background: var(--btn-bg); color: var(--btn-text); font-weight: 700; box-shadow: var(--shadow); border: none; }
        .btn:hover { background: var(--btn-bg-hover); transform: translateY(-2px); }
    """,
    5: """
        :root {
            --bg: #1a0e1a; --card: rgba(60, 20, 40, 0.55); --text: #ffe9dc; --muted: #ffb28e;
            --btn-bg: linear-gradient(135deg, #ff9a3c, #ff5678, #a83279);
            --btn-bg-hover: linear-gradient(135deg, #a83279, #ff5678, #ff9a3c);
            --btn-text: #ffffff; --accent: #ff5678; --shadow: 0 6px 22px rgba(255, 86, 120, 0.35); --avatar-ring: #ff9a3c;
        }
        body { background: radial-gradient(1000px 500px at 20% 0%, rgba(255,154,60,0.35), transparent 60%),
              radial-gradient(900px 500px at 80% 100%, rgba(168,50,121,0.35), transparent 60%),
              linear-gradient(180deg, #1a0e1a 0%, #2b0f2b 100%); }
        .card { border: 1px solid rgba(255, 86, 120, 0.25); }
        .btn { background: var(--btn-bg); color: var(--btn-text); font-weight: 700; box-shadow: var(--shadow); border: none; }
        .btn:hover { background: var(--btn-bg-hover); transform: translateY(-2px) scale(1.02); }
        h1 { text-shadow: 0 0 12px rgba(255,86,120,0.55); }
    """,
    6: """
        :root {
            --bg: #06110d; --card: rgba(10, 40, 24, 0.55); --text: #e6ffe9; --muted: #98c9a3;
            --btn-bg: linear-gradient(135deg, #2d6a4f, #52b788, #b7e4c7);
            --btn-bg-hover: linear-gradient(135deg, #b7e4c7, #52b788, #2d6a4f);
            --btn-text: #06110d; --accent: #52b788; --shadow: 0 6px 22px rgba(82, 183, 136, 0.35); --avatar-ring: #52b788;
        }
        body { background: radial-gradient(1000px 500px at 20% 20%, rgba(82,183,136,0.28), transparent 60%),
              radial-gradient(900px 500px at 80% 100%, rgba(45,106,79,0.40), transparent 60%),
              linear-gradient(180deg, #06110d 0%, #08251a 100%); }
        .card { border: 1px solid rgba(82, 183, 136, 0.25); }
        .btn { background: var(--btn-bg); color: var(--btn-text); font-weight: 700; box-shadow: var(--shadow); border: none; }
        .btn:hover { background: var(--btn-bg-hover); transform: translateY(-2px); }
    """,
    # Premium: Royal Gold
    7: """
        :root {
            --bg: #0e0a02; --card: rgba(40, 28, 6, 0.6); --text: #fff6d5; --muted: #e6c66a;
            --btn-bg: linear-gradient(135deg, #d4af37, #ffdf6c, #b8860b);
            --btn-bg-hover: linear-gradient(135deg, #b8860b, #ffdf6c, #d4af37);
            --btn-text: #0e0a02; --accent: #ffdf6c; --shadow: 0 0 25px rgba(212, 175, 55, 0.55); --avatar-ring: #ffdf6c;
        }
        body { background: radial-gradient(1000px 500px at 30% 0%, rgba(212,175,55,0.35), transparent 60%),
              radial-gradient(900px 500px at 80% 100%, rgba(184,134,11,0.35), transparent 60%),
              linear-gradient(180deg, #0e0a02 0%, #1c1502 100%); }
        .card { border: 1px solid rgba(255,223,108,0.35); }
        .btn { background: var(--btn-bg); color: var(--btn-text); font-weight: 800; box-shadow: var(--shadow); border: none; letter-spacing: 0.3px; }
        .btn:hover { background: var(--btn-bg-hover); transform: translateY(-2px); }
        h1 { text-shadow: 0 0 16px rgba(212,175,55,0.6); background: linear-gradient(90deg,#d4af37,#ffdf6c); -webkit-background-clip: text; background-clip: text; color: transparent; }
    """,
    # Premium: Cyberpunk 2077
    8: """
        :root {
            --bg: #0a0016; --card: rgba(30, 0, 40, 0.65); --text: #f4faff; --muted: #ff41c8;
            --btn-bg: linear-gradient(90deg, #ff003c, #fcee0a, #00f0ff);
            --btn-bg-hover: linear-gradient(90deg, #00f0ff, #fcee0a, #ff003c);
            --btn-text: #0a0016; --accent: #fcee0a; --shadow: 0 0 30px rgba(252, 238, 10, 0.5); --avatar-ring: #fcee0a;
        }
        body { background: radial-gradient(900px 500px at 15% 0%, rgba(255,0,60,0.30), transparent 60%),
              radial-gradient(900px 500px at 85% 100%, rgba(0,240,255,0.30), transparent 60%),
              linear-gradient(180deg, #0a0016 0%, #14001f 100%); }
        .card { border: 1px solid rgba(252,238,10,0.35); }
        .btn { background: var(--btn-bg); color: var(--btn-text); font-weight: 800; box-shadow: var(--shadow); border: none; text-transform: uppercase; letter-spacing: 1px; }
        .btn:hover { background: var(--btn-bg-hover); transform: translateY(-2px) skewX(-2deg); }
        h1 { text-shadow: 0 0 10px #ff003c, 0 0 20px #00f0ff; }
    """,
    # Premium: Crystal Ice
    9: """
        :root {
            --bg: #041224; --card: rgba(200, 230, 255, 0.14); --text: #eaf7ff; --muted: #a9d6ff;
            --btn-bg: linear-gradient(135deg, rgba(255,255,255,0.35), rgba(120,200,255,0.35));
            --btn-bg-hover: linear-gradient(135deg, rgba(120,200,255,0.55), rgba(255,255,255,0.55));
            --btn-text: #041224; --accent: #a9d6ff; --shadow: 0 8px 32px rgba(120,200,255,0.35); --avatar-ring: #a9d6ff;
        }
        body { background: radial-gradient(900px 500px at 30% 20%, rgba(169,214,255,0.35), transparent 60%),
              radial-gradient(900px 500px at 80% 100%, rgba(255,255,255,0.15), transparent 60%),
              linear-gradient(180deg, #041224 0%, #08213d 100%); }
        .card { background: var(--card); border: 1px solid rgba(255,255,255,0.22);
                backdrop-filter: blur(30px); -webkit-backdrop-filter: blur(30px); }
        .btn { background: var(--btn-bg); color: var(--btn-text); font-weight: 700; box-shadow: var(--shadow);
               border: 1px solid rgba(255,255,255,0.35); backdrop-filter: blur(12px); }
        .btn:hover { background: var(--btn-bg-hover); transform: translateY(-2px); }
        h1 { text-shadow: 0 0 15px rgba(169,214,255,0.6); }
    """,
    # Premium: Cosmic Nebula
    10: """
        :root {
            --bg: #0b071a; --card: rgba(22, 11, 46, 0.6); --text: #f1ecff; --muted: #c8b6ff;
            --btn-bg: linear-gradient(135deg, #7b2cbf, #9d4edd, #e0aaff);
            --btn-bg-hover: linear-gradient(135deg, #e0aaff, #9d4edd, #7b2cbf);
            --btn-text: #0b071a; --accent: #e0aaff; --shadow: 0 0 25px rgba(157, 78, 221, 0.45); --avatar-ring: #e0aaff;
        }
        body { background: radial-gradient(1000px 500px at 20% 10%, rgba(123,44,191,0.30), transparent 60%),
              radial-gradient(900px 500px at 80% 90%, rgba(224,170,255,0.20), transparent 60%), #0b071a; }
        .card { border: 1px solid rgba(224,170,255,0.20); }
        .btn { background: var(--btn-bg); color: var(--btn-text); font-weight: 700; box-shadow: var(--shadow); border: none; }
        .btn:hover { background: var(--btn-bg-hover); transform: translateY(-2px); }
        h1 { text-shadow: 0 0 16px rgba(157,78,221,0.6); }
    """,
    # Premium: Obsidian Gold
    11: """
        :root {
            --bg: #0d0d0d; --card: rgba(26, 26, 26, 0.75); --text: #ffffff; --muted: #d4af37;
            --btn-bg: #1a1a1a; --btn-bg-hover: #262626;
            --btn-text: #ffffff; --accent: #d4af37; --shadow: 0 4px 20px rgba(0,0,0,0.5); --avatar-ring: #d4af37;
        }
        body { background: radial-gradient(1000px 500px at 50% 0%, rgba(212,175,55,0.15), transparent 65%), #0d0d0d; }
        .card { border: 1px solid rgba(212, 175, 55, 0.35); }
        .btn { background: var(--btn-bg); color: var(--btn-text); font-weight: 600; border: 1px solid #d4af37; transition: all 0.3s ease; }
        .btn:hover { background: var(--btn-bg-hover); color: #d4af37; box-shadow: 0 0 15px rgba(212,175,55,0.4); transform: translateY(-2px); }
        h1 { background: linear-gradient(90deg, #ffffff, #d4af37); -webkit-background-clip: text; background-clip: text; color: transparent; }
    """,
    # Premium: Emerald Aurora
    12: """
        :root {
            --bg: #020f12; --card: rgba(4, 30, 36, 0.6); --text: #e6fffa; --muted: #48cae4;
            --btn-bg: linear-gradient(135deg, #00f5d4, #00bbf9);
            --btn-bg-hover: linear-gradient(135deg, #00bbf9, #00f5d4);
            --btn-text: #020f12; --accent: #00f5d4; --shadow: 0 0 25px rgba(0, 245, 212, 0.45); --avatar-ring: #00f5d4;
        }
        body { background: radial-gradient(1000px 500px at 10% 20%, rgba(0,245,212,0.22), transparent 60%),
              radial-gradient(900px 500px at 90% 80%, rgba(0,187,249,0.25), transparent 60%), #020f12; }
        .card { border: 1px solid rgba(0,245,212,0.20); }
        .btn { background: var(--btn-bg); color: var(--btn-text); font-weight: 700; box-shadow: var(--shadow); border: none; }
        .btn:hover { background: var(--btn-bg-hover); transform: translateY(-2px); }
        h1 { text-shadow: 0 0 15px rgba(0,245,212,0.5); }
    """,
    # Premium: Vintage Espresso
    13: """
        :root {
            --bg: #1e130c; --card: rgba(60, 35, 23, 0.55); --text: #f5ebe0; --muted: #d5bdaf;
            --btn-bg: #d5bdaf; --btn-bg-hover: #e3d5ca;
            --btn-text: #1e130c; --accent: #e3d5ca; --shadow: 0 6px 15px rgba(0,0,0,0.25); --avatar-ring: #d5bdaf;
        }
        body { background: radial-gradient(1000px 500px at 50% 0%, rgba(213,189,175,0.25), transparent 60%),
              linear-gradient(180deg, #1e130c 0%, #321e12 100%); }
        .card { border: 1px solid rgba(213, 189, 175, 0.25); }
        .btn { background: var(--btn-bg); color: var(--btn-text); font-weight: 600; box-shadow: var(--shadow); border: none; }
        .btn:hover { background: var(--btn-bg-hover); transform: translateY(-2px); }
    """,
    # Premium: Aurora Wave
    14: """
        :root {
            --bg: #0b0f19; --card: rgba(13, 27, 42, 0.65); --text: #e0e1dd; --muted: #a5a5a5;
            --btn-bg: linear-gradient(135deg, #00f5d4 0%, #7b2cbf 100%);
            --btn-bg-hover: linear-gradient(135deg, #7b2cbf 0%, #00f5d4 100%);
            --btn-text: #ffffff; --accent: #00f5d4; --shadow: 0 8px 32px 0 rgba(0, 245, 212, 0.2); --avatar-ring: #00f5d4;
        }
        body { background: radial-gradient(circle at 50% 0%, rgba(123, 44, 191, 0.45), transparent 50%),
                    radial-gradient(circle at 100% 100%, rgba(0, 245, 212, 0.3), transparent 50%), #0b0f19; }
        .card { backdrop-filter: blur(12px); border: 1px solid rgba(0, 245, 212, 0.2); box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37); }
        .btn { background: var(--btn-bg); color: var(--btn-text); border: none; font-weight: 600; box-shadow: var(--shadow); }
        .btn:hover { background: var(--btn-bg-hover); transform: translateY(-2px) scale(1.02); box-shadow: 0 12px 40px 0 rgba(0, 245, 212, 0.35); }
        h1 { text-shadow: 0 0 20px rgba(0,245,212,0.6); }
    """,
    # Premium: Cyber Synth
    15: """
        :root {
            --bg: #1a0826; --card: rgba(36, 11, 54, 0.6); --text: #fbc5ff; --muted: #b18bb5;
            --btn-bg: #ff007f; --btn-bg-hover: #ff55aa; --btn-text: #ffffff; --accent: #00ffff;
            --shadow: 0 0 15px rgba(255, 0, 127, 0.5); --avatar-ring: #ff007f;
        }
        body { background: linear-gradient(180deg, #1a0826 0%, #0d0413 100%);
              background-image: radial-gradient(rgba(255, 0, 127, 0.15) 1px, transparent 0),
                                radial-gradient(rgba(0, 255, 255, 0.1) 1px, transparent 0);
              background-size: 40px 40px; background-position: 0 0, 20px 20px; }
        .card { border: 1px solid rgba(255, 0, 127, 0.3); box-shadow: 0 0 20px rgba(255, 0, 127, 0.2), inset 0 0 10px rgba(255, 0, 127, 0.1); backdrop-filter: blur(8px); }
        .btn { background: var(--btn-bg); color: var(--btn-text); border: 2px solid #00ffff; box-shadow: var(--shadow), 0 0 5px #00ffff; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }
        .btn:hover { background: var(--btn-bg-hover); box-shadow: 0 0 25px rgba(255, 0, 127, 0.8), 0 0 10px #00ffff; transform: translateY(-2px); }
        h1 { color: #fff; text-shadow: 0 0 5px #fff, 0 0 10px #ff007f, 0 0 20px #ff007f, 0 0 30px #ff007f; }
    """,
    # Premium: Bento 3D Grid
    16: """
        :root {
            --bg: #090a0f; --card: rgba(22, 27, 38, 0.7); --text: #f0f6fc; --muted: #8b949e;
            --btn-bg: rgba(33, 38, 45, 0.85); --btn-bg-hover: rgba(56, 139, 253, 0.15);
            --btn-text: #f0f6fc; --accent: #58a6ff; --shadow: 0 10px 30px rgba(0,0,0,0.5); --avatar-ring: #58a6ff;
        }
        body { background: radial-gradient(circle at 10% 20%, rgba(88, 166, 255, 0.15) 0%, transparent 40%),
                           radial-gradient(circle at 90% 80%, rgba(163, 113, 247, 0.15) 0%, transparent 40%), #090a0f; }
        .links { display: grid !important; grid-template-columns: repeat(2, 1fr) !important; gap: 14px !important; }
        .links a.btn:first-child { grid-column: span 2; padding: 20px 16px; background: linear-gradient(135deg, rgba(88,166,255,0.25), rgba(163,113,247,0.25)); border: 1px solid rgba(88,166,255,0.5); }
        .btn { flex-direction: column !important; padding: 18px 12px !important; min-height: 90px; justify-content: center !important; text-align: center; border: 1px solid rgba(240,246,252,0.12); backdrop-filter: blur(12px); border-radius: 18px !important; transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important; }
        .btn:hover { transform: translateY(-4px) scale(1.02); border-color: var(--accent); box-shadow: 0 10px 25px rgba(88,166,255,0.25); }
        .btn .icon { font-size: 26px !important; margin-bottom: 6px; }
        .btn .btn-title { font-size: 14px !important; font-weight: 700; }
    """,
    # Elite Creator Theme 17: Studio Minimalist
    17: """
        :root {
            --bg: #0d0e12; --card: rgba(22, 25, 32, 0.85); --text: #f3f4f6; --muted: #9ca3af;
            --btn-bg: #1f232b; --btn-bg-hover: #2a303c; --btn-text: #ffffff;
            --accent: #e5e7eb; --shadow: 0 4px 20px rgba(0,0,0,0.35); --avatar-ring: rgba(255,255,255,0.15);
        }
        body { background: #0d0e12; }
        .card { border: 1px solid rgba(255,255,255,0.08); backdrop-filter: blur(20px); border-radius: 24px; }
        .btn { border: 1px solid rgba(255,255,255,0.10); border-radius: 16px; font-weight: 600; }
        .btn:hover { border-color: rgba(255,255,255,0.3); transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.4); }
    """,
    # Elite Creator Theme 18: Editorial Luxury
    18: """
        :root {
            --bg: #121110; --card: rgba(28, 26, 24, 0.85); --text: #f7f4ed; --muted: #b8b0a2;
            --btn-bg: rgba(214, 198, 175, 0.08); --btn-bg-hover: rgba(214, 198, 175, 0.16);
            --btn-text: #f7f4ed; --accent: #d6c6af; --shadow: 0 8px 30px rgba(0,0,0,0.4); --avatar-ring: #d6c6af;
        }
        body { background: #121110; }
        .card { border: 1px solid rgba(214, 198, 175, 0.20); border-radius: 20px; backdrop-filter: blur(16px); }
        .btn { border: 1px solid rgba(214, 198, 175, 0.25); border-radius: 12px; }
        .btn:hover { border-color: #d6c6af; transform: translateY(-2px); }
    """,
    # Elite Creator Theme 19: Titanium Stealth
    19: """
        :root {
            --bg: #16181d; --card: rgba(30, 34, 42, 0.85); --text: #e6edf3; --muted: #8b949e;
            --btn-bg: #21262d; --btn-bg-hover: #30363d; --btn-text: #f0f6fc;
            --accent: #58a6ff; --shadow: 0 8px 24px rgba(0,0,0,0.45); --avatar-ring: rgba(240,246,252,0.2);
        }
        body { background: linear-gradient(180deg, #16181d 0%, #0d1117 100%); }
        .card { border: 1px solid rgba(240,246,252,0.12); border-radius: 20px; }
        .btn { border: 1px solid rgba(240,246,252,0.14); border-radius: 14px; }
        .btn:hover { border-color: #58a6ff; transform: translateY(-2px); }
    """,
    # Elite Creator Theme 20: Studio Pure White
    20: """
        :root {
            --bg: #f8fafc; --card: #ffffff; --text: #0f172a; --muted: #64748b;
            --btn-bg: #f1f5f9; --btn-bg-hover: #e2e8f0; --btn-text: #0f172a;
            --accent: #0f172a; --shadow: 0 4px 20px rgba(0,0,0,0.06); --avatar-ring: #e2e8f0;
        }
        body { background: #f8fafc; }
        .card { border: 1px solid #e2e8f0; border-radius: 24px; }
        .btn { border: 1px solid #e2e8f0; border-radius: 16px; font-weight: 600; }
        .btn:hover { background: #e2e8f0; transform: translateY(-2px); box-shadow: 0 6px 16px rgba(0,0,0,0.08); }
    """,
    # Influencer Theme 21: SuperProfile Crimson
    21: """
        :root {
            --bg: #0d0203; --card: transparent; --text: #ffffff; --muted: #d1d5db;
            --btn-bg: #ffffff; --btn-bg-hover: #f3f4f6; --btn-text: #000000;
            --accent: #e50914; --shadow: 0 8px 25px rgba(0,0,0,0.6); --avatar-ring: #e50914;
        }
        body {
            background: radial-gradient(circle at 50% 20%, #3b050a 0%, #0d0203 70%),
                        repeating-linear-gradient(135deg, rgba(229, 9, 20, 0.05) 0px, rgba(229, 9, 20, 0.05) 30px, transparent 30px, transparent 60px);
            background-attachment: fixed;
        }
        .card { background: transparent; box-shadow: none; padding: 0; }
        .btn {
            background: #ffffff !important; color: #000000 !important;
            border-radius: 30px !important; padding: 14px 20px !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3); font-weight: 700;
            border: 1px solid rgba(255,255,255,0.8) !important;
        }
        .btn:hover { transform: translateY(-3px) scale(1.01); box-shadow: 0 8px 25px rgba(229,9,20,0.4); }
        .social-icons-bar a { background: #ffffff; color: #000000; }
    """,
    # Influencer Theme 22: Kaizen Minimal
    22: """
        :root {
            --bg: #f5f6f8; --card: transparent; --text: #191c1f; --muted: #6c757d;
            --btn-bg: #ffffff; --btn-bg-hover: #f8f9fa; --btn-text: #191c1f;
            --accent: #191c1f; --shadow: 0 2px 8px rgba(0,0,0,0.04); --avatar-ring: #ffffff;
        }
        body { background: #f5f6f8; }
        .card { background: transparent; box-shadow: none; padding: 0; }
        .btn {
            background: #ffffff !important; color: #191c1f !important;
            border-radius: 16px !important; border: 1px solid rgba(0,0,0,0.06) !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.03);
        }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(0,0,0,0.07); }
        .social-icons-bar a { background: #ffffff; color: #191c1f; border: 1px solid rgba(0,0,0,0.06); }
    """,
    # Influencer Theme 23: Academy Soft Pastel
    23: """
        :root {
            --bg: #7db3db; --card: rgba(255, 255, 255, 0.45); --text: #0e3046; --muted: #3d5e75;
            --btn-bg: rgba(255, 255, 255, 0.7); --btn-bg-hover: rgba(255, 255, 255, 0.9);
            --btn-text: #0e3046; --accent: #25D366; --shadow: 0 4px 20px rgba(0,0,0,0.06); --avatar-ring: #ffffff;
        }
        body {
            background: linear-gradient(180deg, #7db3db 0%, #a2c8cc 40%, #c4dbcd 70%, #d8e5d0 100%);
            background-attachment: fixed;
        }
        .card { backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); border: 1px solid rgba(255,255,255,0.4); }
        .btn {
            background: rgba(255,255,255,0.75) !important; color: #0e3046 !important;
            border-radius: 14px !important; border: 1px solid rgba(255,255,255,0.8) !important;
            backdrop-filter: blur(10px);
        }
        .btn:hover { background: rgba(255,255,255,0.95) !important; transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0,0,0,0.08); }
        .social-icons-bar a { background: rgba(255,255,255,0.8); color: #0e3046; }
    """,
    # Theme 24: Telegram Emerald (exact match to user Image 1)
    24: """
        :root {
            --bg: #558740; --card: rgba(255, 255, 255, 0.94); --text: #1a3311; --muted: #4a683e;
            --btn-bg: #ffffff; --btn-bg-hover: #f0f7ec; --btn-text: #2d5a1e;
            --accent: #25D366; --shadow: 0 4px 18px rgba(0,0,0,0.08); --avatar-ring: #ffffff;
        }
        body {
            background-color: #558740;
            background-image: 
                radial-gradient(1000px 600px at 50% 10%, rgba(132, 189, 100, 0.35), transparent 70%),
                radial-gradient(800px 500px at 50% 90%, rgba(55, 95, 38, 0.45), transparent 70%),
                url("data:image/svg+xml,%3Csvg%20xmlns%3D%27http%3A//www.w3.org/2000/svg%27%20width%3D%27140%27%20height%3D%27140%27%20viewBox%3D%270%200%20140%20140%27%3E%3Cg%20fill%3D%27none%27%20stroke%3D%27white%27%20stroke-width%3D%271.5%27%20stroke-opacity%3D%270.18%27%20stroke-linecap%3D%27round%27%20stroke-linejoin%3D%27round%27%3E%3Cpath%20d%3D%27M15%2035L45%2015L28%2050L24%2038L38%2025L23%2036Z%27/%3E%3Cpath%20d%3D%27M75%2018c-5%200-9%203-9%208%200%203%202%206%206%207l-2%206%206-3c2%200%204-1%205-2%203-2%206-5%206-8%200-5-6-8-12-8z%27/%3E%3Cpolygon%20points%3D%27115%2C18%20117%2C24%20123%2C24%20118%2C28%20120%2C34%20115%2C30%20110%2C34%20112%2C28%20107%2C24%20113%2C24%27/%3E%3Cpath%20d%3D%27M20%2085h16v12c0%204-4%208-8%208s-8-4-8-8zM36%2089h4c2%200%203%201%203%203s-1%203-3%203h-4%27/%3E%3Cpath%20d%3D%27M75%2088c-4-8-16-4-16%206%200%208%2016%2018%2016%2018s16-10%2016-18c0-10-12-14-16-6z%27/%3E%3Crect%20x%3D%27100%27%20y%3D%2785%27%20width%3D%2726%27%20height%3D%2716%27%20rx%3D%275%27/%3E%3Ccircle%20cx%3D%27106%27%20cy%3D%2793%27%20r%3D%271.5%27/%3E%3Ccircle%20cx%3D%27120%27%20cy%3D%2793%27%20r%3D%271.5%27/%3E%3C/g%3E%3C/svg%3E");
            background-size: auto, auto, 140px 140px;
            background-attachment: fixed;
        }
        .card { background: rgba(255, 255, 255, 0.95); border: 1px solid rgba(255, 255, 255, 0.9); box-shadow: 0 8px 30px rgba(0,0,0,0.1); }
        .btn {
            background: #ffffff !important; color: #1e3f14 !important;
            border-radius: 18px !important; border: 1px solid rgba(255,255,255,0.7) !important;
            box-shadow: 0 4px 14px rgba(0,0,0,0.06); font-weight: 700;
        }
        .btn:hover { background: #f3faf0 !important; transform: translateY(-2px); box-shadow: 0 8px 22px rgba(0,0,0,0.12); }
        .social-icons-bar a { background: #ffffff; color: #1e3f14; border: 1px solid rgba(255,255,255,0.8); }
    """,
    # Theme 25: Cyan Mesh Glow (exact match to user Image 2)
    25: """
        :root {
            --bg: #0077b6; --card: rgba(255, 255, 255, 0.18); --text: #ffffff; --muted: #d0f0fd;
            --btn-bg: rgba(255, 255, 255, 0.25); --btn-bg-hover: rgba(255, 255, 255, 0.4);
            --btn-text: #ffffff; --accent: #00f0ff; --shadow: 0 8px 32px rgba(0, 50, 100, 0.25); --avatar-ring: #00f0ff;
        }
        body {
            background-color: #03045e;
            background-image: 
                radial-gradient(at 10% 15%, #00b4d8 0px, transparent 65%),
                radial-gradient(at 90% 85%, #0077b6 0px, transparent 60%),
                radial-gradient(at 50% 50%, #48cae4 0px, transparent 55%),
                radial-gradient(at 80% 10%, #90e0ef 0px, transparent 50%),
                linear-gradient(180deg, #0096c7 0%, #03045e 100%);
            background-attachment: fixed;
        }
        .card {
            background: rgba(255, 255, 255, 0.16);
            backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px);
            border: 1px solid rgba(255, 255, 255, 0.35);
            box-shadow: 0 10px 40px rgba(0, 20, 60, 0.2);
        }
        .btn {
            background: rgba(255, 255, 255, 0.22) !important; color: #ffffff !important;
            border-radius: 20px !important; border: 1px solid rgba(255, 255, 255, 0.4) !important;
            backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1); font-weight: 700;
        }
        .btn:hover {
            background: rgba(255, 255, 255, 0.35) !important;
            transform: translateY(-3px) scale(1.01);
            box-shadow: 0 10px 30px rgba(0, 240, 255, 0.3);
        }
        .social-icons-bar a { background: rgba(255, 255, 255, 0.25); color: #ffffff; border: 1px solid rgba(255, 255, 255, 0.4); }
    """,
    # Theme 26: Sunset Coral Mesh
    26: """
        :root {
            --bg: #ff6b6b; --card: rgba(255, 255, 255, 0.2); --text: #ffffff; --muted: #ffe3e3;
            --btn-bg: rgba(255, 255, 255, 0.88); --btn-bg-hover: #ffffff;
            --btn-text: #b82d38; --accent: #ffd166; --shadow: 0 8px 30px rgba(180, 40, 60, 0.25); --avatar-ring: #ffd166;
        }
        body {
            background: 
                radial-gradient(at 15% 20%, #ff9a8b 0%, transparent 60%),
                radial-gradient(at 85% 30%, #ff6a88 0%, transparent 60%),
                radial-gradient(at 50% 80%, #a18cd1 0%, transparent 65%),
                linear-gradient(135deg, #f7797d 0%, #FBD786 50%, #C6FFDD 100%);
            background-attachment: fixed;
        }
        .card { backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.4); }
        .btn {
            background: rgba(255, 255, 255, 0.9) !important; color: #a12330 !important;
            border-radius: 16px !important; font-weight: 700;
            box-shadow: 0 4px 18px rgba(0,0,0,0.12);
        }
        .btn:hover { background: #ffffff !important; transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,0.18); }
    """,
    # Theme 27: Velvet Nebula
    27: """
        :root {
            --bg: #0f0c29; --card: rgba(36, 20, 64, 0.6); --text: #f3e8ff; --muted: #c084fc;
            --btn-bg: linear-gradient(135deg, #7928ca, #ff0080);
            --btn-bg-hover: linear-gradient(135deg, #ff0080, #7928ca);
            --btn-text: #ffffff; --accent: #e879f9; --shadow: 0 8px 30px rgba(121, 40, 202, 0.35); --avatar-ring: #e879f9;
        }
        body {
            background: 
                radial-gradient(at 20% 20%, rgba(121, 40, 202, 0.45) 0%, transparent 60%),
                radial-gradient(at 80% 80%, rgba(255, 0, 128, 0.35) 0%, transparent 60%),
                linear-gradient(180deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            background-attachment: fixed;
        }
        .card { border: 1px solid rgba(216, 180, 254, 0.25); backdrop-filter: blur(20px); }
        .btn { background: var(--btn-bg); color: #ffffff !important; border-radius: 16px !important; font-weight: 700; box-shadow: var(--shadow); }
        .btn:hover { background: var(--btn-bg-hover); transform: translateY(-2px); }
    """,
    # Theme 28: Arabian Arabesque
    28: """
        :root {
            --bg: #081c15; --card: rgba(13, 43, 33, 0.75); --text: #e6fcf5; --muted: #d4af37;
            --btn-bg: linear-gradient(135deg, #1b4332, #2d6a4f);
            --btn-bg-hover: linear-gradient(135deg, #2d6a4f, #1b4332);
            --btn-text: #f3eed9; --accent: #d4af37; --shadow: 0 8px 30px rgba(0,0,0,0.35); --avatar-ring: #d4af37;
        }
        body {
            background-color: #081c15;
            background-image: 
                radial-gradient(1000px 500px at 50% 10%, rgba(212, 175, 55, 0.15), transparent 70%),
                url("data:image/svg+xml,%3Csvg%20xmlns%3D%27http%3A//www.w3.org/2000/svg%27%20width%3D%27100%27%20height%3D%27100%27%20viewBox%3D%270%200%20100%20100%27%3E%3Cg%20fill%3D%27none%27%20stroke%3D%27%23d4af37%27%20stroke-width%3D%271%27%20stroke-opacity%3D%270.18%27%3E%3Crect%20x%3D%2730%27%20y%3D%2730%27%20width%3D%2740%27%20height%3D%2740%27%20transform%3D%27rotate(45%2050%2050)%27/%3E%3Crect%20x%3D%2730%27%20y%3D%2730%27%20width%3D%2740%27%20height%3D%2740%27/%3E%3Cpath%20d%3D%27M0%2050L50%200M50%20100L100%2050M0%2050L50%20100M50%200L100%2050%27/%3E%3C/g%3E%3C/svg%3E");
            background-size: auto, 100px 100px;
            background-attachment: fixed;
        }
        .card { border: 1px solid rgba(212, 175, 55, 0.3); box-shadow: 0 10px 30px rgba(0,0,0,0.4); }
        .btn {
            background: rgba(27, 67, 50, 0.8) !important; color: #fdfaf0 !important;
            border-radius: 14px !important; border: 1px solid rgba(212, 175, 55, 0.4) !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.25);
        }
        .btn:hover { background: rgba(45, 106, 79, 0.95) !important; border-color: #d4af37 !important; transform: translateY(-2px); }
    """,
    # Theme 29: Esports Cyber
    29: """
        :root {
            --bg: #090a0f; --card: rgba(18, 20, 29, 0.85); --text: #ffffff; --muted: #8b9bb4;
            --btn-bg: #131722; --btn-bg-hover: #1c2233; --btn-text: #00ffcc;
            --accent: #ff0055; --shadow: 0 8px 30px rgba(255, 0, 85, 0.2); --avatar-ring: #00ffcc;
        }
        body {
            background-color: #090a0f;
            background-image: 
                radial-gradient(at 10% 10%, rgba(255, 0, 85, 0.2) 0%, transparent 50%),
                radial-gradient(at 90% 90%, rgba(0, 255, 204, 0.2) 0%, transparent 50%),
                repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.5) 2px, rgba(0,0,0,0.5) 4px);
            background-attachment: fixed;
        }
        .card { border: 1px solid rgba(255, 0, 85, 0.3); border-radius: 16px; }
        .btn {
            background: #131722 !important; color: #00ffcc !important;
            border-radius: 8px !important; border: 1px solid rgba(0, 255, 204, 0.3) !important;
            font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;
        }
        .btn:hover { border-color: #ff0055 !important; color: #ffffff !important; transform: translateY(-2px); box-shadow: 0 6px 20px rgba(255, 0, 85, 0.35); }
    """,
    # Theme 30: Pastel Mint
    30: """
        :root {
            --bg: #e8f5e9; --card: rgba(255, 255, 255, 0.7); --text: #1b4332; --muted: #52796f;
            --btn-bg: #ffffff; --btn-bg-hover: #f1f8f5; --btn-text: #1b4332;
            --accent: #2d6a4f; --shadow: 0 4px 20px rgba(0,0,0,0.04); --avatar-ring: #b7e4c7;
        }
        body {
            background: linear-gradient(135deg, #d8f3dc 0%, #b7e4c7 50%, #95d5b2 100%);
            background-attachment: fixed;
        }
        .card { backdrop-filter: blur(14px); border: 1px solid rgba(255,255,255,0.6); }
        .btn {
            background: #ffffff !important; color: #1b4332 !important;
            border-radius: 20px !important; border: 1px solid rgba(255,255,255,0.9) !important;
            font-weight: 700; box-shadow: 0 3px 12px rgba(0,0,0,0.04);
        }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 6px 18px rgba(0,0,0,0.08); }
    """,
}

FONT_MAP = {
    "Tajawal": "'Tajawal', -apple-system, BlinkMacSystemFont, sans-serif",
    "Cairo": "'Cairo', -apple-system, BlinkMacSystemFont, sans-serif",
    "Almarai": "'Almarai', -apple-system, BlinkMacSystemFont, sans-serif",
    "Readex Pro": "'Readex Pro', -apple-system, BlinkMacSystemFont, sans-serif",
    "Amiri": "'Amiri', Georgia, serif",
    "IBM Plex Sans Arabic": "'IBM Plex Sans Arabic', -apple-system, BlinkMacSystemFont, sans-serif",
}

SOCIAL_ICONS_SVG = {
    "instagram": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line></svg>',
    "tiktok": '<svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64c.298-.002.595.042.88.13V9.4a6.33 6.33 0 0 0-1-.08A6.34 6.34 0 0 0 3 15.66a6.34 6.34 0 0 0 10.81 4.48 6.27 6.27 0 0 0 1.86-4.48V8.71a8.16 8.16 0 0 0 4.89 1.62V6.89a4.85 4.85 0 0 1-.97-.2z"/></svg>',
    "youtube": '<svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>',
    "x": '<svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>',
    "snapchat": '<svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><path d="M12.007 2c-3.754 0-6.184 2.453-6.22 5.566-.02 1.64.636 2.87 1.054 3.486.113.167.147.28.093.385-.067.13-.25.212-.59.273-.695.125-1.572.493-1.637 1.252-.036.425.263.81.93 1.196.22.127.356.24.356.37 0 .167-.294.398-.797.778-.71.536-1.528 1.155-1.528 2.13 0 1.285 1.295 1.764 2.378 2.01.21.047.38.087.485.127.184.072.268.225.264.478-.01.62-.224 1.344-.658 1.73-.243.216-.48.272-.724.33-.298.07-.63.15-.815.344-.145.153-.162.355-.045.547.202.33 1.052.548 2.057.548.514 0 1.043-.058 1.545-.17.755-.17 1.534-.51 2.37-.872.93-.404 1.837-.798 2.762-.798.93 0 1.83.394 2.76.798.835.362 1.614.702 2.37.872.5.112 1.03.17 1.544.17 1.006 0 1.856-.218 2.058-.548.117-.192.1-.394-.045-.547-.186-.194-.518-.274-.816-.344-.243-.058-.48-.114-.723-.33-.434-.386-.648-1.11-.658-1.73-.004-.253.08-.406.264-.478.106-.04.275-.08.485-.127 1.083-.246 2.378-.725 2.378-2.01 0-.975-.818-1.594-1.528-2.13-.503-.38-.797-.61-.797-.778 0-.13.136-.243.356-.37.667-.386.966-.77.93-1.196-.065-.759-.942-1.127-1.637-1.252-.34-.06-.523-.143-.59-.273-.054-.105-.02-.218.093-.385.418-.616 1.074-1.846 1.054-3.486-.036-3.113-2.466-5.566-6.22-5.566z"/></svg>',
    "telegram": '<svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.446 1.394c-.16.16-.295.295-.605.295l.213-3.053 5.56-5.023c.242-.213-.054-.333-.373-.121l-6.871 4.326-2.962-.924c-.643-.204-.657-.643.136-.953l11.57-4.461c.537-.197 1.006.128.832.942z"/></svg>',
    "facebook": '<svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>',
    "whatsapp": '<svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><path d="M12.04 2c-5.46 0-9.91 4.45-9.91 9.91 0 1.75.46 3.45 1.32 4.95L2.05 22l5.25-1.38c1.45.79 3.08 1.21 4.74 1.21 5.46 0 9.91-4.45 9.91-9.91 0-2.65-1.03-5.14-2.9-7.01A9.816 9.816 0 0 0 12.04 2zm.01 1.67c2.2 0 4.26.86 5.82 2.42a8.225 8.225 0 0 1 2.41 5.83c0 4.54-3.7 8.24-8.24 8.24-1.48 0-2.93-.4-4.2-1.15l-.3-.18-3.12.82.83-3.04-.2-.31a8.196 8.196 0 0 1-1.26-4.38c0-4.54 3.7-8.24 8.24-8.24zm4.52 11.66c-.25.7-.99 1.28-1.74 1.44-.51.11-1.18.2-3.42-.73-2.87-1.19-4.71-4.12-4.85-4.31-.14-.19-1.17-1.56-1.17-2.97 0-1.41.74-2.11 1-2.4.26-.29.58-.36.77-.36.19 0 .38 0 .55.01.18.01.42-.07.66.5.25.59.85 2.08.92 2.23.08.15.13.33.03.53-.1.2-.15.33-.3.51-.15.18-.32.4-.46.54-.15.15-.31.31-.13.62.18.31.8 1.32 1.72 2.13 1.18 1.05 2.18 1.37 2.49 1.52.31.15.49.13.67-.08.18-.21.77-.9 1-.21.23-.31.46-.26.77-.15.31.1.98.96 2.32 1.62.34.17.58.26.66.39.08.13.08.76-.17 1.46z"/></svg>',
    "linkedin": '<svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/></svg>',
    "discord": '<svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994.021-.041.001-.09-.041-.106a13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.929 1.793 8.18 1.793 12.061 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.894.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.028zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/></svg>'
}


PLATFORM_ICONS = {
    "youtube.com": "▶️", "youtu.be": "▶️",
    "instagram.com": "📸",
    "twitter.com": "🐦", "x.com": "🐦",
    "tiktok.com": "🎵",
    "facebook.com": "👥", "fb.com": "👥",
    "t.me": "✈️", "telegram.me": "✈️", "telegram.org": "✈️",
    "whatsapp.com": "💬", "wa.me": "💬",
    "linkedin.com": "💼",
    "github.com": "💻",
    "spotify.com": "🎧",
    "snapchat.com": "👻",
    "twitch.tv": "🎮",
    "discord.gg": "🎮", "discord.com": "🎮",
    "soundcloud.com": "🎵",
    "medium.com": "✍️",
    "pinterest.com": "📌",
    "reddit.com": "🤖",
    "mailto:": "📧",
}


def detect_icon(url: str) -> str:
    low = url.lower()
    if low.startswith("mailto:"):
        return "📧"
    for key, icon in PLATFORM_ICONS.items():
        if key in low:
            return icon
    return "🔗"


def get_verified_badge_html(badge_type: str) -> str:
    badge_type = badge_type or "blue"
    if badge_type == "gold_vip":
        return (
            '<span class="verified badge-gold" title="حساب VIP ملكي">'
            '<svg width="22" height="22" viewBox="0 0 24 24" fill="none">'
            '<path d="M5 16L3 5l5.5 5L12 4l3.5 6L21 5l-2 11H5zm14 3c0 .6-.4 1-1 1H6c-.6 0-1-.4-1-1v-1h14v1z" fill="url(#gold-grad)"/>'
            '<defs><linearGradient id="gold-grad" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#FFE259"/><stop offset="100%" stop-color="#FFA751"/></linearGradient></defs>'
            '</svg></span>'
        )
    elif badge_type == "diamond":
        return (
            '<span class="verified badge-diamond" title="حساب ألماسي نخبوي">'
            '<svg width="22" height="22" viewBox="0 0 24 24" fill="none">'
            '<path d="M12 2L2 9l10 13 10-13-10-7zm0 3.2L18.4 9 12 17.5 5.6 9 12 5.2z" fill="url(#diam-grad)"/>'
            '<defs><linearGradient id="diam-grad" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#00f2fe"/><stop offset="100%" stop-color="#4facfe"/></linearGradient></defs>'
            '</svg></span>'
        )
    elif badge_type == "creator":
        return (
            '<span class="verified badge-creator" title="صانع محتوى موثق">'
            '<svg width="22" height="22" viewBox="0 0 24 24" fill="none">'
            '<circle cx="12" cy="12" r="10" fill="url(#creator-grad)"/>'
            '<path d="M12 6l1.8 3.6 4 .6-2.9 2.8.7 4-3.6-1.9-3.6 1.9.7-4-2.9-2.8 4-.6L12 6z" fill="#fff"/>'
            '<defs><linearGradient id="creator-grad" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#f857a6"/><stop offset="100%" stop-color="#ff5858"/></linearGradient></defs>'
            '</svg></span>'
        )
    elif badge_type == "star":
        return (
            '<span class="verified badge-star" title="حساب بنجمة ذهبية">'
            '<svg width="22" height="22" viewBox="0 0 24 24" fill="none">'
            '<path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" fill="url(#star-grad)"/>'
            '<defs><linearGradient id="star-grad" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#FFE259"/><stop offset="100%" stop-color="#FFA751"/></linearGradient></defs>'
            '</svg></span>'
        )
    else:  # blue official
        return (
            '<span class="verified badge-blue" title="حساب رسمي موثّق">'
            '<svg width="20" height="20" viewBox="0 0 24 24" fill="none">'
            '<path d="M12 1l2.39 2.39L18 2l1.61 3.61L23 7l-1.39 3.39L23 14l-3.39 1.61'
            ' L18 19l-3.61-1.39L12 20l-2.39-2.39L6 19l-1.61-3.61L1 14l1.39-3.39L1 7l3.61-1.61'
            ' L6 2l3.61 1.39L12 1z" fill="#1DA1F2"/>'
            '<path d="M9.5 12.5l2 2 4-4" stroke="#fff" stroke-width="2" '
            'stroke-linecap="round" stroke-linejoin="round"/></svg></span>'
        )


def render_page(user: Dict[str, Any], links: List[Dict[str, Any]], reviews: List[Dict[str, Any]] = None) -> str:
    theme = user.get("theme") or 0
    if theme not in THEME_STYLES:
        theme = 0
    theme_css = THEME_STYLES[theme]

    is_vip = True
    
    # Customization override for VIP users
    custom_css = ""
    if is_vip:
        accent_color = user.get("accent_color")
        if accent_color:
            custom_css += f"\n        :root {{ --accent: {accent_color} !important; }}\n"
            if theme in (0, 3):
                custom_css += f"        .btn {{ border-color: {accent_color} !important; }}\n"
        
        button_style = user.get("button_style") or "rounded"
        radius_map = {
            "rounded": "12px",
            "pill": "30px",
            "square": "0px",
            "tab": "6px"
        }
        radius = radius_map.get(button_style, "12px")
        custom_css += f"        .btn {{ border-radius: {radius} !important; }}\n"
        
    theme_css = theme_css + custom_css

    title = escape(user.get("page_title") or user.get("full_name") or "صفحتي")
    bio = escape(user.get("page_bio") or "")
    user_id = int(user["user_id"])
    initial = (title[:1] or "?").upper()
    has_avatar = bool(user.get("avatar_path"))
    bg_effect = user.get("bg_effect") or "none"
    badge_type = user.get("badge_type") or "blue"
    music_url = user.get("music_url")
    music_title = escape(user.get("music_title") or "المقطع الصوتي")
    marquee_text = user.get("marquee_text")
    marquee_url = user.get("marquee_url")
    font_name = user.get("font_family") or "Tajawal"
    font_stack = FONT_MAP.get(font_name, FONT_MAP["Tajawal"])
    
    # Marketing Pixels
    meta_pixel = user.get("meta_pixel")
    tiktok_pixel = user.get("tiktok_pixel")
    ga_pixel = user.get("ga_pixel")

    # Countdown Timer
    countdown_title = escape(user.get("countdown_title") or "ينتهي العرض الخاص خلال:")
    countdown_target = user.get("countdown_target")

    verified_badge = ""
    show_badge = user.get("show_badge") if user.get("show_badge") is not None else 1
    if is_vip and bool(show_badge):
        verified_badge = get_verified_badge_html(badge_type)

    if has_avatar:
        avatar_html = f'<img class="avatar avatar-img" src="/api/avatar/{user_id}" alt="avatar">'
    else:
        avatar_html = f'<div class="avatar">{initial}</div>'

    # Marquee Announcement Bar (Clickable if URL present)
    marquee_html = ""
    if marquee_text:
        escaped_mq = escape(marquee_text)
        if marquee_url:
            marquee_html = f"""
            <a class="marquee-bar is-link" href="{escape(marquee_url, quote=True)}" target="_blank" rel="noopener">
                <span class="marquee-tag">📢 إعلان</span>
                <div class="marquee-track">
                    <div class="marquee-content">
                        <span>{escaped_mq}</span>
                        <span class="mq-dot">✦</span>
                        <span>{escaped_mq}</span>
                        <span class="mq-dot">✦</span>
                    </div>
                </div>
                <span class="mq-arrow">➜</span>
            </a>
            """
        else:
            marquee_html = f"""
            <div class="marquee-bar">
                <span class="marquee-tag">📢 إعلان</span>
                <div class="marquee-track">
                    <div class="marquee-content">
                        <span>{escaped_mq}</span>
                        <span class="mq-dot">✦</span>
                        <span>{escaped_mq}</span>
                        <span class="mq-dot">✦</span>
                    </div>
                </div>
            </div>
            """

    # Countdown Timer Widget
    countdown_html = ""
    if countdown_target:
        countdown_html = f"""
        <div class="countdown-widget" id="countdownWidget" data-target="{escape(countdown_target, quote=True)}">
            <div class="countdown-head">
                <span class="cd-pulse">⏳</span>
                <strong>{countdown_title}</strong>
            </div>
            <div class="countdown-grid">
                <div class="cd-box"><span class="cd-num" id="cdDays">00</span><span class="cd-lbl">يوم</span></div>
                <div class="cd-sep">:</div>
                <div class="cd-box"><span class="cd-num" id="cdHours">00</span><span class="cd-lbl">ساعة</span></div>
                <div class="cd-sep">:</div>
                <div class="cd-box"><span class="cd-num" id="cdMins">00</span><span class="cd-lbl">دقيقة</span></div>
                <div class="cd-sep">:</div>
                <div class="cd-box"><span class="cd-num" id="cdSecs">00</span><span class="cd-lbl">ثانية</span></div>
            </div>
        </div>
        """

    # Pixels Snippets in <head>
    pixels_head_scripts = []
    if meta_pixel:
        pixels_head_scripts.append(f"""
        <!-- Meta Pixel Code -->
        <script>
        !function(f,b,e,v,n,t,s){{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?
        n.callMethod.apply(n,arguments):n.queue.push(arguments)}};if(!f._fbq)f._fbq=n;
        n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;
        t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}}(window,
        document,'script','https://connect.facebook.net/en_US/fbevents.js');
        fbq('init', '{escape(meta_pixel)}');
        fbq('track', 'PageView');
        </script>
        """)
    if tiktok_pixel:
        pixels_head_scripts.append(f"""
        <!-- TikTok Pixel Code -->
        <script>
        !function (w, d, t) {{
            w.TiktokAnalyticsObject=t;var ttq=w[t]=w[t]||[];ttq.methods=["page","track","identify","instances","debug","on","off","once","ready","alias","group","enableCookie","disableCookie"],ttq.setAndDefer=function(t,e){{t[e]=function(){{t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}}};for(var i=0;i<ttq.methods.length;i++)ttq.setAndDefer(ttq,ttq.methods[i]);ttq.instance=function(t){{for(var e=ttq._i[t]||[],n=0;n<ttq.methods.length;n++)ttq.setAndDefer(e,ttq.methods[n]);return e}},ttq.load=function(e,n){{var i="https://analytics.tiktok.com/i18n/pixel/events.js";ttq._i=ttq._i||{{}},ttq._i[e]=[],ttq._i[e]._u=i,ttq._t=ttq._t||{{}},ttq._t[e]=+new Date,ttq._o=ttq._o||{{}},ttq._o[e]=n||{{}};var o=document.createElement("script");o.type="text/javascript",o.async=!0,o.src=i+"?sdkid="+e+"&lib="+t;var a=document.getElementsByTagName("script")[0];a.parentNode.insertBefore(o,a)}};
            ttq.load('{escape(tiktok_pixel)}');
            ttq.page();
        }}(window, document, 'ttq');
        </script>
        """)
    if ga_pixel:
        pixels_head_scripts.append(f"""
        <!-- Google Analytics -->
        <script async src="https://www.googletagmanager.com/gtag/js?id={escape(ga_pixel)}"></script>
        <script>
          window.dataLayer = window.dataLayer || [];
          function gtag(){{dataLayer.push(arguments);}}
          gtag('js', new Date());
          gtag('config', '{escape(ga_pixel)}');
        </script>
        """)
    pixels_head_html = "\n".join(pixels_head_scripts)

    # WhatsApp CTA
    whatsapp_html = ""
    whatsapp_data = user.get("whatsapp_btn")
    if whatsapp_data:
        try:
            import json
            wa_info = json.loads(whatsapp_data) if isinstance(whatsapp_data, str) else whatsapp_data
            phone = wa_info.get("phone", "").lstrip("+")
            msg = wa_info.get("msg", "")
            import urllib.parse
            wa_url = f"https://wa.me/{phone}"
            if msg:
                wa_url += f"?text={urllib.parse.quote(msg)}"
            whatsapp_html = (
                f'<a class="whatsapp-cta" href="{wa_url}" target="_blank" rel="noopener">'
                f'<span class="wa-icon">💬</span>'
                f'<div class="wa-text"><strong>تواصل عبر واتساب</strong><span>محادثة فورية مباشرة</span></div>'
                f'<span class="wa-arrow">➜</span></a>'
            )
        except Exception:
            pass

    # Music Player
    audio_player_html = ""
    if music_url:
        audio_player_html = f"""
        <div class="audio-player" id="audioPlayer">
            <button class="audio-toggle" id="audioToggle" title="تشغيل / إيقاف">
                <span id="audioPlayIcon">▶️</span>
            </button>
            <div class="audio-info">
                <div class="audio-title">{music_title}</div>
                <div class="audio-bars" id="audioBars">
                    <span></span><span></span><span></span><span></span><span></span>
                </div>
            </div>
            <audio id="mainAudio" src="{escape(music_url, quote=True)}" preload="none"></audio>
        </div>
        """

    # Social Icons Bar
    social_icons_html = ""
    social_links_data = user.get("social_links")
    if social_links_data:
        try:
            import json
            soc = json.loads(social_links_data) if isinstance(social_links_data, str) else social_links_data
            if isinstance(soc, dict) and any(soc.values()):
                parts = []
                for plat, url in soc.items():
                    if not url:
                        continue
                    url_clean = url.strip()
                    if not (url_clean.startswith("http://") or url_clean.startswith("https://")):
                        url_clean = "https://" + url_clean
                    svg = SOCIAL_ICONS_SVG.get(plat.lower(), "🔗")
                    parts.append(f'<a href="{escape(url_clean, quote=True)}" target="_blank" rel="noopener" class="social-icon" title="{plat}">{svg}</a>')
                if parts:
                    social_icons_html = f'<div class="social-icons-bar">{" ".join(parts)}</div>'
        except Exception:
            pass

    # Links with Section Headers, Subtitles, Thumbnails, Banners, and Featured Glow
    links_html_parts = []
    for link in links:
        link_title = escape(link["title"])
        link_url_raw = link["url"]
        link_url = escape(link_url_raw, quote=True)
        link_id = int(link["id"])
        
        section_header = link.get("section_header")
        if section_header:
            links_html_parts.append(f'<div class="section-header"><span>{escape(section_header)}</span></div>')
            
        subtitle = link.get("subtitle")
        sub_html = f'<div class="btn-sub">{escape(subtitle)}</div>' if subtitle else ''
        
        thumbnail_url = link.get("thumbnail_url")
        is_banner = bool(link.get("is_banner"))
        is_featured = bool(link.get("is_featured"))
        featured_cls = " is-featured" if is_featured else ""
        
        if is_banner and thumbnail_url:
            links_html_parts.append(
                f'<a class="btn btn-banner{featured_cls}" href="{link_url}" target="_blank" rel="noopener" data-link-id="{link_id}">'
                f'<img class="banner-img" src="{escape(thumbnail_url, quote=True)}" alt="">'
                f'<div class="btn-info"><span class="btn-title">{link_title}</span>{sub_html}</div>'
                f'</a>'
            )
        elif thumbnail_url:
            links_html_parts.append(
                f'<a class="btn{featured_cls}" href="{link_url}" target="_blank" rel="noopener" data-link-id="{link_id}">'
                f'<img class="btn-thumb" src="{escape(thumbnail_url, quote=True)}" alt="">'
                f'<div class="btn-info"><span class="btn-title">{link_title}</span>{sub_html}</div>'
                f'</a>'
            )
        else:
            icon = detect_icon(link_url_raw)
            links_html_parts.append(
                f'<a class="btn{featured_cls}" href="{link_url}" target="_blank" rel="noopener" data-link-id="{link_id}">'
                f'<span class="icon">{icon}</span>'
                f'<div class="btn-info"><span class="btn-title">{link_title}</span>{sub_html}</div>'
                f'</a>'
            )
    links_html = "\n".join(links_html_parts) if links_html_parts \
        else '<p class="empty">لم يتم إضافة أي روابط بعد</p>'

    # Reviews & Footer configuration
    show_reviews = user.get("show_reviews") if user.get("show_reviews") is not None else 1
    show_reviews = bool(show_reviews)
    
    reviews_section_html = ""
    review_modal_html = ""
    
    if show_reviews:
        reviews_list = reviews or []
        reviews_cards = []
        for r in reviews_list:
            r_name = escape(r.get("reviewer_name") or "زائر")
            r_rating = int(r.get("rating") or 5)
            r_comment = escape(r.get("comment") or "")
            stars_str = "⭐" * r_rating
            reviews_cards.append(
                f'<div class="review-card">'
                f'<div class="review-header"><strong>{r_name}</strong><span class="stars">{stars_str}</span></div>'
                f'<p class="review-text">{r_comment}</p>'
                f'</div>'
            )
        reviews_cards_html = "\n".join(reviews_cards) if reviews_cards else '<p class="no-reviews">كن أول من يترك تقييماً لطيفاً ⭐</p>'
        
        reviews_section_html = f"""
        <div class="reviews-section">
            <div class="reviews-head">
                <h3>💬 آراء وتقييمات الزوار</h3>
                <button class="add-rev-btn" id="openReviewModal">✍️ أضف تقييمك</button>
            </div>
            <div class="reviews-list">
                {reviews_cards_html}
            </div>
        </div>
        """
        
        review_modal_html = """
    <!-- Review Modal -->
    <div class="modal" id="reviewModal">
        <div class="modal-content">
            <div class="modal-title">⭐ اترك تقييمك</div>
            <div class="form-group">
                <label>اسمك الكريـم:</label>
                <input type="text" id="revName" class="form-control" placeholder="مثال: أحمد">
            </div>
            <div class="form-group">
                <label>التقييم:</label>
                <div class="star-rating" id="starPicker">
                    <span class="star active" data-v="1">⭐</span>
                    <span class="star active" data-v="2">⭐</span>
                    <span class="star active" data-v="3">⭐</span>
                    <span class="star active" data-v="4">⭐</span>
                    <span class="star active" data-v="5">⭐</span>
                </div>
            </div>
            <div class="form-group">
                <label>تعليقك:</label>
                <textarea id="revComment" class="form-control" rows="3" placeholder="اكتب رأيك اللطيف هنا..."></textarea>
            </div>
            <div class="modal-actions">
                <button class="btn-submit" id="submitReview">إرسال التقييم 🚀</button>
                <button class="btn-cancel" id="closeReviewModal">إلغاء</button>
            </div>
        </div>
    </div>
        """

    if is_vip:
        footer_html = '<div class="footer"></div>'
    else:
        footer_html = f'<a href="https://t.me/{settings.BOT_USERNAME}" class="footer" style="text-decoration: none; color: var(--muted); opacity: 0.8; display: block; margin-top: 28px;">مدعوم بواسطة {settings.BOT_USERNAME} ⚡</a>'

    html = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <meta name="theme-color" content="#000000">
    <title>{title}</title>
    {pixels_head_html}
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Almarai:wght@400;700;800&family=Amiri:ital,wght@0,400;0,700;1,400&family=Cairo:wght@400;600;700;800;900&family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&family=Readex+Pro:wght@400;500;600;700&family=Tajawal:wght@400;500;700;800;900&display=swap" rel="stylesheet">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        html, body {{
            min-height: 100vh;
            font-family: {font_stack};
            color: var(--text);
            -webkit-font-smoothing: antialiased;
            overflow-x: hidden;
        }}
        {theme_css}
        
        /* Canvas & Background Pattern Effects */
        #bgCanvas, #particleCanvas, #bgPattern {
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            pointer-events: none;
        }
        #bgPattern { z-index: 0; background-attachment: fixed; }
        #bgCanvas { z-index: 1; }
        #particleCanvas { z-index: 99; }

        /* Background Pattern Styles */
        .bg-pattern-none { display: none; }
        .bg-pattern-tg_doodles {
            background-image: url("data:image/svg+xml,%3Csvg%20xmlns%3D%27http%3A//www.w3.org/2000/svg%27%20width%3D%27140%27%20height%3D%27140%27%20viewBox%3D%270%200%20140%20140%27%3E%3Cg%20fill%3D%27none%27%20stroke%3D%27white%27%20stroke-width%3D%271.5%27%20stroke-opacity%3D%270.18%27%20stroke-linecap%3D%27round%27%20stroke-linejoin%3D%27round%27%3E%3Cpath%20d%3D%27M15%2035L45%2015L28%2050L24%2038L38%2025L23%2036Z%27/%3E%3Cpath%20d%3D%27M75%2018c-5%200-9%203-9%208%200%203%202%206%206%207l-2%206%206-3c2%200%204-1%205-2%203-2%206-5%206-8%200-5-6-8-12-8z%27/%3E%3Cpolygon%20points%3D%27115%2C18%20117%2C24%20123%2C24%20118%2C28%20120%2C34%20115%2C30%20110%2C34%20112%2C28%20107%2C24%20113%2C24%27/%3E%3Cpath%20d%3D%27M20%2085h16v12c0%204-4%208-8%208s-8-4-8-8zM36%2089h4c2%200%203%201%203%203s-1%203-3%203h-4%27/%3E%3Cpath%20d%3D%27M75%2088c-4-8-16-4-16%206%200%208%2016%2018%2016%2018s16-10%2016-18c0-10-12-14-16-6z%27/%3E%3Crect%20x%3D%27100%27%20y%3D%2785%27%20width%3D%2726%27%20height%3D%2716%27%20rx%3D%275%27/%3E%3Ccircle%20cx%3D%27106%27%20cy%3D%2793%27%20r%3D%271.5%27/%3E%3Ccircle%20cx%3D%27120%27%20cy%3D%2793%27%20r%3D%271.5%27/%3E%3C/g%3E%3C/svg%3E");
            background-size: 140px 140px;
            opacity: 0.85;
        }
        .bg-pattern-arabic_art {
            background-image: url("data:image/svg+xml,%3Csvg%20xmlns%3D%27http%3A//www.w3.org/2000/svg%27%20width%3D%27120%27%20height%3D%27120%27%20viewBox%3D%270%200%20120%20120%27%3E%3Cg%20fill%3D%27none%27%20stroke%3D%27white%27%20stroke-width%3D%271.2%27%20stroke-opacity%3D%270.16%27%3E%3Crect%20x%3D%2735%27%20y%3D%2735%27%20width%3D%2750%27%20height%3D%2750%27%20transform%3D%27rotate(45%2060%2060)%27/%3E%3Crect%20x%3D%2735%27%20y%3D%2735%27%20width%3D%2750%27%20height%3D%2750%27/%3E%3Cpath%20d%3D%27M0%2060L60%200M60%20120L120%2060M0%2060L60%20120M60%200L120%2060M60%2020L100%2060L60%20100L20%2060Z%27/%3E%3C/g%3E%3C/svg%3E");
            background-size: 120px 120px;
            opacity: 0.9;
        }
        .bg-pattern-contour_lines {
            background-image: url("data:image/svg+xml,%3Csvg%20xmlns%3D%27http%3A//www.w3.org/2000/svg%27%20width%3D%27200%27%20height%3D%27200%27%20viewBox%3D%270%200%20200%20200%27%3E%3Cg%20fill%3D%27none%27%20stroke%3D%27white%27%20stroke-width%3D%271.4%27%20stroke-opacity%3D%270.15%27%3E%3Cpath%20d%3D%27M-20%2060Q40%2020%20100%2060T220%2060M-20%20100Q50%2060%20110%20100T220%20100M-20%20140Q30%20110%2090%20140T220%20140M-20%2020Q60%20-10%20120%2020T220%2020M-20%20180Q70%20150%20130%20180T220%20180%27/%3E%3C/g%3E%3C/svg%3E");
            background-size: 200px 200px;
            opacity: 0.85;
        }
        .bg-pattern-gaming_icons {
            background-image: url("data:image/svg+xml,%3Csvg%20xmlns%3D%27http%3A//www.w3.org/2000/svg%27%20width%3D%27140%27%20height%3D%27140%27%20viewBox%3D%270%200%20140%20140%27%3E%3Cg%20fill%3D%27none%27%20stroke%3D%27white%27%20stroke-width%3D%271.5%27%20stroke-opacity%3D%270.18%27%3E%3Crect%20x%3D%2715%27%20y%3D%2725%27%20width%3D%2740%27%20height%3D%2724%27%20rx%3D%278%27/%3E%3Cpath%20d%3D%27M25%2037h8M29%2033v8M45%2035h.01M49%2039h.01%27/%3E%3Cpath%20d%3D%27M85%2025h30v15c0%208-7%2015-15%2015s-15-7-15-15zM85%2030H80M115%2030h5M100%2055v10M90%2065h20%27/%3E%3Cpolygon%20points%3D%2735%2C90%2040%2C80%2045%2C90%2035%2C90%27/%3E%3Cpath%20d%3D%27M25%20105l20-20M90%2095l15-15%2015%2015-15%2015z%27/%3E%3C/g%3E%3C/svg%3E");
            background-size: 140px 140px;
            opacity: 0.85;
        }
        .bg-pattern-hex_grid {
            background-image: url("data:image/svg+xml,%3Csvg%20xmlns%3D%27http%3A//www.w3.org/2000/svg%27%20width%3D%2760%27%20height%3D%27104%27%20viewBox%3D%270%200%2060%20104%27%3E%3Cpath%20d%3D%27M60%200L30%2017.3%200%200v34.6L30%2052l30-17.3V0zM30%2069.3L0%2086.6v17.4l30-17.3%2030%2017.3v-17.4L30%2069.3z%27%20fill%3D%27none%27%20stroke%3D%27white%27%20stroke-width%3D%271.2%27%20stroke-opacity%3D%270.16%27/%3E%3C/svg%3E");
            background-size: 60px 104px;
            opacity: 0.85;
        }
        .bg-pattern-polka_dots {
            background-image: radial-gradient(rgba(255, 255, 255, 0.18) 1.5px, transparent 1.5px);
            background-size: 24px 24px;
            opacity: 0.9;
        }
        .bg-pattern-mesh_glow {
            background: 
                radial-gradient(circle at 10% 20%, rgba(0, 240, 255, 0.28) 0%, transparent 45%),
                radial-gradient(circle at 90% 80%, rgba(124, 58, 237, 0.35) 0%, transparent 50%),
                radial-gradient(circle at 50% 50%, rgba(255, 0, 128, 0.22) 0%, transparent 55%);
            mix-blend-mode: screen;
            filter: blur(35px);
        }

        .wrap {{
            position: relative; z-index: 2;
            max-width: 520px; margin: 0 auto; padding: 24px 20px 60px;
            min-height: 100vh; display: flex; flex-direction: column;
            align-items: stretch; animation: fadeIn 0.6s ease-out;
        }}
        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}

        /* Marquee Bar */
        .marquee-bar {{
            display: flex; align-items: center; gap: 10px;
            background: var(--card); border: 1px solid rgba(255,255,255,0.12);
            border-radius: 14px; padding: 8px 12px; margin-bottom: 20px;
            backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.15); overflow: hidden;
            text-decoration: none; color: inherit; transition: transform 0.2s ease, border-color 0.2s ease;
        }}
        .marquee-bar.is-link:hover {{ transform: translateY(-2px); border-color: var(--accent); }}
        .marquee-tag {{
            background: linear-gradient(135deg, #ff4b2b, #ff416c);
            color: #fff; font-size: 11px; font-weight: 800;
            padding: 3px 8px; border-radius: 8px; white-space: nowrap; flex-shrink: 0;
            animation: tagPulse 2s infinite ease-in-out;
        }}
        @keyframes tagPulse {{ 0%, 100% {{ transform: scale(1); }} 50% {{ transform: scale(1.06); }} }}
        .marquee-track {{ flex: 1; overflow: hidden; white-space: nowrap; display: flex; }}
        .marquee-content {{
            display: inline-flex; align-items: center; gap: 18px;
            font-size: 13px; font-weight: 600; color: var(--text);
            animation: marqueeScroll 18s linear infinite;
        }}
        .marquee-content:hover {{ animation-play-state: paused; }}
        .mq-dot {{ opacity: 0.5; font-size: 10px; }}
        .mq-arrow {{ font-size: 14px; opacity: 0.8; margin-right: 4px; }}
        @keyframes marqueeScroll {{
            0% {{ transform: translateX(0); }}
            100% {{ transform: translateX(50%); }}
        }}

        /* Countdown Widget */
        .countdown-widget {{
            background: var(--card); border: 1px solid rgba(255,255,255,0.12);
            border-radius: 18px; padding: 14px 16px; margin-bottom: 20px;
            backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
            box-shadow: var(--shadow); text-align: center;
        }}
        .countdown-head {{
            font-size: 13px; font-weight: 700; color: var(--text);
            margin-bottom: 10px; display: flex; align-items: center; justify-content: center; gap: 6px;
        }}
        .cd-pulse {{ animation: cdPulse 1.5s infinite; }}
        @keyframes cdPulse {{ 0%, 100% {{ transform: scale(1); }} 50% {{ transform: scale(1.2); }} }}
        .countdown-grid {{
            display: flex; align-items: center; justify-content: center; gap: 6px;
        }}
        .cd-box {{
            background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.1);
            border-radius: 10px; padding: 6px 10px; min-width: 50px;
            display: flex; flex-direction: column; align-items: center;
        }}
        .cd-num {{ font-size: 18px; font-weight: 800; color: var(--accent); font-variant-numeric: tabular-nums; }}
        .cd-lbl {{ font-size: 10px; color: var(--muted); margin-top: 2px; }}
        .cd-sep {{ font-size: 18px; font-weight: 800; color: var(--muted); opacity: 0.6; }}
        
        .avatar {{
            width: 110px; height: 110px; border-radius: 50%;
            margin: 8px auto 16px; background: var(--btn-bg);
            display: grid; place-items: center;
            font-size: 44px; font-weight: 800;
            color: var(--btn-text); border: 3px solid var(--avatar-ring);
            box-shadow: var(--shadow); overflow: hidden;
            position: relative;
        }}
        .avatar-img {{ object-fit: cover; }}
        
        h1 {{
            font-size: 24px; font-weight: 800; text-align: center;
            color: var(--text); margin-bottom: 6px; letter-spacing: -0.3px;
            display: flex; align-items: center; justify-content: center; gap: 8px;
        }}
        
        .verified {{ display: inline-flex; align-items: center; justify-content: center; }}
        .badge-gold svg {{ filter: drop-shadow(0 0 6px rgba(255, 215, 0, 0.6)); animation: goldPulse 2.5s infinite ease-in-out; }}
        .badge-diamond svg {{ filter: drop-shadow(0 0 6px rgba(0, 242, 254, 0.7)); animation: diamShine 3s infinite ease-in-out; }}
        .badge-creator svg {{ filter: drop-shadow(0 0 6px rgba(255, 88, 88, 0.6)); }}
        .badge-star svg {{ filter: drop-shadow(0 0 6px rgba(255, 226, 89, 0.6)); animation: goldPulse 2.5s infinite ease-in-out; }}
        @keyframes goldPulse {{ 0%, 100% {{ transform: scale(1); }} 50% {{ transform: scale(1.1); }} }}
        @keyframes diamShine {{ 0%, 100% {{ transform: rotate(0deg); }} 50% {{ transform: rotate(8deg); }} }}

        .bio {{ font-size: 14px; text-align: center; color: var(--muted);
                margin-bottom: 16px; line-height: 1.6; padding: 0 8px; }}

        /* Social Icons Bar */
        .social-icons-bar {{
            display: flex; align-items: center; justify-content: center;
            gap: 12px; flex-wrap: wrap; margin-bottom: 22px;
        }}
        .social-icon {{
            width: 44px; height: 44px; border-radius: 50%;
            display: grid; place-items: center;
            background: var(--card); color: var(--text);
            border: 1px solid rgba(255,255,255,0.15);
            text-decoration: none; transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
            box-shadow: 0 3px 10px rgba(0,0,0,0.15);
        }}
        .social-icon:hover {{
            transform: translateY(-3px) scale(1.08);
            box-shadow: 0 8px 20px rgba(0,0,0,0.25);
            color: var(--accent);
        }}
                
        .card {{ background: var(--card); border-radius: 20px; padding: 20px 16px; box-shadow: var(--shadow); margin-bottom: 20px; }}
        .links {{ display: flex; flex-direction: column; gap: 14px; }}
        
        /* Section Header */
        .section-header {{
            text-align: center; margin: 18px 0 8px; font-size: 15px; font-weight: 700;
            color: var(--text); display: flex; align-items: center; justify-content: center; gap: 10px;
        }}
        .section-header::before, .section-header::after {{
            content: ""; flex: 1; height: 1px; background: rgba(255,255,255,0.15);
        }}
        
        .btn {{
            display: flex; align-items: center; gap: 14px;
            width: 100%; padding: 14px 18px; border-radius: 16px;
            font-size: 15px; font-weight: 600; text-align: right;
            text-decoration: none; cursor: pointer;
            transition: transform 0.18s ease, background 0.25s ease, box-shadow 0.25s ease;
            position: relative; overflow: hidden;
        }}
        .btn .icon {{ font-size: 22px; flex-shrink: 0; }}
        .btn-thumb {{ width: 44px; height: 44px; border-radius: 10px; object-fit: cover; flex-shrink: 0; }}
        .btn-info {{ flex: 1; display: flex; flex-direction: column; min-width: 0; }}
        .btn-title {{ font-size: 15px; font-weight: 700; color: inherit; }}
        .btn-sub {{ font-size: 12px; color: var(--muted); margin-top: 2px; line-height: 1.3; }}
        
        /* Banner Link Card */
        .btn-banner {{
            flex-direction: column !important; padding: 0 !important; align-items: stretch !important;
        }}
        .banner-img {{
            width: 100%; height: 160px; object-fit: cover; border-top-left-radius: inherit; border-top-right-radius: inherit;
        }}
        .btn-banner .btn-info {{ padding: 14px 18px; text-align: center; }}
        
        /* Featured Glow Link */
        .btn.is-featured {{
            border: 2px solid #ffb800 !important;
            animation: goldGlow 2.5s infinite ease-in-out;
        }}
        @keyframes goldGlow {{
            0%, 100% {{ box-shadow: 0 0 12px rgba(255, 184, 0, 0.45); }}
            50% {{ box-shadow: 0 0 24px rgba(255, 184, 0, 0.85); }}
        }}

        .btn:active {{ transform: scale(0.98); }}
        .empty {{ text-align: center; color: var(--muted); padding: 22px 8px; font-size: 14px; }}
        
        /* Audio Player Widget */
        .audio-player {{
            display: flex; align-items: center; gap: 14px;
            background: var(--card); border: 1px solid rgba(255,255,255,0.15);
            border-radius: 16px; padding: 12px 16px; margin-bottom: 20px;
            backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
            box-shadow: var(--shadow);
        }}
        .audio-toggle {{
            width: 44px; height: 44px; border-radius: 50%;
            background: var(--btn-bg); color: var(--btn-text);
            border: none; cursor: pointer; display: grid; place-items: center;
            font-size: 18px; flex-shrink: 0; box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            transition: transform 0.2s ease;
        }}
        .audio-toggle:active {{ transform: scale(0.92); }}
        .audio-info {{ flex: 1; overflow: hidden; }}
        .audio-title {{ font-size: 14px; font-weight: 700; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .audio-bars {{ display: flex; align-items: flex-end; gap: 3px; height: 16px; margin-top: 4px; }}
        .audio-bars span {{ width: 3px; height: 4px; background: var(--accent); border-radius: 2px; transition: height 0.2s ease; }}
        .audio-playing .audio-bars span:nth-child(1) {{ animation: eq 0.8s infinite ease-in-out; }}
        .audio-playing .audio-bars span:nth-child(2) {{ animation: eq 0.6s infinite ease-in-out 0.2s; }}
        .audio-playing .audio-bars span:nth-child(3) {{ animation: eq 1.0s infinite ease-in-out 0.4s; }}
        .audio-playing .audio-bars span:nth-child(4) {{ animation: eq 0.7s infinite ease-in-out 0.1s; }}
        .audio-playing .audio-bars span:nth-child(5) {{ animation: eq 0.9s infinite ease-in-out 0.3s; }}
        @keyframes eq {{ 0%, 100% {{ height: 4px; }} 50% {{ height: 16px; }} }}
        
        /* WhatsApp CTA */
        .whatsapp-cta {{
            display: flex; align-items: center; gap: 12px;
            background: linear-gradient(135deg, #25D366, #128C7E);
            color: #fff; text-decoration: none; border-radius: 16px;
            padding: 14px 18px; margin-bottom: 20px; box-shadow: 0 6px 20px rgba(37, 211, 102, 0.3);
            transition: transform 0.2s ease, box-shadow 0.2s ease; font-weight: 600;
        }}
        .whatsapp-cta:hover {{ transform: translateY(-2px); box-shadow: 0 10px 25px rgba(37, 211, 102, 0.4); }}
        .wa-icon {{ font-size: 26px; }}
        .wa-text {{ flex: 1; display: flex; flex-direction: column; }}
        .wa-text strong {{ font-size: 15px; }}
        .wa-text span {{ font-size: 12px; opacity: 0.85; }}
        .wa-arrow {{ font-size: 18px; }}

        /* Reviews Section */
        .reviews-section {{ margin-top: 10px; background: var(--card); border-radius: 20px; padding: 20px 16px; }}
        .reviews-head {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }}
        .reviews-head h3 {{ font-size: 16px; font-weight: 700; color: var(--text); }}
        .add-rev-btn {{ background: var(--btn-bg); color: var(--btn-text); border: none; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 600; cursor: pointer; }}
        .reviews-list {{ display: flex; flex-direction: column; gap: 10px; }}
        .review-card {{ background: rgba(255,255,255,0.05); border-radius: 12px; padding: 12px; border: 1px solid rgba(255,255,255,0.08); }}
        .review-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; font-size: 13px; }}
        .review-text {{ font-size: 13px; color: var(--muted); line-height: 1.4; }}
        .no-reviews {{ text-align: center; font-size: 13px; color: var(--muted); padding: 12px; }}

        /* Modal Form */
        .modal {{ display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.6); z-index: 100; place-items: center; padding: 20px; backdrop-filter: blur(8px); }}
        .modal-content {{ background: var(--card); width: 100%; max-width: 400px; border-radius: 20px; padding: 24px; border: 1px solid rgba(255,255,255,0.2); box-shadow: 0 20px 40px rgba(0,0,0,0.5); }}
        .modal-title {{ font-size: 18px; font-weight: 800; margin-bottom: 16px; text-align: center; }}
        .form-group {{ margin-bottom: 14px; }}
        .form-group label {{ display: block; font-size: 13px; margin-bottom: 6px; color: var(--muted); }}
        .form-control {{ width: 100%; padding: 10px 12px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.2); background: rgba(0,0,0,0.2); color: #fff; font-family: inherit; font-size: 14px; }}
        .star-rating {{ display: flex; gap: 8px; font-size: 24px; cursor: pointer; justify-content: center; margin: 8px 0; }}
        .star {{ transition: transform 0.15s; opacity: 0.4; }}
        .star.active {{ opacity: 1; transform: scale(1.1); }}
        .modal-actions {{ display: flex; gap: 10px; margin-top: 18px; }}
        .btn-submit {{ flex: 1; background: var(--accent); color: #000; border: none; padding: 12px; border-radius: 10px; font-weight: 700; cursor: pointer; }}
        .btn-cancel {{ background: rgba(255,255,255,0.1); color: #fff; border: none; padding: 12px 18px; border-radius: 10px; cursor: pointer; }}

        .footer {{ margin-top: 28px; text-align: center; font-size: 12px; color: var(--muted); opacity: 0.8; }}
    </style>
</head>
<body>
    <div id="bgPattern" class="bg-pattern-{bg_effect}"></div>
    <canvas id="bgCanvas"></canvas>
    <canvas id="particleCanvas"></canvas>

    <div class="wrap">
        {marquee_html}
        {countdown_html}
        {avatar_html}
        <h1>{title} {verified_badge}</h1>
        {'<div class="bio">' + bio + '</div>' if bio else ''}
        {social_icons_html}
        
        {audio_player_html}
        {whatsapp_html}

        <div class="card">
            <div class="links">
                {links_html}
            </div>
        </div>

        {reviews_section_html}
        {footer_html}
    </div>

    {review_modal_html}

    <script>
        // Countdown Timer Logic
        (function() {{
            var cdWidget = document.getElementById("countdownWidget");
            if (!cdWidget) return;
            var targetStr = cdWidget.getAttribute("data-target");
            var targetDate = new Date(targetStr).getTime();
            if (isNaN(targetDate)) return;

            function updateCd() {{
                var now = new Date().getTime();
                var diff = targetDate - now;
                if (diff <= 0) {{
                    document.getElementById("cdDays").textContent = "00";
                    document.getElementById("cdHours").textContent = "00";
                    document.getElementById("cdMins").textContent = "00";
                    document.getElementById("cdSecs").textContent = "00";
                    return;
                }}
                var days = Math.floor(diff / (1000 * 60 * 60 * 24));
                var hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                var mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                var secs = Math.floor((diff % (1000 * 60)) / 1000);

                document.getElementById("cdDays").textContent = String(days).padStart(2, '0');
                document.getElementById("cdHours").textContent = String(hours).padStart(2, '0');
                document.getElementById("cdMins").textContent = String(mins).padStart(2, '0');
                document.getElementById("cdSecs").textContent = String(secs).padStart(2, '0');
            }}
            updateCd();
            setInterval(updateCd, 1000);
        }})();

        // WebApp Init
        try {{
            if (window.Telegram && window.Telegram.WebApp) {{
                window.Telegram.WebApp.ready();
                window.Telegram.WebApp.expand();
            }}
        }} catch (e) {{}}

        function getTgUserPayload() {{
            var payload = {{}};
            try {{
                var wa = window.Telegram && window.Telegram.WebApp;
                if (wa && wa.initDataUnsafe && wa.initDataUnsafe.user) {{
                    var u = wa.initDataUnsafe.user;
                    if (u.first_name) payload.first_name = u.first_name;
                    if (u.last_name) payload.last_name = u.last_name;
                    if (u.language_code) payload.language_code = u.language_code;
                }}
            }} catch (e) {{}}
            return payload;
        }}

        // Analytics Tracking
        try {{
            fetch("/api/track/{user_id}/visit", {{
                method: "POST", keepalive: true,
                headers: {{ "Content-Type": "application/json" }},
                body: JSON.stringify(getTgUserPayload()),
            }});
        }} catch (e) {{}}

        document.querySelectorAll("a.btn[data-link-id]").forEach(function(a) {{
            a.addEventListener("click", function() {{
                var lid = a.getAttribute("data-link-id");
                try {{
                    fetch("/api/track/{user_id}/click/" + lid, {{
                        method: "POST", keepalive: true,
                        headers: {{ "Content-Type": "application/json" }},
                        body: JSON.stringify(getTgUserPayload()),
                    }});
                }} catch (e) {{}}
            }});
        }});

        // Audio Player Logic
        var audio = document.getElementById("mainAudio");
        var audioBtn = document.getElementById("audioToggle");
        var audioPlayer = document.getElementById("audioPlayer");
        var audioPlayIcon = document.getElementById("audioPlayIcon");
        if (audio && audioBtn) {{
            audioBtn.addEventListener("click", function() {{
                if (audio.paused) {{
                    audio.play().then(function() {{
                        audioPlayer.classList.add("audio-playing");
                        audioPlayIcon.textContent = "⏸️";
                    }}).catch(function(err){{}});
                }} else {{
                    audio.pause();
                    audioPlayer.classList.remove("audio-playing");
                    audioPlayIcon.textContent = "▶️";
                }}
            }});
        }}

        // Reviews Modal Logic
        var openRev = document.getElementById("openReviewModal");
        var closeRev = document.getElementById("closeReviewModal");
        var revModal = document.getElementById("reviewModal");
        var submitRev = document.getElementById("submitReview");
        var currentRating = 5;

        if (openRev && revModal) {{
            openRev.onclick = function() {{ revModal.style.display = "grid"; }};
            closeRev.onclick = function() {{ revModal.style.display = "none"; }};
            
            var stars = document.querySelectorAll("#starPicker .star");
            stars.forEach(function(s) {{
                s.onclick = function() {{
                    currentRating = parseInt(s.getAttribute("data-v"));
                    stars.forEach(function(st, idx) {{
                        if (idx < currentRating) st.classList.add("active");
                        else st.classList.remove("active");
                    }});
                }};
            }});

            submitRev.onclick = function() {{
                var name = document.getElementById("revName").value.trim() || "زائر";
                var comment = document.getElementById("revComment").value.trim();
                if (!comment) {{ alert("الرجاء كتابة تعليق لطيف قبل الإرسال 😊"); return; }}
                
                submitRev.textContent = "جاري الإرسال...";
                submitRev.disabled = true;

                fetch("/api/review/{user_id}", {{
                    method: "POST",
                    headers: {{ "Content-Type": "application/json" }},
                    body: JSON.stringify({{ reviewer_name: name, rating: currentRating, comment: comment }})
                }}).then(function(r) {{ return r.json(); }}).then(function(res) {{
                    alert("شكراً لك! تم إرسال تقييمك وسيظهر بالصفحة فور اعتماده من صاحب الصفحة ✨");
                    revModal.style.display = "none";
                    submitRev.textContent = "إرسال التقييم 🚀";
                    submitRev.disabled = false;
                }}).catch(function() {{
                    alert("حدث خطأ أثناء الإرسال، حاول مجدداً.");
                    submitRev.textContent = "إرسال التقييم 🚀";
                    submitRev.disabled = false;
                }});
            }};
        }}

        // Live Backgrounds & Touch Particles
        (function() {{
            var bgType = "{bg_effect}";
            var bgCanvas = document.getElementById("bgCanvas");
            var pCanvas = document.getElementById("particleCanvas");
            if (!bgCanvas || !pCanvas) return;
            
            var bgCtx = bgCanvas.getContext("2d");
            var pCtx = pCanvas.getContext("2d");
            var w, h;
            
            function resize() {{
                w = bgCanvas.width = pCanvas.width = window.innerWidth;
                h = bgCanvas.height = pCanvas.height = window.innerHeight;
            }}
            window.addEventListener("resize", resize);
            resize();

            // 1. Touch / Mouse Particles Trail
            var particles = [];
            function addParticle(x, y) {{
                for (var i = 0; i < 2; i++) {{
                    particles.push({{
                        x: x, y: y,
                        vx: (Math.random() - 0.5) * 2,
                        vy: (Math.random() - 0.5) * 2 - 0.5,
                        size: Math.random() * 3 + 1.5,
                        alpha: 1,
                        color: ["#00f5d4", "#7b2cbf", "#ffd700", "#ff007f", "#58a6ff"][Math.floor(Math.random() * 5)]
                    }});
                }}
            }}
            window.addEventListener("mousemove", function(e) {{ addParticle(e.clientX, e.clientY); }});
            window.addEventListener("touchmove", function(e) {{
                if (e.touches[0]) addParticle(e.touches[0].clientX, e.touches[0].clientY);
            }});

            // 2. Background Stars / Orbs
            var bgItems = [];
            if (bgType === "stars" || bgType === "neon" || bgType === "bubbles") {{
                var count = bgType === "bubbles" ? 25 : 60;
                for (var i = 0; i < count; i++) {{
                    bgItems.push({{
                        x: Math.random() * w, y: Math.random() * h,
                        r: Math.random() * (bgType === "bubbles" ? 15 : 2) + 1,
                        speed: Math.random() * 0.6 + 0.2,
                        alpha: Math.random() * 0.7 + 0.3
                    }});
                }}
            }}

            function loop() {{
                // Draw Touch Particles
                pCtx.clearRect(0, 0, w, h);
                for (var i = particles.length - 1; i >= 0; i--) {{
                    var p = particles[i];
                    p.x += p.vx; p.y += p.vy;
                    p.alpha -= 0.025;
                    if (p.alpha <= 0) {{ particles.splice(i, 1); continue; }}
                    pCtx.beginPath();
                    pCtx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
                    pCtx.fillStyle = p.color;
                    pCtx.globalAlpha = p.alpha;
                    pCtx.fill();
                }}
                pCtx.globalAlpha = 1.0;

                // Draw Live Background
                if (bgItems.length > 0) {{
                    bgCtx.clearRect(0, 0, w, h);
                    for (var j = 0; j < bgItems.length; j++) {{
                        var item = bgItems[j];
                        item.y -= item.speed;
                        if (item.y < 0) item.y = h;
                        bgCtx.beginPath();
                        bgCtx.arc(item.x, item.y, item.r, 0, Math.PI * 2);
                        bgCtx.fillStyle = bgType === "bubbles" ? "rgba(88, 166, 255, " + item.alpha * 0.2 + ")" : "rgba(255, 255, 255, " + item.alpha + ")";
                        bgCtx.fill();
                    }}
                }}
                requestAnimationFrame(loop);
            }}
            loop();
        }})();
    </script>
</body>
</html>
"""
    return html
