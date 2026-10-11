"""Light + dark QSS."""

_LIGHT = """
* { font-family: "Ubuntu Sans", "Inter", "Segoe UI", system-ui, sans-serif;
    font-size: 13px; color: #1f2330; }
QMainWindow, QWidget { background: #f5f6f8; }
QScrollArea { background: transparent; border: none; }
QScrollArea > QWidget > QWidget { background: transparent; }

#Toolbar { background: #ffffff; border-bottom: 1px solid #e3e6ec; }
#Brand { font-size: 22px; font-weight: 800; color: #8b5cf6;
    letter-spacing: -0.5px; }
#Muted { color: #8a92a3; font-size: 12px; }

QLineEdit#Search { background: #f5f6f8; border: 1px solid #e3e6ec;
    border-radius: 9px; padding: 8px 12px; font-size: 13.5px; }
QLineEdit#Search:focus { background: #ffffff; border-color: #8b5cf6; }

QPushButton { background: #ffffff; border: 1px solid #e3e6ec;
    border-radius: 9px; padding: 8px 14px; }
QPushButton:hover { background: #eef1f6; }
QPushButton#Primary { background: #8b5cf6; color: #ffffff;
    border: 1px solid #8b5cf6; font-weight: 600; }
QPushButton#Primary:hover { background: #7c3aed; border-color: #7c3aed; }
QPushButton#Danger { color: #ef4444; border-color: #fca5a5; }
QPushButton#Danger:hover { background: #ef4444; color: #ffffff; }
QPushButton#Chip { background: #f5f6f8; border: 1px solid #e3e6ec;
    border-radius: 12px; padding: 3px 12px; font-size: 11.5px;
    color: #8a92a3; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.3px; }
QPushButton#Chip:checked { background: #8b5cf6; border-color: #8b5cf6;
    color: #ffffff; }

#FilterBar { background: #ffffff; border-bottom: 1px solid #e3e6ec; }

#DropZone { background: #f0f4ff; border: 2px dashed #cbd2dc;
    border-radius: 10px; margin: 12px 20px 4px 20px; }
#DropZone[dragover="true"] { background: #e0e8ff; border-color: #8b5cf6; }
#DropZoneLabel { color: #8a92a3; font-size: 12.5px; }

#PaperCard { background: #ffffff; border: 1px solid #e3e6ec;
    border-radius: 12px; }
#PaperCard:hover { border-color: #8b5cf6; background: #faf8ff; }
#PaperCard[dragover="true"] { border: 2px solid #8b5cf6;
    background: #f3ebff; }
#PaperCover { background: #eef1f6; border-top-left-radius: 12px;
    border-top-right-radius: 12px; }
#CardTitle { font-size: 13.5px; font-weight: 700; color: #1f2330; }
#CardPath  { font-family: "Ubuntu Sans Mono", monospace; font-size: 11px;
    color: #8a92a3; }
#CardDesc  { font-size: 11.5px; color: #566072; }

#Status_drafting          { background:#e5e7eb; color:#4b5563;
    border-radius:8px; padding:3px 10px; font-size:10.5px;
    font-weight:700; letter-spacing:.5px; }
#Status_idea              { background:#cffafe; color:#0891b2;
    border-radius:8px; padding:3px 10px; font-size:10.5px;
    font-weight:700; letter-spacing:.5px; }
#Status_ready             { background:#d1fae5; color:#047857;
    border-radius:8px; padding:3px 10px; font-size:10.5px;
    font-weight:700; letter-spacing:.5px; }
#Status_submitted         { background:#dbeafe; color:#1d4ed8;
    border-radius:8px; padding:3px 10px; font-size:10.5px;
    font-weight:700; letter-spacing:.5px; }
#Status_in_review         { background:#e0e7ff; color:#4338ca;
    border-radius:8px; padding:3px 10px; font-size:10.5px;
    font-weight:700; letter-spacing:.5px; }
#Status_revision_requested{ background:#fef3c7; color:#b45309;
    border-radius:8px; padding:3px 10px; font-size:10.5px;
    font-weight:700; letter-spacing:.5px; }
#Status_accepted          { background:#a7f3d0; color:#065f46;
    border-radius:8px; padding:3px 10px; font-size:10.5px;
    font-weight:700; letter-spacing:.5px; }
#Status_published         { background:#c7d2fe; color:#3730a3;
    border-radius:8px; padding:3px 10px; font-size:10.5px;
    font-weight:700; letter-spacing:.5px; }
#Status_rejected          { background:#fee2e2; color:#991b1b;
    border-radius:8px; padding:3px 10px; font-size:10.5px;
    font-weight:700; letter-spacing:.5px; }

#Empty { color:#8a92a3; font-size:14px; padding:80px 0; }
QStatusBar { background:#ffffff; color:#8a92a3;
    border-top:1px solid #e3e6ec; }
QStatusBar::item { border: none; }
"""

_DARK = """
* { font-family: "Ubuntu Sans", "Inter", "Segoe UI", system-ui, sans-serif;
    font-size: 13px; color: #e6e9ef; }
QMainWindow, QWidget { background: #0f1115; }
QScrollArea { background: transparent; border: none; }
QScrollArea > QWidget > QWidget { background: transparent; }

#Toolbar { background: #161a21; border-bottom: 1px solid #262d3a; }
#Brand { font-size: 22px; font-weight: 800; color: #bb9af7;
    letter-spacing: -0.5px; }
#Muted { color: #8a93a6; font-size: 12px; }

QLineEdit#Search { background: #1a1f28; border: 1px solid #262d3a;
    border-radius: 9px; padding: 8px 12px; font-size: 13.5px;
    color: #e6e9ef; }
QLineEdit#Search:focus { background: #0f1115; border-color: #bb9af7; }

QPushButton { background: #1a1f28; border: 1px solid #262d3a;
    border-radius: 9px; padding: 8px 14px; }
QPushButton:hover { background: #232a38; border-color: #3a4455; }
QPushButton#Primary { background: #bb9af7; color: #0f1115;
    border: 1px solid #bb9af7; font-weight: 600; }
QPushButton#Primary:hover { background: #c4a8fa; border-color: #c4a8fa; }
QPushButton#Danger { color: #f7768e; border-color: #5a2a38; }
QPushButton#Danger:hover { background: #f7768e; color: #0f1115; }
QPushButton#Chip { background: #1a1f28; border: 1px solid #262d3a;
    border-radius: 12px; padding: 3px 12px; font-size: 11.5px;
    color: #8a93a6; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.3px; }
QPushButton#Chip:checked { background: #bb9af7; border-color: #bb9af7;
    color: #0f1115; }

#FilterBar { background: #161a21; border-bottom: 1px solid #262d3a; }

#DropZone { background: #1a1f28; border: 2px dashed #3a4455;
    border-radius: 10px; margin: 12px 20px 4px 20px; }
#DropZone[dragover="true"] { background: #2b3a5a; border-color: #bb9af7; }
#DropZoneLabel { color: #8a93a6; font-size: 12.5px; }

#PaperCard { background: #1a1f28; border: 1px solid #262d3a;
    border-radius: 12px; }
#PaperCard:hover { border-color: #bb9af7; background: #1e2130; }
#PaperCard[dragover="true"] { border: 2px solid #bb9af7;
    background: #241c38; }
#PaperCover { background: #232a38; border-top-left-radius: 12px;
    border-top-right-radius: 12px; }
#CardTitle { font-size: 13.5px; font-weight: 700; color: #e6e9ef; }
#CardPath  { font-family: "Ubuntu Sans Mono", monospace; font-size: 11px;
    color: #8a93a6; }
#CardDesc  { font-size: 11.5px; color: #a8b0c1; }

#Status_drafting          { background:#2c3546; color:#c6cbd6;
    border-radius:8px; padding:3px 10px; font-size:10.5px;
    font-weight:700; letter-spacing:.5px; }
#Status_idea              { background:#1a3d46; color:#67e8f9;
    border-radius:8px; padding:3px 10px; font-size:10.5px;
    font-weight:700; letter-spacing:.5px; }
#Status_ready             { background:#1a3d2c; color:#86efac;
    border-radius:8px; padding:3px 10px; font-size:10.5px;
    font-weight:700; letter-spacing:.5px; }
#Status_submitted         { background:#1e3a5f; color:#9ab8fa;
    border-radius:8px; padding:3px 10px; font-size:10.5px;
    font-weight:700; letter-spacing:.5px; }
#Status_in_review         { background:#2a2f5f; color:#a5b4fc;
    border-radius:8px; padding:3px 10px; font-size:10.5px;
    font-weight:700; letter-spacing:.5px; }
#Status_revision_requested{ background:#3d2f10; color:#ffd166;
    border-radius:8px; padding:3px 10px; font-size:10.5px;
    font-weight:700; letter-spacing:.5px; }
#Status_accepted          { background:#1a3d2c; color:#86efac;
    border-radius:8px; padding:3px 10px; font-size:10.5px;
    font-weight:700; letter-spacing:.5px; }
#Status_published         { background:#2a2a6a; color:#c7d2fe;
    border-radius:8px; padding:3px 10px; font-size:10.5px;
    font-weight:700; letter-spacing:.5px; }
#Status_rejected          { background:#3d1a1f; color:#fca5a5;
    border-radius:8px; padding:3px 10px; font-size:10.5px;
    font-weight:700; letter-spacing:.5px; }

#Empty { color:#8a93a6; font-size:14px; padding:80px 0; }
QStatusBar { background:#161a21; color:#8a93a6;
    border-top:1px solid #262d3a; }
QStatusBar::item { border: none; }
"""


def qss_for(theme):
    return _DARK if (theme or "").lower() == "dark" else _LIGHT
