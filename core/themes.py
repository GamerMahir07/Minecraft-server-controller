"""core/themes.py — THEMES dict, QSS generator, active theme state"""
import ast, logging, os
from .constants import THEMES_FILE
from .settings import load_settings, update_setting

logger = logging.getLogger(__name__)

THEMES: dict[str, dict] = {
    "Dark (Default)": {"appearance":"dark","bg":"#0d0d0d","card":"#1a1a1a","border":"#2a2a2a","text":"#e0e0e0","muted":"#555555","start":"#22c55e","stop":"#ef4444","sync":"#60a5fa","handoff":"#f59e0b"},
    "Light (Default)": {"appearance":"light","bg":"#f5f5f5","card":"#ffffff","border":"#e0e0e0","text":"#1a1a1a","muted":"#888888","start":"#16a34a","stop":"#dc2626","sync":"#2563eb","handoff":"#d97706"},
    "Midnight Blue Dark": {"appearance":"dark","bg":"#0a0f1e","card":"#111827","border":"#1e3a5f","text":"#e2e8f0","muted":"#4a6080","start":"#34d399","stop":"#f87171","sync":"#818cf8","handoff":"#fbbf24"},
    "Midnight Blue Light": {"appearance":"light","bg":"#e8eeff","card":"#ffffff","border":"#7a9fd4","text":"#0a0f2e","muted":"#5570a0","start":"#059669","stop":"#dc2626","sync":"#4f46e5","handoff":"#d97706"},
    "Creeper Green Dark": {"appearance":"dark","bg":"#0a1a0a","card":"#0f2a0f","border":"#1a4a1a","text":"#c8f0c8","muted":"#3a6a3a","start":"#4ade80","stop":"#f87171","sync":"#86efac","handoff":"#fde047"},
    "Creeper Green Light": {"appearance":"light","bg":"#f0fff0","card":"#ffffff","border":"#86efac","text":"#052e16","muted":"#3a7a3a","start":"#16a34a","stop":"#dc2626","sync":"#059669","handoff":"#ca8a04"},
    "Nether Red Dark": {"appearance":"dark","bg":"#000000","card":"#1a0000","border":"#6a0000","text":"#ff4444","muted":"#8b0000","start":"#ff6b6b","stop":"#ff0000","sync":"#ff8c8c","handoff":"#ffd700"},
    "Nether Red Light": {"appearance":"light","bg":"#fff5f5","card":"#ffffff","border":"#fca5a5","text":"#3a0000","muted":"#b06060","start":"#b91c1c","stop":"#7f1d1d","sync":"#dc2626","handoff":"#c2410c"},
    "Ocean Dark": {"appearance":"dark","bg":"#01131e","card":"#021f30","border":"#0e4a6e","text":"#bae6fd","muted":"#2a6a8a","start":"#22d3ee","stop":"#f87171","sync":"#38bdf8","handoff":"#fbbf24"},
    "Ocean Light": {"appearance":"light","bg":"#e0f7ff","card":"#ffffff","border":"#7dd3f0","text":"#003a52","muted":"#4a8fa8","start":"#0284c7","stop":"#e11d48","sync":"#0ea5e9","handoff":"#f59e0b"},
    "Sunset Dark": {"appearance":"dark","bg":"#1a0a00","card":"#2a1200","border":"#7c3a10","text":"#ffe4c4","muted":"#8a5030","start":"#4ade80","stop":"#f87171","sync":"#c084fc","handoff":"#fb923c"},
    "Sunset Light": {"appearance":"light","bg":"#fff7ed","card":"#ffffff","border":"#fed7aa","text":"#1c0a00","muted":"#9a6030","start":"#16a34a","stop":"#e11d48","sync":"#7c3aed","handoff":"#ea580c"},
    "Obsidian Dark": {"appearance":"dark","bg":"#020202","card":"#070710","border":"#13132a","text":"#cdd6f4","muted":"#3a3a52","start":"#a6e3a1","stop":"#f38ba8","sync":"#89b4fa","handoff":"#fab387"},
    "Obsidian Light": {"appearance":"light","bg":"#f0f0f8","card":"#ffffff","border":"#c5c5e0","text":"#1e1e2e","muted":"#6e7090","start":"#40a02b","stop":"#d20f39","sync":"#1e66f5","handoff":"#e49320"},
    "Ender Night Dark": {"appearance":"dark","bg":"#000000","card":"#0d0010","border":"#3b0060","text":"#e8b4ff","muted":"#6a2a8a","start":"#bf7fff","stop":"#ff5f87","sync":"#d68fff","handoff":"#ffb347"},
    "Ender Night Light": {"appearance":"light","bg":"#f8f0ff","card":"#ffffff","border":"#d4b0ff","text":"#200040","muted":"#7a40a0","start":"#7c3aed","stop":"#db2777","sync":"#6d28d9","handoff":"#c2410c"},
    "Arctic Light": {"appearance":"light","bg":"#eef4fb","card":"#ffffff","border":"#b8d4f0","text":"#0d2137","muted":"#6a90b0","start":"#0ea5e9","stop":"#e11d48","sync":"#6366f1","handoff":"#f59e0b"},
    "Arctic Dark": {"appearance":"dark","bg":"#071520","card":"#0d2035","border":"#1a4060","text":"#dbeafe","muted":"#3a6080","start":"#38bdf8","stop":"#f87171","sync":"#818cf8","handoff":"#fbbf24"},
    "Forest Dark": {"appearance":"dark","bg":"#0d1a0d","card":"#142414","border":"#254025","text":"#d4edda","muted":"#4a7a4a","start":"#86efac","stop":"#fca5a5","sync":"#6ee7b7","handoff":"#fde68a"},
    "Forest Light": {"appearance":"light","bg":"#f0faf0","card":"#ffffff","border":"#a7d7a7","text":"#0a2010","muted":"#4a7a4a","start":"#16a34a","stop":"#dc2626","sync":"#0d9488","handoff":"#ca8a04"},
    "Rose Gold Dark": {"appearance":"dark","bg":"#1a0008","card":"#2a0010","border":"#7a2040","text":"#ffd6e0","muted":"#8a4060","start":"#fb7185","stop":"#f43f5e","sync":"#f472b6","handoff":"#fb923c"},
    "Rose Gold Light": {"appearance":"light","bg":"#fff0f3","card":"#ffffff","border":"#f4c2cb","text":"#3a0a14","muted":"#b06070","start":"#e11d48","stop":"#9f1239","sync":"#db2777","handoff":"#c2410c"},
    "Dracula Dark": {"appearance":"dark","bg":"#282a36","card":"#313442","border":"#44475a","text":"#f8f8f2","muted":"#6272a4","start":"#50fa7b","stop":"#ff5555","sync":"#8be9fd","handoff":"#ffb86c"},
    "Dracula Light": {"appearance":"light","bg":"#f8f8f5","card":"#ffffff","border":"#bdbdcc","text":"#282a36","muted":"#6272a4","start":"#2da44e","stop":"#d0333e","sync":"#0087cc","handoff":"#c47900"},
    "Lava Dark": {"appearance":"dark","bg":"#120500","card":"#1e0a00","border":"#5a1a00","text":"#ffe8d0","muted":"#7a3a10","start":"#ff7c00","stop":"#ff3300","sync":"#ffaa00","handoff":"#ffdd00"},
    "Lava Light": {"appearance":"light","bg":"#fff8f0","card":"#ffffff","border":"#ffc080","text":"#2a0a00","muted":"#a05020","start":"#c2410c","stop":"#b91c1c","sync":"#ea580c","handoff":"#b45309"},
    "Sand Light": {"appearance":"light","bg":"#f5e6c8","card":"#fdf3e0","border":"#c8a96e","text":"#3d2b00","muted":"#8a6a30","start":"#5a8a00","stop":"#c0392b","sync":"#1a6b8a","handoff":"#c07000"},
    "Sand Dark": {"appearance":"dark","bg":"#1a1200","card":"#2a1e00","border":"#7a5a20","text":"#f0dcb0","muted":"#7a6030","start":"#a0c040","stop":"#e05030","sync":"#40a0c0","handoff":"#e0a000"},
    "Void Dark": {"appearance":"dark","bg":"#000000","card":"#0a0a0a","border":"#1a1a1a","text":"#aaaaaa","muted":"#333333","start":"#444444","stop":"#666666","sync":"#555555","handoff":"#777777"},
    "Void Light": {"appearance":"light","bg":"#f0f0f0","card":"#ffffff","border":"#cccccc","text":"#222222","muted":"#999999","start":"#444444","stop":"#888888","sync":"#666666","handoff":"#777777"},
    "Carbon Dark": {"appearance":"dark","bg":"#1a1a2e","card":"#16213e","border":"#0f3460","text":"#e0e0e0","muted":"#4a4a6a","start":"#00c896","stop":"#e94560","sync":"#4d9fff","handoff":"#f5a623"},
    "Carbon Light": {"appearance":"light","bg":"#eef0ff","card":"#ffffff","border":"#8090cc","text":"#0a0a20","muted":"#5060a0","start":"#009966","stop":"#cc2244","sync":"#2266cc","handoff":"#c07000"},
    "Lavender Light": {"appearance":"light","bg":"#f0eeff","card":"#ffffff","border":"#c5b8ff","text":"#1a0050","muted":"#7060a0","start":"#5b21b6","stop":"#db2777","sync":"#4f46e5","handoff":"#d97706"},
    "Lavender Dark": {"appearance":"dark","bg":"#0f0820","card":"#1a1035","border":"#3d2a7a","text":"#e8dfff","muted":"#6050a0","start":"#a78bfa","stop":"#f472b6","sync":"#818cf8","handoff":"#fbbf24"},
    "Mocha Dark": {"appearance":"dark","bg":"#1c1410","card":"#2a1f18","border":"#4a3428","text":"#f0dece","muted":"#7a5a48","start":"#c8a86e","stop":"#e05050","sync":"#90b8d0","handoff":"#e8c060"},
    "Mocha Light": {"appearance":"light","bg":"#fdf6ee","card":"#ffffff","border":"#d4b896","text":"#2a1a0a","muted":"#9a7a60","start":"#7a5a28","stop":"#c0392b","sync":"#2a6080","handoff":"#c07020"},
    "Sakura Light": {"appearance":"light","bg":"#fff0f5","card":"#ffffff","border":"#ffb8cc","text":"#3a0020","muted":"#c06080","start":"#be185d","stop":"#e11d48","sync":"#9d174d","handoff":"#f59e0b"},
    "Sakura Dark": {"appearance":"dark","bg":"#1a0010","card":"#2a0018","border":"#7a2050","text":"#ffd6e8","muted":"#8a4068","start":"#f472b6","stop":"#fb7185","sync":"#e879f9","handoff":"#fbbf24"},
    "Matrix Dark": {"appearance":"dark","bg":"#000000","card":"#001400","border":"#004400","text":"#00ff41","muted":"#006600","start":"#00ff41","stop":"#ff0000","sync":"#00cc33","handoff":"#ffff00"},
    "Matrix Light": {"appearance":"light","bg":"#f0fff0","card":"#ffffff","border":"#80cc80","text":"#002200","muted":"#408040","start":"#166534","stop":"#b91c1c","sync":"#14532d","handoff":"#713f12"},
    "Nord Dark": {"appearance":"dark","bg":"#2e3440","card":"#3b4252","border":"#434c5e","text":"#eceff4","muted":"#4c566a","start":"#a3be8c","stop":"#bf616a","sync":"#88c0d0","handoff":"#ebcb8b"},
    "Nord Light": {"appearance":"light","bg":"#eceff4","card":"#ffffff","border":"#d8dee9","text":"#2e3440","muted":"#7a8898","start":"#4c9a2a","stop":"#bf616a","sync":"#5e81ac","handoff":"#d08770"},
    "Solarized Light": {"appearance":"light","bg":"#fdf6e3","card":"#eee8d5","border":"#93a1a1","text":"#073642","muted":"#657b83","start":"#859900","stop":"#dc322f","sync":"#268bd2","handoff":"#b58900"},
    "Solarized Dark": {"appearance":"dark","bg":"#002b36","card":"#073642","border":"#586e75","text":"#fdf6e3","muted":"#839496","start":"#859900","stop":"#dc322f","sync":"#268bd2","handoff":"#b58900"},
    "Gruvbox Dark": {"appearance":"dark","bg":"#282828","card":"#3c3836","border":"#504945","text":"#ebdbb2","muted":"#7c6f64","start":"#b8bb26","stop":"#fb4934","sync":"#83a598","handoff":"#fabd2f"},
    "Gruvbox Light": {"appearance":"light","bg":"#fbf1c7","card":"#f9f5d7","border":"#d5c4a1","text":"#3c3836","muted":"#928374","start":"#79740e","stop":"#9d0006","sync":"#076678","handoff":"#b57614"},
    "Cyberpunk Dark": {"appearance":"dark","bg":"#0a0014","card":"#110022","border":"#ff00ff","text":"#00ffff","muted":"#8800aa","start":"#00ffff","stop":"#ff0088","sync":"#ff00ff","handoff":"#ffff00"},
    "Cyberpunk Light": {"appearance":"light","bg":"#f0e8ff","card":"#ffffff","border":"#cc44ff","text":"#1a0030","muted":"#8840aa","start":"#0088cc","stop":"#cc0066","sync":"#8800ff","handoff":"#cc8800"},
    "Slate Dark": {"appearance":"dark","bg":"#0f172a","card":"#1e293b","border":"#334155","text":"#f1f5f9","muted":"#64748b","start":"#22d3ee","stop":"#f43f5e","sync":"#818cf8","handoff":"#fb923c"},
    "Slate Light": {"appearance":"light","bg":"#f1f5f9","card":"#ffffff","border":"#cbd5e1","text":"#0f172a","muted":"#64748b","start":"#0891b2","stop":"#e11d48","sync":"#4f46e5","handoff":"#ea580c"},
    "Amber Dark": {"appearance":"dark","bg":"#1a1000","card":"#2a1a00","border":"#7a5500","text":"#ffe88a","muted":"#7a6020","start":"#fbbf24","stop":"#ef4444","sync":"#f59e0b","handoff":"#84cc16"},
    "Amber Light": {"appearance":"light","bg":"#fffbeb","card":"#ffffff","border":"#fde68a","text":"#1c1400","muted":"#9a7a00","start":"#b45309","stop":"#dc2626","sync":"#d97706","handoff":"#65a30d"},
    "Copper Dark": {"appearance":"dark","bg":"#150900","card":"#221200","border":"#7a3a10","text":"#ffcc99","muted":"#7a4a20","start":"#f97316","stop":"#ef4444","sync":"#fb923c","handoff":"#fbbf24"},
    "Copper Light": {"appearance":"light","bg":"#fff8f0","card":"#ffffff","border":"#e0a060","text":"#1a0800","muted":"#a06030","start":"#c2410c","stop":"#b91c1c","sync":"#d97706","handoff":"#65a30d"},
    "CB: Blue & Orange Light": {"appearance":"light","bg":"#f7f7f7","card":"#ffffff","border":"#cccccc","text":"#000000","muted":"#767676","start":"#0072b2","stop":"#d55e00","sync":"#56b4e9","handoff":"#e69f00"},
    "CB: Blue & Orange Dark": {"appearance":"dark","bg":"#111111","card":"#1e1e1e","border":"#333333","text":"#ffffff","muted":"#888888","start":"#56b4e9","stop":"#d55e00","sync":"#0072b2","handoff":"#e69f00"},
    "CB: Green & Purple Light": {"appearance":"light","bg":"#f5f5f5","card":"#ffffff","border":"#cccccc","text":"#000000","muted":"#767676","start":"#009e73","stop":"#cc79a7","sync":"#0072b2","handoff":"#f0e442"},
    "CB: Green & Purple Dark": {"appearance":"dark","bg":"#111111","card":"#1e1e1e","border":"#333333","text":"#eeeeee","muted":"#888888","start":"#009e73","stop":"#cc79a7","sync":"#56b4e9","handoff":"#f0e442"},
    "CB: High Contrast Light": {"appearance":"light","bg":"#ffffff","card":"#f0f0f0","border":"#000000","text":"#000000","muted":"#444444","start":"#0000ff","stop":"#ff0000","sync":"#007700","handoff":"#ff8800"},
    "CB: High Contrast Dark": {"appearance":"dark","bg":"#000000","card":"#1a1a1a","border":"#ffffff","text":"#ffffff","muted":"#aaaaaa","start":"#ffff00","stop":"#ff6600","sync":"#00ffff","handoff":"#ff99ff"},
    "CB: Tol Muted Light": {"appearance":"light","bg":"#f8f4f0","card":"#ffffff","border":"#bbaabb","text":"#221122","muted":"#887799","start":"#44aa99","stop":"#cc6677","sync":"#88ccee","handoff":"#ddcc77"},
    "CB: Tol Muted Dark": {"appearance":"dark","bg":"#221122","card":"#332244","border":"#554466","text":"#eeddff","muted":"#887799","start":"#44aa99","stop":"#cc6677","sync":"#88ccee","handoff":"#ddcc77"},
    "CB: Monochrome Light": {"appearance":"light","bg":"#ffffff","card":"#f0f0f0","border":"#999999","text":"#000000","muted":"#666666","start":"#222222","stop":"#777777","sync":"#444444","handoff":"#555555"},
    "CB: Monochrome Dark": {"appearance":"dark","bg":"#111111","card":"#1e1e1e","border":"#555555","text":"#eeeeee","muted":"#888888","start":"#cccccc","stop":"#888888","sync":"#aaaaaa","handoff":"#bbbbbb"},
    "Pastel Light": {"appearance":"light","bg":"#fdf4ff","card":"#ffffff","border":"#e9d5ff","text":"#3b0764","muted":"#a78bca","start":"#7c3aed","stop":"#e11d48","sync":"#2563eb","handoff":"#d97706"},
    "Pastel Dark": {"appearance":"dark","bg":"#1a0a2e","card":"#2d1b4e","border":"#5b3a8a","text":"#e9d5ff","muted":"#9d7ac0","start":"#a78bfa","stop":"#fb7185","sync":"#60a5fa","handoff":"#fbbf24"},
    "Teal Light": {"appearance":"light","bg":"#eefffe","card":"#ffffff","border":"#80d8d0","text":"#002420","muted":"#4a9a90","start":"#007a70","stop":"#cc2244","sync":"#0066aa","handoff":"#cc8800"},
    "Teal Dark": {"appearance":"dark","bg":"#00100e","card":"#001a18","border":"#00524a","text":"#a0fff5","muted":"#2a7a72","start":"#00d4c0","stop":"#ff4466","sync":"#00aaff","handoff":"#ffcc00"},
    "Peach Light": {"appearance":"light","bg":"#fff8f5","card":"#ffffff","border":"#fed7aa","text":"#431407","muted":"#c47c5a","start":"#c2410c","stop":"#be123c","sync":"#9333ea","handoff":"#ca8a04"},
    "Peach Dark": {"appearance":"dark","bg":"#180a00","card":"#2c1200","border":"#7c2d12","text":"#ffedd5","muted":"#c47c5a","start":"#fb923c","stop":"#f43f5e","sync":"#c084fc","handoff":"#fbbf24"},
    "Sky Light": {"appearance":"light","bg":"#f0f9ff","card":"#ffffff","border":"#bae6fd","text":"#0c4a6e","muted":"#7dd3fc","start":"#0284c7","stop":"#e11d48","sync":"#7c3aed","handoff":"#d97706"},
    "Sky Dark": {"appearance":"dark","bg":"#020d18","card":"#082032","border":"#0c4a6e","text":"#e0f2fe","muted":"#38bdf8","start":"#38bdf8","stop":"#f87171","sync":"#a78bfa","handoff":"#fbbf24"},
    "Lilac Light": {"appearance":"light","bg":"#faf5ff","card":"#ffffff","border":"#e9d5ff","text":"#3b0764","muted":"#c4b5fd","start":"#7c3aed","stop":"#db2777","sync":"#0284c7","handoff":"#d97706"},
    "Lilac Dark": {"appearance":"dark","bg":"#120820","card":"#1e1035","border":"#4c1d95","text":"#ede9fe","muted":"#a78bfa","start":"#c4b5fd","stop":"#f472b6","sync":"#60a5fa","handoff":"#fbbf24"},
    "Honey Light": {"appearance":"light","bg":"#fffbeb","card":"#ffffff","border":"#fde68a","text":"#1c1400","muted":"#d9a22e","start":"#d97706","stop":"#dc2626","sync":"#0284c7","handoff":"#65a30d"},
    "Honey Dark": {"appearance":"dark","bg":"#160e00","card":"#241800","border":"#92400e","text":"#fef3c7","muted":"#d97706","start":"#fbbf24","stop":"#f87171","sync":"#38bdf8","handoff":"#86efac"},
    "Ruby Light": {"appearance":"light","bg":"#fff1f2","card":"#ffffff","border":"#fecdd3","text":"#4c0519","muted":"#fb7185","start":"#be123c","stop":"#dc2626","sync":"#0284c7","handoff":"#d97706"},
    "Ruby Dark": {"appearance":"dark","bg":"#1a0008","card":"#2d000f","border":"#881337","text":"#ffe4e6","muted":"#fb7185","start":"#fb7185","stop":"#ef4444","sync":"#38bdf8","handoff":"#fbbf24"},
    "Jade Light": {"appearance":"light","bg":"#f0fdf4","card":"#ffffff","border":"#bbf7d0","text":"#052e16","muted":"#6ee7b7","start":"#059669","stop":"#dc2626","sync":"#0284c7","handoff":"#d97706"},
    "Jade Dark": {"appearance":"dark","bg":"#011810","card":"#022c1e","border":"#065f46","text":"#d1fae5","muted":"#34d399","start":"#34d399","stop":"#f87171","sync":"#38bdf8","handoff":"#fbbf24"},
    "Dusk Dark": {"appearance":"dark","bg":"#0a0014","card":"#130022","border":"#38006b","text":"#e8d5ff","muted":"#9d74cc","start":"#c084fc","stop":"#f472b6","sync":"#818cf8","handoff":"#fb923c"},
    "Dusk Light": {"appearance":"light","bg":"#f9f0ff","card":"#ffffff","border":"#d8b4fe","text":"#1e0050","muted":"#9d74cc","start":"#7c3aed","stop":"#be185d","sync":"#4f46e5","handoff":"#d97706"},
    "Espresso Dark": {"appearance":"dark","bg":"#100800","card":"#1a1000","border":"#3d2000","text":"#f5e6c8","muted":"#7a5a30","start":"#d4a96e","stop":"#e05050","sync":"#7eb8d0","handoff":"#e8c060"},
    "Espresso Light": {"appearance":"light","bg":"#fdf8f0","card":"#fff9f2","border":"#d4b896","text":"#1c0e00","muted":"#8a6a40","start":"#92400e","stop":"#b91c1c","sync":"#0369a1","handoff":"#b45309"},
    "Steel Light": {"appearance":"light","bg":"#f8fafc","card":"#ffffff","border":"#cbd5e1","text":"#0f172a","muted":"#94a3b8","start":"#0284c7","stop":"#e11d48","sync":"#7c3aed","handoff":"#d97706"},
    "Steel Dark": {"appearance":"dark","bg":"#0d1117","card":"#161b22","border":"#30363d","text":"#e6edf3","muted":"#8b949e","start":"#3fb950","stop":"#f85149","sync":"#58a6ff","handoff":"#d29922"},
    "Cherry Blossom Light": {"appearance":"light","bg":"#fff8fa","card":"#ffffff","border":"#fecdd3","text":"#3d0015","muted":"#f9a8d4","start":"#e11d48","stop":"#be123c","sync":"#db2777","handoff":"#f59e0b"},
    "Cherry Blossom Dark": {"appearance":"dark","bg":"#1a0010","card":"#2d0018","border":"#9f1239","text":"#ffe4e6","muted":"#fda4af","start":"#fb7185","stop":"#f43f5e","sync":"#e879f9","handoff":"#fbbf24"},
    "Glacier Light": {"appearance":"light","bg":"#f0fdff","card":"#ffffff","border":"#a5f3fc","text":"#083344","muted":"#67e8f9","start":"#0891b2","stop":"#e11d48","sync":"#6366f1","handoff":"#f59e0b"},
    "Glacier Dark": {"appearance":"dark","bg":"#001a22","card":"#002e3a","border":"#164e63","text":"#cffafe","muted":"#22d3ee","start":"#22d3ee","stop":"#f87171","sync":"#818cf8","handoff":"#fbbf24"},
    "Tangerine Light": {"appearance":"light","bg":"#fff7ed","card":"#ffffff","border":"#fed7aa","text":"#1c0a00","muted":"#fb923c","start":"#ea580c","stop":"#dc2626","sync":"#0284c7","handoff":"#65a30d"},
    "Tangerine Dark": {"appearance":"dark","bg":"#1a0800","card":"#2c1200","border":"#c2410c","text":"#ffedd5","muted":"#fb923c","start":"#fb923c","stop":"#ef4444","sync":"#38bdf8","handoff":"#86efac"},
    "Parchment Light": {"appearance":"light","bg":"#fdf8ee","card":"#fef9f0","border":"#d6c89a","text":"#2a1e00","muted":"#a08840","start":"#7a5a00","stop":"#b91c1c","sync":"#0369a1","handoff":"#b45309"},
    "Parchment Dark": {"appearance":"dark","bg":"#15100a","card":"#201a10","border":"#5a4820","text":"#f0e4c0","muted":"#8a7040","start":"#d4aa60","stop":"#e05050","sync":"#70a8c0","handoff":"#d4aa30"},
    "Volcanic Dark": {"appearance":"dark","bg":"#0a0000","card":"#160000","border":"#7f1d1d","text":"#fecaca","muted":"#991b1b","start":"#ef4444","stop":"#f97316","sync":"#fbbf24","handoff":"#a3e635"},
    "Volcanic Light": {"appearance":"light","bg":"#fff5f5","card":"#ffffff","border":"#fca5a5","text":"#1a0000","muted":"#ef4444","start":"#dc2626","stop":"#c2410c","sync":"#d97706","handoff":"#65a30d"},
    "Deep Sea Dark": {"appearance":"dark","bg":"#000d1a","card":"#001a33","border":"#003366","text":"#b3d9ff","muted":"#336699","start":"#0066cc","stop":"#cc0033","sync":"#00aacc","handoff":"#ffaa00"},
    "Deep Sea Light": {"appearance":"light","bg":"#e8f4ff","card":"#ffffff","border":"#99c9f5","text":"#001433","muted":"#6699cc","start":"#0066cc","stop":"#cc0033","sync":"#0099bb","handoff":"#cc8800"},
    "Bubblegum Light": {"appearance":"light","bg":"#fff0fa","card":"#ffffff","border":"#f9a8d4","text":"#2d0025","muted":"#f472b6","start":"#ec4899","stop":"#e11d48","sync":"#8b5cf6","handoff":"#f59e0b"},
    "Bubblegum Dark": {"appearance":"dark","bg":"#1a0016","card":"#2d0026","border":"#9d174d","text":"#fce7f3","muted":"#f472b6","start":"#f472b6","stop":"#fb7185","sync":"#c084fc","handoff":"#fbbf24"},
    "programmer Green Dark": {"appearance":"dark","bg":"#000000","card":"#000d00","border":"#003b00","text":"#b4ffb4","muted":"#2a6a2a","start":"#7fff7f","stop":"#ff5f87","sync":"#7dff8f","handoff":"#ffb347"},
    "programmer Green Light": {"appearance":"light","bg":"#f0fff0","card":"#ffffff","border":"#b0d4b0","text":"#002000","muted":"#408040","start":"#276327","stop":"#db2777","sync":"#2d7a2d","handoff":"#c2410c"},
    "Midnight Purple Dark": {"appearance":"dark","bg":"#05000f","card":"#0d0020","border":"#4c1d95","text":"#ede9fe","muted":"#7c3aed","start":"#a78bfa","stop":"#f472b6","sync":"#818cf8","handoff":"#fbbf24"},
    "Midnight Purple Light": {"appearance":"light","bg":"#faf5ff","card":"#ffffff","border":"#c4b5fd","text":"#1e0050","muted":"#7c3aed","start":"#6d28d9","stop":"#be185d","sync":"#4f46e5","handoff":"#d97706"},
    "Cinnamon Light": {"appearance":"light","bg":"#fdf5ee","card":"#ffffff","border":"#d4a57a","text":"#2a1200","muted":"#a0622a","start":"#9a3412","stop":"#b91c1c","sync":"#0369a1","handoff":"#b45309"},
    "Cinnamon Dark": {"appearance":"dark","bg":"#180900","card":"#281400","border":"#92400e","text":"#fde8d0","muted":"#c47c4a","start":"#f97316","stop":"#ef4444","sync":"#38bdf8","handoff":"#fbbf24"},
    "Petal Light": {"appearance":"light","bg":"#fef9ff","card":"#ffffff","border":"#f0abfc","text":"#3b0764","muted":"#e879f9","start":"#a21caf","stop":"#e11d48","sync":"#7c3aed","handoff":"#d97706"},
    "Petal Dark": {"appearance":"dark","bg":"#1a0020","card":"#2a0035","border":"#701a75","text":"#fae8ff","muted":"#e879f9","start":"#d946ef","stop":"#f43f5e","sync":"#818cf8","handoff":"#fbbf24"},
    "Golden Hour Light": {"appearance":"light","bg":"#fffbf0","card":"#ffffff","border":"#fde68a","text":"#1c1200","muted":"#d9a520","start":"#b45309","stop":"#dc2626","sync":"#7c3aed","handoff":"#65a30d"},
    "Golden Hour Dark": {"appearance":"dark","bg":"#130e00","card":"#201600","border":"#854d0e","text":"#fefce8","muted":"#d97706","start":"#eab308","stop":"#f87171","sync":"#c084fc","handoff":"#86efac"},
    "Neon Nights Dark": {"appearance":"dark","bg":"#050010","card":"#0d0020","border":"#330066","text":"#e8d0ff","muted":"#6600cc","start":"#cc00ff","stop":"#ff0066","sync":"#00ffcc","handoff":"#ffcc00"},
    "Neon Nights Light": {"appearance":"light","bg":"#f5f0ff","card":"#ffffff","border":"#cc99ff","text":"#1a0040","muted":"#8844cc","start":"#7c00cc","stop":"#cc0055","sync":"#008866","handoff":"#997700"},
    "Tundra Light": {"appearance":"light","bg":"#f5f8fa","card":"#ffffff","border":"#b0c4cc","text":"#1a2530","muted":"#7a9aaa","start":"#1d6a8a","stop":"#c0392b","sync":"#2c7a4b","handoff":"#c07a00"},
    "Tundra Dark": {"appearance":"dark","bg":"#0a1218","card":"#111e26","border":"#1e3a4a","text":"#d4e8f0","muted":"#4a7a8a","start":"#4ab8d8","stop":"#e05060","sync":"#4ac880","handoff":"#e8c050"},
    "Autumn Light": {"appearance":"light","bg":"#fdf7f0","card":"#ffffff","border":"#d4a87a","text":"#2a1400","muted":"#a07040","start":"#c05010","stop":"#c0392b","sync":"#2c6080","handoff":"#c08020"},
    "Autumn Dark": {"appearance":"dark","bg":"#180a00","card":"#281400","border":"#8b4513","text":"#ffecd0","muted":"#b06030","start":"#e07030","stop":"#e05050","sync":"#50a0c0","handoff":"#e0b020"},
    "Abyss Dark": {"appearance":"dark","bg":"#000408","card":"#00080f","border":"#001a33","text":"#80c8ff","muted":"#004488","start":"#0080ff","stop":"#ff2244","sync":"#00ccaa","handoff":"#ffaa00"},
    "Abyss Light": {"appearance":"light","bg":"#f0f8ff","card":"#ffffff","border":"#80b8e8","text":"#000810","muted":"#4488bb","start":"#0066cc","stop":"#cc2233","sync":"#008877","handoff":"#bb8800"},
    "Hazel Light": {"appearance":"light","bg":"#faf8f5","card":"#ffffff","border":"#c8b89a","text":"#2a2015","muted":"#8a7a60","start":"#5a4020","stop":"#b91c1c","sync":"#1d4ed8","handoff":"#b45309"},
    "Hazel Dark": {"appearance":"dark","bg":"#141008","card":"#1e1810","border":"#5a4830","text":"#ecdcc8","muted":"#8a7050","start":"#d0a870","stop":"#e05050","sync":"#60a0d0","handoff":"#d8b040"},
    "Deep Space Dark": {"appearance":"dark","bg":"#00000a","card":"#00000f","border":"#0a0a2a","text":"#c8c8ff","muted":"#4444aa","start":"#6688ff","stop":"#ff4466","sync":"#44ddff","handoff":"#ffcc44"},
    "Deep Space Light": {"appearance":"light","bg":"#f0f0ff","card":"#ffffff","border":"#9090cc","text":"#00001a","muted":"#5555aa","start":"#3344cc","stop":"#cc2244","sync":"#0088cc","handoff":"#aa7700"},
    "Moss Light": {"appearance":"light","bg":"#f4f9f0","card":"#ffffff","border":"#a0c090","text":"#0f2010","muted":"#607850","start":"#3a6030","stop":"#c0392b","sync":"#1d6080","handoff":"#b08020"},
    "Moss Dark": {"appearance":"dark","bg":"#0a1208","card":"#101e0e","border":"#204020","text":"#d0e8c0","muted":"#608050","start":"#70c050","stop":"#e05050","sync":"#50a0c0","handoff":"#d0b840"},
    "Tokyonight Dark": {"appearance":"dark","bg":"#1a1b2e","card":"#16213e","border":"#0f3460","text":"#a9b1d6","muted":"#414868","start":"#73daca","stop":"#f7768e","sync":"#7aa2f7","handoff":"#ff9e64"},
    "Tokyonight Light": {"appearance":"light","bg":"#d5d6db","card":"#ffffff","border":"#a8aecb","text":"#343b58","muted":"#9699a6","start":"#33635c","stop":"#8c4351","sync":"#34548a","handoff":"#8f5e15"},
    "Frostbite Dark": {"appearance":"dark","bg":"#050f1a","card":"#0a1e2e","border":"#1a4060","text":"#e0f8ff","muted":"#3080aa","start":"#00c8ff","stop":"#ff4488","sync":"#88ddff","handoff":"#ffdd44"},
    "Frostbite Light": {"appearance":"light","bg":"#e8f8ff","card":"#ffffff","border":"#88ccee","text":"#001830","muted":"#4499bb","start":"#0088cc","stop":"#cc2266","sync":"#5588ff","handoff":"#cc9900"},
    "Ultra White Light": {"appearance":"light","bg":"#ffffff","card":"#ffffff","border":"#eeeeee","text":"#000000","muted":"#bbbbbb","start":"#000000","stop":"#ff0000","sync":"#444444","handoff":"#ff8800"},
    "Ultra Black Dark": {"appearance":"dark","bg":"#000000","card":"#050505","border":"#0f0f0f","text":"#ffffff","muted":"#333333","start":"#ffffff","stop":"#ff0000","sync":"#aaaaaa","handoff":"#ffff00"},
    "Abyss Dark": {"appearance":"dark","bg":"#05050a","card":"#0a0a14","border":"#15151f","text":"#e8e8f0","muted":"#727278","start":"#00d4aa","stop":"#ff4466","sync":"#7b68ee","handoff":"#ff9900"},
    "Void Black Dark": {"appearance":"dark","bg":"#000000","card":"#0a0a0a","border":"#1a1a1a","text":"#e8e8f0","muted":"#757575","start":"#39ff14","stop":"#ff2020","sync":"#00bfff","handoff":"#ffd700"},
    "Carbon Dark": {"appearance":"dark","bg":"#0d0d0d","card":"#141414","border":"#222222","text":"#e8e8f0","muted":"#7a7a7a","start":"#64ffda","stop":"#ff5370","sync":"#82aaff","handoff":"#ffcb6b"},
    "Pitch Dark": {"appearance":"dark","bg":"#070708","card":"#0f0f12","border":"#1c1c22","text":"#e8e8f0","muted":"#76767a","start":"#a8ff78","stop":"#ff6b6b","sync":"#78dbff","handoff":"#ffd460"},
    "Obsidian II Dark": {"appearance":"dark","bg":"#0c0c10","card":"#131318","border":"#202028","text":"#e8e8f0","muted":"#79797e","start":"#50fa7b","stop":"#ff5555","sync":"#8be9fd","handoff":"#ffb86c"},
    "Phantom Dark": {"appearance":"dark","bg":"#080810","card":"#0e0e18","border":"#1a1a28","text":"#e8e8f0","muted":"#75757e","start":"#00ff87","stop":"#ff3366","sync":"#00b4d8","handoff":"#ff9f1c"},
    "Slate Dark Dark": {"appearance":"dark","bg":"#0e1117","card":"#161b22","border":"#21262d","text":"#e8e8f0","muted":"#797c81","start":"#3fb950","stop":"#f85149","sync":"#58a6ff","handoff":"#d29922"},
    "Ink Dark": {"appearance":"dark","bg":"#06070a","card":"#0d0f14","border":"#181c25","text":"#e8e8f0","muted":"#74767c","start":"#4dffb4","stop":"#ff4d4d","sync":"#4dc3ff","handoff":"#ffcc00"},
    "Onyx Dark": {"appearance":"dark","bg":"#0a0a0b","card":"#121213","border":"#1e1e20","text":"#e8e8f0","muted":"#787879","start":"#00e676","stop":"#ff1744","sync":"#40c4ff","handoff":"#ffab40"},
    "Graphite Dark Dark": {"appearance":"dark","bg":"#111114","card":"#18181c","border":"#242428","text":"#e8e8f0","muted":"#7b7b7e","start":"#69ff47","stop":"#ff3d00","sync":"#18ffff","handoff":"#ffea00"},
    "Noir Dark": {"appearance":"dark","bg":"#060608","card":"#0e0e12","border":"#18181e","text":"#e8e8f0","muted":"#747478","start":"#39ffb0","stop":"#ff2d55","sync":"#5ac8fa","handoff":"#ff9500"},
    "Eclipse Dark Dark": {"appearance":"dark","bg":"#0a0b10","card":"#12131a","border":"#1e2030","text":"#e8e8f0","muted":"#787982","start":"#7fff00","stop":"#ff4500","sync":"#00e5ff","handoff":"#ff6d00"},
    "Shadow Dark": {"appearance":"dark","bg":"#09090c","card":"#111115","border":"#1c1c22","text":"#e8e8f0","muted":"#76767a","start":"#00ffa3","stop":"#ff0055","sync":"#00b0ff","handoff":"#ff6e00"},
    "Raven Dark": {"appearance":"dark","bg":"#080a0e","card":"#101318","border":"#1c2030","text":"#e8e8f0","muted":"#767982","start":"#54d62c","stop":"#ff4842","sync":"#74caff","handoff":"#ffd666"},
    "Midnight II Dark": {"appearance":"dark","bg":"#050812","card":"#0c1020","border":"#141c30","text":"#e8e8f0","muted":"#727682","start":"#6effb4","stop":"#ff4d6d","sync":"#56cfe1","handoff":"#ffbe0b"},
    "Deep Space Dark": {"appearance":"dark","bg":"#020408","card":"#060c14","border":"#101820","text":"#e8e8f0","muted":"#6f7479","start":"#00ff9f","stop":"#ff003f","sync":"#00e5ff","handoff":"#ffaa00"},
    "Charcoal Dark": {"appearance":"dark","bg":"#141414","card":"#1c1c1c","border":"#2a2a2a","text":"#e8e8f0","muted":"#7f7f7f","start":"#73d13d","stop":"#ff4d4f","sync":"#40a9ff","handoff":"#ffa940"},
    "Magnetite Dark": {"appearance":"dark","bg":"#0d0f11","card":"#151819","border":"#202428","text":"#e8e8f0","muted":"#797b7e","start":"#4ade80","stop":"#f87171","sync":"#60a5fa","handoff":"#fb923c"},
    "Dark Matter Dark": {"appearance":"dark","bg":"#030305","card":"#08080e","border":"#111118","text":"#e8e8f0","muted":"#707074","start":"#22d3ee","stop":"#fb7185","sync":"#818cf8","handoff":"#fbbf24"},
    "Iron Dark Dark": {"appearance":"dark","bg":"#0e0e0e","card":"#161616","border":"#242424","text":"#e8e8f0","muted":"#7b7b7b","start":"#52c41a","stop":"#ff4d4f","sync":"#1890ff","handoff":"#faad14"},
    "Parchment Light": {"appearance":"light","bg":"#f8f4ee","card":"#fffdf8","border":"#e8e0d4","text":"#1a1a2a","muted":"#122118109","start":"#1a1a2e","stop":"#c0392b","sync":"#2980b9","handoff":"#e67e22"},
    "Snow Light": {"appearance":"light","bg":"#f8f9fa","card":"#ffffff","border":"#dee2e6","text":"#1a1a2a","muted":"#11511a11f","start":"#2d6a2d","stop":"#c0392b","sync":"#1565c0","handoff":"#e65100"},
    "Cream Light": {"appearance":"light","bg":"#fdf6e3","card":"#fffef9","border":"#e8dcc8","text":"#1a1a2a","muted":"#122113fa","start":"#276749","stop":"#e53e3e","sync":"#2b6cb0","handoff":"#dd6b20"},
    "Linen Light": {"appearance":"light","bg":"#f5f0e8","card":"#fffefa","border":"#ddd5c8","text":"#1a1a2a","muted":"#11410afa","start":"#2a5f2a","stop":"#c53030","sync":"#2c5282","handoff":"#c05621"},
    "Pearl Light": {"appearance":"light","bg":"#f0f0f5","card":"#ffffff","border":"#d8d8e8","text":"#1a1a2a","muted":"#10e10e122","start":"#1a4731","stop":"#9b2c2c","sync":"#1a365d","handoff":"#7b341e"},
    "Ivory Light": {"appearance":"light","bg":"#fffff0","card":"#fffff8","border":"#e8e8d0","text":"#1a1a2a","muted":"#122122104","start":"#22543d","stop":"#c53030","sync":"#2a4365","handoff":"#c05621"},
    "Mist Light": {"appearance":"light","bg":"#f0f4f8","card":"#ffffff","border":"#d4dde6","text":"#1a1a2a","muted":"#10911411f","start":"#276749","stop":"#c53030","sync":"#2c5282","handoff":"#c05621"},
    "Cloud Light": {"appearance":"light","bg":"#f7f9fc","card":"#ffffff","border":"#dde4ed","text":"#1a1a2a","muted":"#11411d128","start":"#2f855a","stop":"#c53030","sync":"#2b6cb0","handoff":"#c05621"},
    "Seashell Light": {"appearance":"light","bg":"#fff5ee","card":"#ffffff","border":"#ead5c8","text":"#1a1a2a","muted":"#12410afa","start":"#285e61","stop":"#9b2c2c","sync":"#2c5282","handoff":"#7b341e"},
    "Antique Light": {"appearance":"light","bg":"#faebd7","card":"#fffef0","border":"#e0cdb0","text":"#1a1a2a","muted":"#118100dc","start":"#22543d","stop":"#c53030","sync":"#2a4365","handoff":"#c05621"},
    "Cobalt Dark": {"appearance":"dark","bg":"#0a0f1a","card":"#101828","border":"#1a2840","text":"#e8f4fd","muted":"#607060","start":"#0ea5e9","stop":"#f59e0b","sync":"#22d3ee","handoff":"#fb923c"},
    "Copper Dark": {"appearance":"dark","bg":"#110d08","card":"#1a1208","border":"#2a1e10","text":"#f5e6d8","muted":"#807060","start":"#c87941","stop":"#ef4444","sync":"#f97316","handoff":"#fbbf24"},
    "Amethyst Dark": {"appearance":"dark","bg":"#0e0814","card":"#150c1e","border":"#221430","text":"#ede0f8","muted":"#706090","start":"#a855f7","stop":"#f43f5e","sync":"#c084fc","handoff":"#fb923c"},
    "Sapphire Dark": {"appearance":"dark","bg":"#081018","card":"#0e1824","border":"#162538","text":"#deeaf5","muted":"#506080","start":"#3b82f6","stop":"#ef4444","sync":"#60a5fa","handoff":"#f59e0b"},
    "Ruby Dark": {"appearance":"dark","bg":"#140810","card":"#1e0c18","border":"#301424","text":"#f8e0ec","muted":"#907080","start":"#ec4899","stop":"#ef4444","sync":"#f472b6","handoff":"#fb923c"},
    "Emerald Dark": {"appearance":"dark","bg":"#08140e","card":"#0c1e12","border":"#143020","text":"#e0f5ea","muted":"#608070","start":"#10b981","stop":"#ef4444","sync":"#34d399","handoff":"#fbbf24"},
    "Topaz Dark": {"appearance":"dark","bg":"#100e08","card":"#181408","border":"#281e10","text":"#f5f0e0","muted":"#807870","start":"#f59e0b","stop":"#ef4444","sync":"#fcd34d","handoff":"#fb923c"},
    "Jade Dark": {"appearance":"dark","bg":"#081210","card":"#0e1a18","border":"#142824","text":"#e0f0ee","muted":"#607870","start":"#0d9488","stop":"#ef4444","sync":"#14b8a6","handoff":"#fbbf24"},
    "Coral Dark": {"appearance":"dark","bg":"#140c0a","card":"#1e1210","border":"#301c18","text":"#f5e8e0","muted":"#907870","start":"#f97316","stop":"#ef4444","sync":"#fb923c","handoff":"#fbbf24"},
    "Lilac Dark": {"appearance":"dark","bg":"#0e0c14","card":"#141218","border":"#201830","text":"#ede8f5","muted":"#706890","start":"#8b5cf6","stop":"#f43f5e","sync":"#a78bfa","handoff":"#fbbf24"},
    "Teal Dark": {"appearance":"dark","bg":"#081214","card":"#0e1c1e","border":"#142830","text":"#dff0f2","muted":"#507880","start":"#0891b2","stop":"#ef4444","sync":"#22d3ee","handoff":"#f59e0b"},
    "Rose Dark": {"appearance":"dark","bg":"#14080e","card":"#1e0e16","border":"#301420","text":"#f5e0ea","muted":"#908090","start":"#e11d48","stop":"#b91c1c","sync":"#fb7185","handoff":"#fb923c"},
    "Gold Dark": {"appearance":"dark","bg":"#12100a","card":"#1c1808","border":"#2c2410","text":"#f5f0e0","muted":"#908070","start":"#d97706","stop":"#ef4444","sync":"#fbbf24","handoff":"#fb923c"},
    "Maroon Dark": {"appearance":"dark","bg":"#12080a","card":"#1c0e12","border":"#2c1418","text":"#f5e0e4","muted":"#907880","start":"#be123c","stop":"#b91c1c","sync":"#fb7185","handoff":"#fbbf24"},
    "Indigo Dark": {"appearance":"dark","bg":"#0a0c18","card":"#10141e","border":"#181c2c","text":"#e4e8f5","muted":"#607080","start":"#4f46e5","stop":"#ef4444","sync":"#818cf8","handoff":"#f59e0b"},
    "Forest Dark": {"appearance":"dark","bg":"#08120a","card":"#0e1c10","border":"#142a18","text":"#e0f0e4","muted":"#608068","start":"#16a34a","stop":"#ef4444","sync":"#4ade80","handoff":"#fbbf24"},
    "Ocean Dark": {"appearance":"dark","bg":"#080e14","card":"#0e1820","border":"#141e30","text":"#dce8f5","muted":"#607080","start":"#0284c7","stop":"#ef4444","sync":"#38bdf8","handoff":"#f59e0b"},
    "Sunset Dark": {"appearance":"dark","bg":"#14100a","card":"#1e1810","border":"#301e10","text":"#f5eada","muted":"#908068","start":"#ea580c","stop":"#dc2626","sync":"#fb923c","handoff":"#fbbf24"},
    "Neon Dark": {"appearance":"dark","bg":"#05050a","card":"#08081a","border":"#10102a","text":"#e8e8ff","muted":"#606090","start":"#00ff41","stop":"#ff0040","sync":"#00d4ff","handoff":"#ffee00"},
    "Matrix Dark": {"appearance":"dark","bg":"#000a00","card":"#001200","border":"#001e00","text":"#c0ffc0","muted":"#408040","start":"#00ff41","stop":"#ff4444","sync":"#00cc33","handoff":"#88ff00"},
    "Arctic Dark": {"appearance":"dark","bg":"#0a0e14","card":"#10161e","border":"#181e28","text":"#dce8f8","muted":"#607080","start":"#0ea5e9","stop":"#ef4444","sync":"#7dd3fc","handoff":"#fbbf24"},
    "Slate Blue": {"appearance":"dark","bg":"#0a0c14","card":"#10141e","border":"#181c2a","text":"#e0e4f0","muted":"#606880","start":"#6366f1","stop":"#ef4444","sync":"#818cf8","handoff":"#f59e0b"},
    "Dark Chocolate": {"appearance":"dark","bg":"#0e0a08","card":"#18100c","border":"#281812","text":"#f0e8e0","muted":"#807068","start":"#92400e","stop":"#b91c1c","sync":"#d97706","handoff":"#fbbf24"},
    "Ink Blue": {"appearance":"dark","bg":"#080c14","card":"#0e1420","border":"#141c30","text":"#dce4f5","muted":"#506078","start":"#1d4ed8","stop":"#dc2626","sync":"#60a5fa","handoff":"#f59e0b"},
    "Dark Plum": {"appearance":"dark","bg":"#10080e","card":"#180c18","border":"#281220","text":"#f0e0f0","muted":"#807090","start":"#7e22ce","stop":"#be123c","sync":"#c084fc","handoff":"#fbbf24"},
    "Dark Teal": {"appearance":"dark","bg":"#081012","card":"#0e181c","border":"#142428","text":"#e0eeee","muted":"#507878","start":"#0f766e","stop":"#dc2626","sync":"#2dd4bf","handoff":"#fbbf24"},
    "Deep Navy": {"appearance":"dark","bg":"#040812","card":"#080e1c","border":"#10182a","text":"#d8e4f5","muted":"#486080","start":"#1e40af","stop":"#dc2626","sync":"#3b82f6","handoff":"#f59e0b"},
    "Dark Grape": {"appearance":"dark","bg":"#0c080e","card":"#140c18","border":"#20122a","text":"#ece0f8","muted":"#706090","start":"#6d28d9","stop":"#dc2626","sync":"#8b5cf6","handoff":"#fbbf24"},
    "Dark Moss": {"appearance":"dark","bg":"#0a0e08","card":"#121c10","border":"#1a2a18","text":"#e0ecd8","muted":"#608060","start":"#3f6212","stop":"#dc2626","sync":"#65a30d","handoff":"#fbbf24"},
    "Dark Burgundy": {"appearance":"dark","bg":"#0e0808","card":"#180e0e","border":"#2a1414","text":"#f0e0e0","muted":"#807070","start":"#881337","stop":"#b91c1c","sync":"#e11d48","handoff":"#fbbf24"},
    "Dark Gunmetal": {"appearance":"dark","bg":"#0c0e10","card":"#141618","border":"#1e2022","text":"#e0e4e8","muted":"#607078","start":"#374151","stop":"#dc2626","sync":"#6b7280","handoff":"#fbbf24"},
    "Dark Sienna": {"appearance":"dark","bg":"#100a06","card":"#1a1008","border":"#28180c","text":"#f0e8d8","muted":"#806860","start":"#92400e","stop":"#b91c1c","sync":"#c2410c","handoff":"#fbbf24"},
    "Dark Byzantium": {"appearance":"dark","bg":"#0c0810","card":"#141018","border":"#201828","text":"#f0e4f8","muted":"#806890","start":"#4a044e","stop":"#dc2626","sync":"#86198f","handoff":"#fbbf24"},
    "Dark Viridian": {"appearance":"dark","bg":"#081010","card":"#0e1818","border":"#142020","text":"#dff5f0","muted":"#507870","start":"#065f46","stop":"#dc2626","sync":"#059669","handoff":"#fbbf24"},
    "Dark Crimson": {"appearance":"dark","bg":"#0e0606","card":"#180a0a","border":"#2a1010","text":"#f5e0e0","muted":"#907070","start":"#7f1d1d","stop":"#dc2626","sync":"#ef4444","handoff":"#fbbf24"},
    "Dark Azure": {"appearance":"dark","bg":"#080c12","card":"#0e1420","border":"#141e2e","text":"#dce8f8","muted":"#506080","start":"#1e3a5f","stop":"#dc2626","sync":"#2563eb","handoff":"#fbbf24"},
    "Cyberpunk": {"appearance":"dark","bg":"#050515","card":"#0a0a24","border":"#10102a","text":"#f0f0ff","muted":"#606090","start":"#ff00ff","stop":"#ff0000","sync":"#00ffff","handoff":"#ffff00"},
    "Hack Dark": {"appearance":"dark","bg":"#030303","card":"#080808","border":"#141414","text":"#33ff33","muted":"#1a4d1a","start":"#33ff33","stop":"#ff3333","sync":"#33ccff","handoff":"#ffcc00"},
    "Synthwave": {"appearance":"dark","bg":"#0a0510","card":"#140818","border":"#1e0f28","text":"#f8e8ff","muted":"#706080","start":"#ff71ce","stop":"#ff4466","sync":"#01cdfe","handoff":"#fffb96"},
    "Vaporwave": {"appearance":"dark","bg":"#0a0818","card":"#10101e","border":"#181428","text":"#ffccff","muted":"#888090","start":"#ff77ff","stop":"#ff4477","sync":"#77ffee","handoff":"#ffcc44"},
    "Retrowave": {"appearance":"dark","bg":"#0c0510","card":"#180a18","border":"#240f24","text":"#ffd6ff","muted":"#806080","start":"#ff44cc","stop":"#ff2244","sync":"#44eeff","handoff":"#ffdd44"},
    "Lo-fi Dark": {"appearance":"dark","bg":"#0a0c12","card":"#12141e","border":"#1c1e2a","text":"#e0e4f0","muted":"#687090","start":"#7c83bc","stop":"#e57373","sync":"#90caf9","handoff":"#ffcc80"},
    "Pastel Dark": {"appearance":"dark","bg":"#0e0e12","card":"#16161c","border":"#202026","text":"#f0e8f8","muted":"#787090","start":"#c084fc","stop":"#fb7185","sync":"#67e8f9","handoff":"#fde68a"},
    "Nord Night": {"appearance":"dark","bg":"#1a1e2a","card":"#20263a","border":"#2e3a50","text":"#eceff4","muted":"#6070a0","start":"#a3be8c","stop":"#bf616a","sync":"#88c0d0","handoff":"#ebcb8b"},
    "Dracula++": {"appearance":"dark","bg":"#1e1e2e","card":"#282840","border":"#3a3a55","text":"#f8f8f2","muted":"#807890","start":"#50fa7b","stop":"#ff5555","sync":"#8be9fd","handoff":"#ffb86c"},
    "Gruvbox Dark": {"appearance":"dark","bg":"#282828","card":"#3c3836","border":"#504945","text":"#ebdbb2","muted":"#a89984","start":"#b8bb26","stop":"#cc241d","sync":"#83a598","handoff":"#fe8019"},
    "Material Dark": {"appearance":"dark","bg":"#212121","card":"#2d2d2d","border":"#424242","text":"#ffffff","muted":"#9e9e9e","start":"#80cbc4","stop":"#ef9a9a","sync":"#90caf9","handoff":"#ffcc02"},
    "Monokai Dark": {"appearance":"dark","bg":"#272822","card":"#3e3d32","border":"#4e4d43","text":"#f8f8f2","muted":"#8f908a","start":"#a6e22e","stop":"#f92672","sync":"#66d9e8","handoff":"#fd971f"},
    "Solarized Dark": {"appearance":"dark","bg":"#002b36","card":"#073642","border":"#094052","text":"#839496","muted":"#657b83","start":"#859900","stop":"#dc322f","sync":"#268bd2","handoff":"#b58900"},
    "One Dark Pro": {"appearance":"dark","bg":"#282c34","card":"#31363f","border":"#4b5263","text":"#abb2bf","muted":"#5c6370","start":"#98c379","stop":"#e06c75","sync":"#61afef","handoff":"#d19a66"},
    "Catppuccin": {"appearance":"dark","bg":"#1e1e2e","card":"#24273a","border":"#363a4f","text":"#cad3f5","muted":"#6e738d","start":"#a6e3a1","stop":"#ed8796","sync":"#8aadf4","handoff":"#f5a97f"},
    "Tokyo Night": {"appearance":"dark","bg":"#1a1b26","card":"#24283b","border":"#2f3549","text":"#c0caf5","muted":"#565f89","start":"#9ece6a","stop":"#f7768e","sync":"#7aa2f7","handoff":"#ff9e64"},
    "Everforest Dark": {"appearance":"dark","bg":"#2d353b","card":"#343f44","border":"#475258","text":"#d3c6aa","muted":"#7a8478","start":"#a7c080","stop":"#e67e80","sync":"#7fbbb3","handoff":"#dbbc7f"},
    "Kanagawa": {"appearance":"dark","bg":"#1f1f28","card":"#2a2a37","border":"#363646","text":"#dcd7ba","muted":"#727169","start":"#76946a","stop":"#c34043","sync":"#7e9cd8","handoff":"#ffa066"},
    "Rosé Pine": {"appearance":"dark","bg":"#191724","card":"#1f1d2e","border":"#2a283e","text":"#e0def4","muted":"#6e6a86","start":"#9ccfd8","stop":"#eb6f92","sync":"#c4a7e7","handoff":"#f6c177"},
    "Ayu Dark": {"appearance":"dark","bg":"#0a0e14","card":"#0d1017","border":"#151b22","text":"#bfbdb6","muted":"#4d5566","start":"#7fd962","stop":"#f07178","sync":"#59c2ff","handoff":"#ffb454"},
    "Nightowl": {"appearance":"dark","bg":"#011627","card":"#0d2238","border":"#1d3a50","text":"#d6deeb","muted":"#637777","start":"#addb67","stop":"#ef5350","sync":"#82aaff","handoff":"#ffcb8b"},
    "Solarized Light": {"appearance":"light","bg":"#fdf6e3","card":"#eee8d5","border":"#d3cdb4","text":"#657b83","muted":"#93a1a1","start":"#859900","stop":"#dc322f","sync":"#268bd2","handoff":"#b58900"},
    "Gruvbox Light": {"appearance":"light","bg":"#fbf1c7","card":"#f2e5bc","border":"#d5c4a1","text":"#3c3836","muted":"#7c6f64","start":"#b57614","stop":"#9d0006","sync":"#076678","handoff":"#d65d0e"},
    "One Light": {"appearance":"light","bg":"#fafafa","card":"#f0f0f0","border":"#d8d8d8","text":"#383a42","muted":"#a0a1a7","start":"#50a14f","stop":"#e45649","sync":"#0184bc","handoff":"#986801"},
    "Material Light": {"appearance":"light","bg":"#fafafa","card":"#ffffff","border":"#e0e0e0","text":"#212121","muted":"#9e9e9e","start":"#00897b","stop":"#e53935","sync":"#1e88e5","handoff":"#f4511e"},
    "Nord Light": {"appearance":"light","bg":"#eceff4","card":"#e5e9f0","border":"#d8dee9","text":"#2e3440","muted":"#4c566a","start":"#a3be8c","stop":"#bf616a","sync":"#5e81ac","handoff":"#ebcb8b"},
    "Github Light": {"appearance":"light","bg":"#ffffff","card":"#f6f8fa","border":"#d0d7de","text":"#24292f","muted":"#57606a","start":"#2da44e","stop":"#cf222e","sync":"#0969da","handoff":"#bf8700"},
    "Catppuccin Latte": {"appearance":"light","bg":"#eff1f5","card":"#e6e9ef","border":"#ccd0da","text":"#4c4f69","muted":"#8c8fa1","start":"#40a02b","stop":"#d20f39","sync":"#1e66f5","handoff":"#fe640b"},
    "Tokyo Day": {"appearance":"light","bg":"#e1e2e7","card":"#d5d6db","border":"#c4c8da","text":"#3760bf","muted":"#848cb5","start":"#587539","stop":"#f52a65","sync":"#2e7de9","handoff":"#b15c00"},
    "Everforest Light": {"appearance":"light","bg":"#fdf6e3","card":"#f4f0d9","border":"#e0dac3","text":"#5c6a72","muted":"#9da9a0","start":"#8da101","stop":"#f85552","sync":"#35a77c","handoff":"#dfa000"},
    "Ayu Light": {"appearance":"light","bg":"#fafafa","card":"#f3f4f5","border":"#e7e8ea","text":"#575f66","muted":"#787b80","start":"#6cbf43","stop":"#f07171","sync":"#399ee6","handoff":"#fa8d3e"},
    "Rosé Pine Dawn": {"appearance":"light","bg":"#faf4ed","card":"#fffaf3","border":"#f2e9e1","text":"#575279","muted":"#9893a5","start":"#56949f","stop":"#b4637a","sync":"#907aa9","handoff":"#ea9d34"},
    "Kanagawa Light": {"appearance":"light","bg":"#f2ecbc","card":"#e7e0a8","border":"#c8ba80","text":"#545176","muted":"#908c6a","start":"#618a18","stop":"#c84053","sync":"#3477b2","handoff":"#ce7e4b"},
    "Coffee Dark": {"appearance":"dark","bg":"#0e0a08","card":"#170e0a","border":"#22160f","text":"#f0e6d8","muted":"#806050","start":"#a0522d","stop":"#dc143c","sync":"#cd853f","handoff":"#daa520"},
    "Midnight Teal": {"appearance":"dark","bg":"#080e10","card":"#0e181a","border":"#142428","text":"#d8f0ee","muted":"#507878","start":"#00b4ab","stop":"#ff4466","sync":"#00d4cc","handoff":"#ffaa00"},
    "Dark Mauve": {"appearance":"dark","bg":"#0e0a12","card":"#160e1e","border":"#201428","text":"#f0e4f8","muted":"#806890","start":"#9d4edd","stop":"#e63946","sync":"#c77dff","handoff":"#ffba08"},
    "Amber Dark": {"appearance":"dark","bg":"#0e0c08","card":"#181208","border":"#241a0c","text":"#f5edcc","muted":"#807050","start":"#d4a017","stop":"#dc143c","sync":"#ffd700","handoff":"#ff8c00"},
    "Sepia Dark": {"appearance":"dark","bg":"#0c0a08","card":"#14100c","border":"#1e1810","text":"#f0e8d0","muted":"#706858","start":"#8b6914","stop":"#a0522d","sync":"#cd853f","handoff":"#daa520"},
    "Steel Dark": {"appearance":"dark","bg":"#0c0e10","card":"#141618","border":"#1e2224","text":"#d0d8e0","muted":"#607080","start":"#4682b4","stop":"#dc143c","sync":"#70a0c8","handoff":"#ffa500"},
    "Pine Dark": {"appearance":"dark","bg":"#080e0a","card":"#0e1810","border":"#142018","text":"#d0f0d8","muted":"#508060","start":"#228b22","stop":"#dc143c","sync":"#32cd32","handoff":"#ffd700"},
    "Cinder": {"appearance":"dark","bg":"#0a0a08","card":"#121210","border":"#1e1e1a","text":"#f0f0e0","muted":"#808070","start":"#ff6347","stop":"#dc143c","sync":"#ffd700","handoff":"#ff8c00"},
    "Lavender Dark": {"appearance":"dark","bg":"#0e0c14","card":"#14101e","border":"#1e1828","text":"#f0ecff","muted":"#7870a0","start":"#9370db","stop":"#ff4466","sync":"#7b68ee","handoff":"#ffaa00"},
    "Hacker": {"appearance":"dark","bg":"#000000","card":"#050505","border":"#0a0a0a","text":"#00ff00","muted":"#1a4d1a","start":"#00dd00","stop":"#ff0000","sync":"#00ffff","handoff":"#ffff00"},
    "Blood Moon": {"appearance":"dark","bg":"#0e0404","card":"#180808","border":"#2a0c0c","text":"#ffe0e0","muted":"#906060","start":"#ff2020","stop":"#8b0000","sync":"#ff8080","handoff":"#ff4400"},
    "Radioactive": {"appearance":"dark","bg":"#050e05","card":"#081808","border":"#0f220f","text":"#e0ffe0","muted":"#408040","start":"#39ff14","stop":"#ff2020","sync":"#00ffff","handoff":"#ffff00"},
    "Deep Purple": {"appearance":"dark","bg":"#0a0414","card":"#10081e","border":"#180c2a","text":"#ece0ff","muted":"#6840a0","start":"#7c3aed","stop":"#e11d48","sync":"#a855f7","handoff":"#f59e0b"},
    "Night Vision": {"appearance":"dark","bg":"#000a00","card":"#001400","border":"#001e00","text":"#39ff14","muted":"#1a4d1a","start":"#00ff41","stop":"#ff2020","sync":"#00ddff","handoff":"#aaff00"},
    "Twilight": {"appearance":"dark","bg":"#100c1a","card":"#181228","border":"#22183a","text":"#ece0ff","muted":"#806890","start":"#7c3aed","stop":"#e11d48","sync":"#c084fc","handoff":"#f59e0b"},
    "Crimson Night": {"appearance":"dark","bg":"#0e0408","card":"#180810","border":"#2a0c18","text":"#ffd0e8","muted":"#906070","start":"#e11d48","stop":"#7f1d1d","sync":"#ff77aa","handoff":"#ffaa00"},
    "Fossil": {"appearance":"dark","bg":"#10100a","card":"#181810","border":"#22221a","text":"#f5f0e0","muted":"#807870","start":"#8b7355","stop":"#a0522d","sync":"#b8860b","handoff":"#cd853f"},
    "Storm": {"appearance":"dark","bg":"#0a0c14","card":"#10121e","border":"#181a2c","text":"#c8d4f0","muted":"#5868a0","start":"#4169e1","stop":"#dc143c","sync":"#6495ed","handoff":"#ffa500"},
    "Absinthe": {"appearance":"dark","bg":"#081008","card":"#0e1a0e","border":"#142618","text":"#d0f8d0","muted":"#508050","start":"#7fff00","stop":"#ff2020","sync":"#00ff80","handoff":"#ffee00"},
    "Ash": {"appearance":"dark","bg":"#121212","card":"#1a1a1a","border":"#282828","text":"#e0e0e0","muted":"#787878","start":"#808080","stop":"#cc2222","sync":"#8080cc","handoff":"#ccaa22"},
    "Void Purple": {"appearance":"dark","bg":"#050010","card":"#0a0018","border":"#12002a","text":"#f0d0ff","muted":"#604880","start":"#cc00ff","stop":"#ff2020","sync":"#8800ff","handoff":"#ff8800"},
    "Terminal": {"appearance":"dark","bg":"#000000","card":"#0c0c0c","border":"#1a1a1a","text":"#cccccc","muted":"#666666","start":"#00cc00","stop":"#cc0000","sync":"#0099cc","handoff":"#ccaa00"},
    "Lava": {"appearance":"dark","bg":"#100000","card":"#1a0404","border":"#280808","text":"#ffe0c8","muted":"#906048","start":"#ff4500","stop":"#dc143c","sync":"#ff8c00","handoff":"#ffd700"},
    "Iceberg Dark": {"appearance":"dark","bg":"#161821","card":"#1e2132","border":"#2e3244","text":"#c6c8d1","muted":"#6b7089","start":"#84a0c6","stop":"#e27878","sync":"#89b8c2","handoff":"#e2a478"},
    "Moonlight": {"appearance":"dark","bg":"#222436","card":"#2f334d","border":"#444a73","text":"#c8d3f5","muted":"#828bb8","start":"#c3e88d","stop":"#ff757f","sync":"#86e1fc","handoff":"#ffc777"},
    "Oxocarbon": {"appearance":"dark","bg":"#161616","card":"#1e1e1e","border":"#262626","text":"#f4f4f4","muted":"#8d8d8d","start":"#42be65","stop":"#ff8389","sync":"#78a9ff","handoff":"#ffb3b8"},
    "Zenbones Dark": {"appearance":"dark","bg":"#191919","card":"#222222","border":"#333333","text":"#e0dfd7","muted":"#7c7c7c","start":"#78aa6a","stop":"#d47766","sync":"#6aa6c2","handoff":"#c9aa7c"}
,
    "Peach Dark": {"appearance":"dark","bg":"#100a08","card":"#1a1008","border":"#281810","text":"#ffe8d0","muted":"#906858","start":"#ff7043","stop":"#e53935","sync":"#ffa726","handoff":"#ffd54f"},
    "Watermelon Dark": {"appearance":"dark","bg":"#08100a","card":"#0c1e0e","border":"#102a14","text":"#d0ffe0","muted":"#407050","start":"#ff4d6d","stop":"#e53935","sync":"#4caf50","handoff":"#ffeb3b"},
    "Bubblegum Dark": {"appearance":"dark","bg":"#140810","card":"#1e0c1a","border":"#2a1228","text":"#ffe0f8","muted":"#906888","start":"#ff69b4","stop":"#e53935","sync":"#da70d6","handoff":"#ffe066"},
    "Spearmint Dark": {"appearance":"dark","bg":"#081410","card":"#0e2018","border":"#142c22","text":"#d0fff0","muted":"#408068","start":"#00bfa5","stop":"#e53935","sync":"#00e5b0","handoff":"#ffeb3b"},
    "Grapefruit Dark": {"appearance":"dark","bg":"#120808","card":"#1c0c0c","border":"#2a1010","text":"#ffe8e0","muted":"#906058","start":"#ff6f61","stop":"#c62828","sync":"#ff8a65","handoff":"#ffd54f"},
    "Dusk": {"appearance":"dark","bg":"#0e0c14","card":"#141020","border":"#1e162e","text":"#e8dff8","muted":"#706888","start":"#b39ddb","stop":"#f06292","sync":"#81d4fa","handoff":"#fff176"},
    "Deep Orange Dark": {"appearance":"dark","bg":"#100800","card":"#1a0c00","border":"#281200","text":"#ffe0c0","muted":"#906040","start":"#ff6d00","stop":"#d50000","sync":"#ff9100","handoff":"#ffd600"},
    "Cyan Dark": {"appearance":"dark","bg":"#081012","card":"#0e181c","border":"#142428","text":"#d0f8ff","muted":"#408090","start":"#00bcd4","stop":"#e53935","sync":"#00e5ff","handoff":"#ffeb3b"},
    "Lime Dark": {"appearance":"dark","bg":"#0a1008","card":"#121e0c","border":"#1a2c12","text":"#e0ffd0","muted":"#608058","start":"#8bc34a","stop":"#e53935","sync":"#c6ff00","handoff":"#ffeb3b"},
    "Amber Light": {"appearance":"light","bg":"#fff8e1","card":"#fffff0","border":"#ffe082","text":"#5d4037","muted":"#8d6e63","start":"#f57f17","stop":"#c62828","sync":"#0288d1","handoff":"#e65100"},
    "Cyan Light": {"appearance":"light","bg":"#e0f7fa","card":"#f0feff","border":"#b2ebf2","text":"#006064","muted":"#0097a7","start":"#00838f","stop":"#c62828","sync":"#0288d1","handoff":"#e65100"},
    "Lime Light": {"appearance":"light","bg":"#f9fbe7","card":"#fffff0","border":"#dce775","text":"#33691e","muted":"#689f38","start":"#558b2f","stop":"#c62828","sync":"#0288d1","handoff":"#e65100"},
    "Deep Purple Light": {"appearance":"light","bg":"#ede7f6","card":"#f8f5ff","border":"#ce93d8","text":"#4a148c","muted":"#7b1fa2","start":"#6a1b9a","stop":"#c62828","sync":"#0288d1","handoff":"#f57f17"},
    "Pink Light": {"appearance":"light","bg":"#fce4ec","card":"#fff0f4","border":"#f48fb1","text":"#880e4f","muted":"#c2185b","start":"#ad1457","stop":"#c62828","sync":"#0288d1","handoff":"#f57f17"},
    "Teal Light": {"appearance":"light","bg":"#e0f2f1","card":"#f0fffe","border":"#b2dfdb","text":"#004d40","muted":"#00796b","start":"#00695c","stop":"#c62828","sync":"#0288d1","handoff":"#f57f17"},
    "Indigo Light": {"appearance":"light","bg":"#e8eaf6","card":"#f2f4ff","border":"#9fa8da","text":"#1a237e","muted":"#303f9f","start":"#283593","stop":"#c62828","sync":"#0288d1","handoff":"#f57f17"},
    "Wetstone": {"appearance":"dark","bg":"#1a1a1c","card":"#222224","border":"#2e2e32","text":"#dcdce8","muted":"#787888","start":"#78c8d4","stop":"#e06c75","sync":"#a8c8f0","handoff":"#f0b878"},
    "Dawnfrost": {"appearance":"dark","bg":"#141820","card":"#1c2230","border":"#283040","text":"#d8e4f8","muted":"#6878a0","start":"#56a0d8","stop":"#e06878","sync":"#56d0b8","handoff":"#f0c860"},
    "Mosstone": {"appearance":"dark","bg":"#141814","card":"#1c241c","border":"#283228","text":"#d8e8d8","muted":"#688068","start":"#78c878","stop":"#e06878","sync":"#78c8c0","handoff":"#f0d060"},
    "Ashgold": {"appearance":"dark","bg":"#181610","card":"#221e14","border":"#302a1c","text":"#f0e8d0","muted":"#887860","start":"#c0a040","stop":"#d05040","sync":"#a0c8d0","handoff":"#f0d060"},
    "Verdant": {"appearance":"dark","bg":"#0c180e","card":"#12221a","border":"#183028","text":"#d0f0e0","muted":"#508070","start":"#2eb872","stop":"#e05050","sync":"#00d4aa","handoff":"#f0d060"},
    "Chalcedony": {"appearance":"dark","bg":"#1a1c20","card":"#22262e","border":"#2e3440","text":"#dce4f0","muted":"#7080a0","start":"#88aad0","stop":"#d87878","sync":"#88cccc","handoff":"#e8c880"}
}

_DEFAULT_KEYS = ("appearance","bg","card","border","text","muted","start","stop","sync","handoff")
_DEFAULT_T = THEMES["Dark (Default)"]


def _norm(raw: dict) -> dict:
    out = {}
    out["appearance"] = raw.get("appearance", raw.get("a", "dark"))
    for k in ("bg","card","border","text","muted","start","stop","sync"):
        out[k] = raw.get(k, _DEFAULT_T[k])
    out["handoff"] = raw.get("handoff", raw.get("hand", _DEFAULT_T["handoff"]))
    return out


def _load_themes_from_file() -> dict:
    if not THEMES_FILE or not os.path.exists(THEMES_FILE):
        return {}
    try:
        raw = open(THEMES_FILE, encoding="utf-8", errors="ignore").read()
        raw = raw.replace("\r\n", "\n").replace("\r", "\n")
        lines = [l for l in raw.splitlines() if not l.strip().startswith("#")]
        raw_clean = "\n".join(lines)
        eq = raw_clean.find("=")
        dict_str = raw_clean[eq+1:].strip() if eq != -1 else raw_clean.strip()
        parsed = ast.literal_eval(dict_str)
        result = {}
        for name, t in parsed.items():
            try:
                result[name] = _norm(t)
            except Exception:
                pass
        logger.info(f"Loaded {len(result)} themes from {os.path.basename(THEMES_FILE)}")
        return result
    except Exception as e:
        logger.warning(f"Theme file parse error: {e}")
        return {}


def _init_themes():
    THEMES.update(_load_themes_from_file())
    THEMES.update({
        k: _norm(v)
        for k, v in load_settings().get("custom_themes", {}).items()
    })

_init_themes()


def _resolve_theme(name: str) -> dict:
    td = THEMES.get(name, _DEFAULT_T)
    return {k: td.get(k, _DEFAULT_T[k]) for k in _DEFAULT_KEYS}


_s = load_settings()
current_theme_name: str = _s.get("theme", "Dark (Default)").strip()
if current_theme_name not in THEMES:
    current_theme_name = "Dark (Default)"

T: dict = _resolve_theme(current_theme_name)


def _qss(t: dict, **_) -> str:
    """Generate app-wide QSS. Glossy removed — clean flat design only."""
    try:
        from core.constants import UI_FONT, MONO_FONT
        _uf = UI_FONT.split(",")[0]
        _mf = MONO_FONT.split(",")[0]
    except Exception:
        _uf, _mf = "Segoe UI", "Consolas"
    return f"""
    * {{ font-family: {_uf}, sans-serif; font-size: 13px; }}

    QMainWindow, QDialog  {{ background: {t["bg"]}; color: {t["text"]}; }}
    QWidget               {{ background: {t["bg"]}; color: {t["text"]}; }}
    QWidget#central       {{ background: {t["bg"]}; }}

    QAbstractScrollArea::viewport {{ background: {t["bg"]}; }}
    QScrollArea                   {{ background: {t["bg"]}; border: none; }}

    /* ── Sidebar ── */
    QFrame#sidebar {{
        background: {t["card"]};
        border: none;
    }}

    /* ── Cards ── */
    QFrame#card {{
        background: {t["card"]};
        border: 1px solid {t["border"]};
        border-radius: 10px;
    }}

    /* ── Top bar / sub bars ── */
    QFrame#topbar    {{ background: {t["card"]}; border-bottom: 1px solid {t["border"]}; border-radius: 0; }}
    QFrame#subtopbar {{ background: {t["bg"]};   border-bottom: 1px solid {t["border"]}; border-radius: 0; }}
    QFrame#perf_strip {{ background: {t["card"]}; border-top: 1px solid {t["border"]}; border-radius: 0; }}
    QFrame#ip_bar     {{ background: {t["card"]}; border-top: 1px solid {t["border"]}; border-radius: 0; }}

    /* ── Settings row style ── */
    QFrame#settings_row {{
        background: {t["card"]};
        border: 1px solid {t["border"]};
        border-radius: 8px;
        min-height: 46px;
    }}
    QFrame#settings_row:hover {{
        border-color: {t["muted"]};
        background: {t["bg"]};
    }}
    QFrame#settings_section {{
        background: transparent;
        border: none;
    }}

    /* ── Labels ── */
    QLabel             {{ background: transparent; color: {t["text"]}; }}
    QLabel#muted       {{ color: {t["muted"]}; font-size: 11px; background: transparent; }}
    QLabel#header      {{ color: {t["text"]}; font-size: 11px; font-weight: 700;
                          letter-spacing: 0.8px; background: transparent; }}
    QLabel#section_hdr {{ color: {t["muted"]}; font-size: 10px; font-weight: 600;
                          letter-spacing: 1.2px; background: transparent;
                          text-transform: uppercase; padding: 8px 0 4px 0; }}
    QLabel#dot_running {{ color: {t["start"]};   font-size: 16px; background: transparent; }}
    QLabel#dot_stopped {{ color: {t["stop"]};    font-size: 16px; background: transparent; }}
    QLabel#dot_other   {{ color: {t["handoff"]}; font-size: 16px; background: transparent; }}
    QLabel#perf_val    {{ font-size: 17px; font-weight: 700; background: transparent; }}

    /* ── Horizontal rule ── */
    QFrame#hline {{ background: {t["border"]}; border: none; max-height: 1px; }}

    /* ── Buttons ── */
    QPushButton {{
        background: {t["card"]};
        color: {t["text"]};
        border: 1px solid {t["border"]};
        border-radius: 7px;
        padding: 5px 12px;
        font-weight: 500;
    }}
    QPushButton:hover   {{ background: {t["border"]}; color: {t["text"]}; }}
    QPushButton:pressed {{ background: {t["bg"]}; }}
    QPushButton:disabled {{ color: {t["muted"]}; border-color: {t["border"]}; }}

    QPushButton#start   {{ background: {t["start"]}; color: #000; border: none; font-weight: 700; border-radius: 7px; }}
    QPushButton#start:hover  {{ background: {t["start"]}cc; }}
    QPushButton#stop    {{ background: {t["stop"]};  color: #fff; border: none; font-weight: 700; border-radius: 7px; }}
    QPushButton#stop:hover   {{ background: {t["stop"]}cc; }}
    QPushButton#sync    {{ background: {t["sync"]};  color: #000; border: none; font-weight: 700; border-radius: 7px; }}
    QPushButton#sync:hover   {{ background: {t["sync"]}cc; color: #000; }}
    QPushButton#accent  {{ background: {t["sync"]}; color: #000; border: none; border-radius: 7px;
                           padding: 6px 14px; font-weight: 700; }}
    QPushButton#accent:hover {{ background: {t["sync"]}cc; color: #000; }}
    QPushButton#handoff {{ background: {t["handoff"]}; color: #000; border: none; font-weight: 700; border-radius: 7px; }}
    QPushButton#handoff:hover {{ background: {t["handoff"]}cc; }}

    /* ── Inputs ── */
    QTextEdit, QPlainTextEdit {{
        background: {t["bg"]};
        color: {t["text"]};
        border: 1px solid {t["border"]};
        border-radius: 7px;
        font-family: {_mf}, monospace;
        font-size: 11px;
        padding: 4px;
        selection-background-color: {t["sync"]};
    }}
    QTextEdit#log_widget {{
        background: {t["bg"]};
        color: {t["text"]};
        border: 1px solid {t["border"]};
        border-radius: 7px;
        font-family: {_mf}, monospace;
        font-size: 10px;
        padding: 4px;
        selection-background-color: {t["sync"]};
    }}
    QLineEdit {{
        background: {t["bg"]};
        color: {t["text"]};
        border: 1px solid {t["border"]};
        border-radius: 7px;
        padding: 5px 10px;
        font-size: 12px;
    }}
    QLineEdit:focus  {{ border-color: {t["sync"]}; }}
    QLineEdit:hover  {{ border-color: {t["muted"]}; }}

    /* ── Tab widget (fallback / sub-tabs only) ── */
    QTabWidget::pane {{ background: {t["bg"]}; border: none; border-top: 1px solid {t["border"]}; }}
    QTabBar::tab {{
        background: transparent; color: {t["muted"]};
        border: none; border-bottom: 2px solid transparent;
        padding: 6px 16px; font-size: 11px; font-weight: 500; margin-right: 2px;
    }}
    QTabBar::tab:selected {{ color: {t["sync"]}; border-bottom: 2px solid {t["sync"]}; font-weight: 700; }}
    QTabBar::tab:hover    {{ color: {t["text"]}; }}

    /* Sub-tab variant */
    QTabWidget#subtab::pane  {{ background: {t["bg"]}; border: none; border-top: 1px solid {t["border"]}; }}
    QTabBar#subtabbar::tab {{
        background: transparent; color: {t["muted"]};
        border: none; border-bottom: 2px solid transparent;
        padding: 5px 14px; font-size: 11px; font-weight: 500; margin-right: 2px;
    }}
    QTabBar#subtabbar::tab:selected {{ color: {t["sync"]}; border-bottom: 2px solid {t["sync"]}; font-weight: 700; }}
    QTabBar#subtabbar::tab:hover    {{ color: {t["text"]}; }}

    /* ── Scrollbars ── */
    QScrollBar:vertical   {{ background: {t["bg"]}; width: 7px; border-radius: 4px; }}
    QScrollBar::handle:vertical {{ background: {t["border"]}; border-radius: 4px; min-height: 20px; }}
    QScrollBar::handle:vertical:hover {{ background: {t["muted"]}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar:horizontal {{ background: {t["bg"]}; height: 7px; border-radius: 4px; }}
    QScrollBar::handle:horizontal {{ background: {t["border"]}; border-radius: 4px; }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

    /* ── Combo / check / slider ── */
    QComboBox {{
        background: {t["bg"]}; color: {t["text"]};
        border: 1px solid {t["border"]}; border-radius: 7px; padding: 4px 10px;
    }}
    QComboBox:hover  {{ border-color: {t["muted"]}; }}
    QComboBox:focus  {{ border-color: {t["sync"]}; }}
    QComboBox::drop-down {{ border: none; padding-right: 6px; }}
    QComboBox QAbstractItemView {{
        background: {t["card"]}; color: {t["text"]};
        border: 1px solid {t["border"]};
        selection-background-color: {t["border"]};
    }}

    QCheckBox             {{ color: {t["text"]}; spacing: 8px; background: transparent; }}
    QCheckBox::indicator  {{
        width: 18px; height: 18px;
        border: 1px solid {t["border"]}; border-radius: 5px; background: {t["bg"]};
    }}
    QCheckBox::indicator:checked {{ background: {t["sync"]}; border-color: {t["sync"]}; }}
    QCheckBox::indicator:hover   {{ border-color: {t["muted"]}; }}

    QSlider::groove:horizontal {{ background: {t["border"]}; height: 4px; border-radius: 2px; }}
    QSlider::handle:horizontal {{
        background: {t["sync"]}; width: 16px; height: 16px; margin: -6px 0; border-radius: 8px;
    }}
    QSlider::sub-page:horizontal {{ background: {t["sync"]}; border-radius: 2px; }}

    QProgressBar {{
        background: {t["border"]}; border: none; border-radius: 4px;
        text-align: center; color: {t["text"]};
    }}
    QProgressBar::chunk {{ background: {t["sync"]}; border-radius: 4px; }}

    QSplitter::handle {{ background: {t["border"]}; }}

    /* ── Status bar ── */
    QStatusBar {{ background: {t["card"]}; color: {t["muted"]}; border-top: 1px solid {t["border"]}; font-size: 9px; }}

    /* ── Dialogs ── */
    QInputDialog QWidget {{ background: {t["card"]}; color: {t["text"]}; }}
    QMessageBox           {{ background: {t["bg"]};   color: {t["text"]}; }}
    QMessageBox QLabel    {{ color: {t["text"]}; background: transparent; }}
    QMessageBox QPushButton {{
        background: {t["card"]}; color: {t["text"]};
        border: 1px solid {t["border"]}; border-radius: 7px;
        padding: 6px 18px; min-width: 64px;
    }}
    """
