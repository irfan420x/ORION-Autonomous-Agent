"""
ORION GUI Core - Theme Engine
==============================

Dark futuristic theme inspired by JARVIS/FRIDAY/Cyberpunk.
All colors, fonts, and styles defined here.
"""


class Colors:
    """Color palette."""
    # Backgrounds
    BG_PRIMARY = "#050510"
    BG_SECONDARY = "#0a0a1a"
    BG_CARD = "#0d1117"
    BG_CARD_HOVER = "#161b22"
    BG_GLASS = "rgba(13, 17, 23, 180)"
    
    # Accents
    CYAN = "#00d4ff"
    CYAN_DIM = "#007a99"
    BLUE = "#0969da"
    GREEN = "#3fb950"
    ORANGE = "#d29922"
    RED = "#f85149"
    PURPLE = "#bc8cff"
    WHITE = "#e6edf3"
    GRAY = "#8b949e"
    BORDER = "#21262d"
    
    # Glow
    GLOW_CYAN = "rgba(0, 212, 255, 60)"
    GLOW_BLUE = "rgba(9, 105, 218, 60)"
    GLOW_GREEN = "rgba(63, 185, 80, 60)"


class Fonts:
    """Font definitions."""
    FAMILY = "Segoe UI"
    FAMILY_MONO = "Consolas"
    
    TITLE = (FAMILY, 24, "bold")
    SUBTITLE = (FAMILY, 16, "bold")
    BODY = (FAMILY, 12)
    SMALL = (FAMILY, 10)
    TINY = (FAMILY, 8)
    MONO = (FAMILY_MONO, 11)


class Sizes:
    """Size constants."""
    WINDOW_WIDTH = 1400
    WINDOW_HEIGHT = 900
    SIDEBAR_WIDTH = 220
    TITLE_BAR_HEIGHT = 40
    DOCK_HEIGHT = 70
    CARD_RADIUS = 12
    BUTTON_RADIUS = 8


class Theme:
    """Complete theme stylesheet."""
    
    MAIN_WINDOW = f"""
        QMainWindow {{
            background-color: {Colors.BG_PRIMARY};
        }}
    """
    
    TITLE_BAR = f"""
        QWidget#titleBar {{
            background-color: {Colors.BG_SECONDARY};
            border-bottom: 1px solid {Colors.BORDER};
        }}
    """
    
    SIDEBAR = f"""
        QWidget#sidebar {{
            background-color: {Colors.BG_SECONDARY};
            border-right: 1px solid {Colors.BORDER};
        }}
    """
    
    NAV_BUTTON = f"""
        QPushButton {{
            background-color: transparent;
            color: {Colors.GRAY};
            border: none;
            text-align: left;
            padding: 12px 20px;
            font-size: 12px;
            font-weight: 500;
            letter-spacing: 1px;
        }}
        QPushButton:hover {{
            background-color: {Colors.BG_CARD};
            color: {Colors.WHITE};
            border-left: 3px solid {Colors.CYAN_DIM};
        }}
        QPushButton:checked {{
            background-color: {Colors.BG_CARD};
            color: {Colors.CYAN};
            border-left: 3px solid {Colors.CYAN};
        }}
    """
    
    CARD = f"""
        QFrame {{
            background-color: {Colors.BG_CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: {Sizes.CARD_RADIUS}px;
        }}
        QFrame:hover {{
            border: 1px solid {Colors.CYAN_DIM};
        }}
    """
    
    LABEL_PRIMARY = f"""
        QLabel {{
            color: {Colors.WHITE};
            background: transparent;
            border: none;
        }}
    """
    
    LABEL_SECONDARY = f"""
        QLabel {{
            color: {Colors.GRAY};
            background: transparent;
            border: none;
            font-size: 10px;
            letter-spacing: 1px;
        }}
    """
    
    LABEL_ACCENT = f"""
        QLabel {{
            color: {Colors.CYAN};
            background: transparent;
            border: none;
        }}
    """
    
    DOCK_BUTTON = f"""
        QPushButton {{
            background-color: {Colors.BG_CARD};
            color: {Colors.WHITE};
            border: 1px solid {Colors.BORDER};
            border-radius: 12px;
            padding: 8px;
            font-size: 18px;
        }}
        QPushButton:hover {{
            background-color: {Colors.BG_CARD_HOVER};
            border: 1px solid {Colors.CYAN_DIM};
        }}
    """
    
    INPUT_FIELD = f"""
        QLineEdit {{
            background-color: {Colors.BG_CARD};
            color: {Colors.WHITE};
            border: 1px solid {Colors.BORDER};
            border-radius: 20px;
            padding: 10px 20px;
            font-size: 13px;
        }}
        QLineEdit:focus {{
            border: 1px solid {Colors.CYAN};
        }}
    """
    
    BADGE_GREEN = f"""
        QLabel {{
            background-color: rgba(63, 185, 80, 40);
            color: {Colors.GREEN};
            border-radius: 4px;
            padding: 2px 8px;
            font-size: 10px;
            font-weight: bold;
        }}
    """
    
    BADGE_ORANGE = f"""
        QLabel {{
            background-color: rgba(210, 153, 34, 40);
            color: {Colors.ORANGE};
            border-radius: 4px;
            padding: 2px 8px;
            font-size: 10px;
            font-weight: bold;
        }}
    """
    
    PROGRESS_BAR = f"""
        QProgressBar {{
            background-color: {Colors.BORDER};
            border: none;
            border-radius: 2px;
            height: 4px;
            text-align: center;
        }}
        QProgressBar::chunk {{
            background-color: {Colors.CYAN};
            border-radius: 2px;
        }}
    """
