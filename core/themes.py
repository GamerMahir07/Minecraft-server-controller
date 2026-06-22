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
    "Ultra Black Dark": {"appearance":"dark","bg":"#000000","card":"#050505","border":"#0f0f0f","text":"#ffffff","muted":"#333333","start":"#ffffff","stop":"#ff0000","sync":"#aaaaaa","handoff":"#ffff00"}
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


def _qss(t: dict, glossy: bool = False, side_tabs: bool = False) -> str:

    # ── Glossy variants ───────────────────────────────────────────────────────
    # Uses theme's own card/bg colors with a subtle top-lit sheen.
    # Sheen = card at 100% opacity on top, card at 80% in middle, bg at 90% at bottom.
    if glossy:
        _card = f"""
    QFrame#card {{
        background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
            stop:0 {t['card']}ff,
            stop:0.4 {t['card']}cc,
            stop:1   {t['bg']}e6);
        border: 1px solid {t['border']};
        border-top: 1px solid {t['muted']}66;
        border-radius: 12px;
    }}"""
        _btn = f"""
    QPushButton {{
        background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
            stop:0 {t['card']}ff, stop:1 {t['bg']}cc);
        color: {t['text']};
        border: 1px solid {t['border']};
        border-top: 1px solid {t['muted']}55;
        border-radius: 7px;
        padding: 5px 12px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
            stop:0 {t['border']}ff, stop:1 {t['card']}cc);
        color: {t['text']};
    }}
    QPushButton:pressed {{
        background: qlineargradient(x1:0,y1:1,x2:0,y2:0,
            stop:0 {t['card']}ff, stop:1 {t['bg']}cc);
    }}
    QPushButton:disabled {{ color: {t['muted']}; border-color: {t['border']}; }}"""
        _input = f"""
    QTextEdit, QPlainTextEdit {{
        background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
            stop:0 {t['bg']}ff, stop:1 {t['card']}bb);
        color: {t['text']};
        border: 1px solid {t['border']};
        border-top: 1px solid {t['muted']}44;
        border-radius: 7px;
        font-family: "Consolas", monospace; font-size: 11px; padding: 4px;
        selection-background-color: {t['sync']};
    }}
    QLineEdit {{
        background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
            stop:0 {t['bg']}ff, stop:1 {t['card']}bb);
        color: {t['text']};
        border: 1px solid {t['border']};
        border-top: 1px solid {t['muted']}44;
        border-radius: 7px;
        padding: 5px 8px; font-size: 12px;
    }}
    QLineEdit:focus  {{ border-color: {t['sync']}; }}
    QLineEdit:hover  {{ border-color: {t['muted']}; }}"""
        _tab_bg     = f"qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 {t['card']}ff,stop:1 {t['bg']}cc)"
        _tab_sel_bg = f"qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 {t['sync']}18,stop:1 {t['bg']}ff)"
        _card_radius = "12px"
    else:
        _card = f"""
    QFrame#card {{
        background: {t['card']};
        border: 1px solid {t['border']};
        border-radius: 10px;
    }}"""
        _btn = f"""
    QPushButton {{
        background: {t['card']};
        color: {t['text']};
        border: 1px solid {t['border']};
        border-radius: 6px;
        padding: 5px 12px;
        font-weight: 500;
    }}
    QPushButton:hover   {{ background: {t['border']}; color: {t['text']}; }}
    QPushButton:pressed {{ background: {t['border']}; }}
    QPushButton:disabled {{ color: {t['muted']}; border-color: {t['border']}; }}"""
        _input = f"""
    QTextEdit, QPlainTextEdit {{
        background: {t['bg']};
        color: {t['text']};
        border: 1px solid {t['border']};
        border-radius: 6px;
        font-family: "Consolas", monospace; font-size: 11px; padding: 4px;
        selection-background-color: {t['sync']};
    }}
    QLineEdit {{
        background: {t['bg']};
        color: {t['text']};
        border: 1px solid {t['border']};
        border-radius: 6px;
        padding: 5px 8px; font-size: 12px;
    }}
    QLineEdit:focus  {{ border-color: {t['sync']}; }}
    QLineEdit:hover  {{ border-color: {t['muted']}; }}"""
        _tab_bg     = t['card']
        _tab_sel_bg = t['bg']
        _card_radius = "10px"

    # ── Main tab bar — horizontal (default) or vertical (side_tabs=True) ──────
    if side_tabs:
        _tabs = f"""
    QTabWidget::pane  {{ background: {t['bg']}; border: none; border-left: 1px solid {t['border']}; }}
    QTabBar::tab {{
        background: {_tab_bg};
        color: {t['muted']};
        border: none;
        border-right: 2px solid transparent;
        padding: 12px 18px;
        margin-bottom: 2px;
        text-align: left;
        min-width: 110px;
        font-size: 12px;
    }}
    QTabBar::tab:selected {{
        background: {_tab_sel_bg};
        color: {t['text']};
        border-right: 2px solid {t['sync']};
        font-weight: 700;
    }}
    QTabBar::tab:hover {{ color: {t['text']}; background: {t['border']}; }}"""
    else:
        _tabs = f"""
    QTabWidget::pane  {{ background: {t['bg']}; border: none; }}
    QTabBar::tab {{
        background: {_tab_bg};
        color: {t['muted']};
        border: 1px solid {t['border']};
        border-bottom: none;
        padding: 8px 20px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        margin-right: 2px;
        font-size: 13px;
    }}
    QTabBar::tab:selected {{
        background: {_tab_sel_bg};
        color: {t['text']};
        border-bottom: 2px solid {t['sync']};
        font-weight: 600;
    }}
    QTabBar::tab:hover {{ color: {t['text']}; }}"""

    return f"""
    * {{ font-family: "Segoe UI", sans-serif; font-size: 13px; }}

    QMainWindow, QDialog  {{ background: {t['bg']}; color: {t['text']}; }}
    QWidget               {{ background: {t['bg']}; color: {t['text']}; }}
    QWidget#central       {{ background: {t['bg']}; }}

    QAbstractScrollArea::viewport {{ background: {t['bg']}; }}
    QScrollArea                   {{ background: {t['bg']}; border: none; }}

    {_card}

    QFrame#topbar    {{ background: {t['card']}; border-bottom: 1px solid {t['border']}; border-radius: 0; }}
    QFrame#subtopbar {{ background: {t['bg']};   border-bottom: 1px solid {t['border']}; border-radius: 0; }}
    QFrame#perf_strip {{ background: {t['card']}; border-top: 1px solid {t['border']}; border-radius: 0; }}
    QFrame#ip_bar     {{ background: {t['card']}; border-top: 1px solid {t['border']}; border-radius: 0; }}

    QLabel             {{ background: transparent; color: {t['text']}; }}
    QLabel#muted       {{ color: {t['muted']}; font-size: 11px; background: transparent; }}
    QLabel#header      {{ color: {t['text']}; font-size: 12px; font-weight: 700; letter-spacing: 0.5px; background: transparent; }}
    QLabel#dot_running {{ color: {t['start']}; font-size: 16px; background: transparent; }}
    QLabel#dot_stopped {{ color: {t['stop']};  font-size: 16px; background: transparent; }}
    QLabel#dot_other   {{ color: {t['handoff']}; font-size: 16px; background: transparent; }}

    {_btn}

    QPushButton#start   {{ background: {t['start']}; color: #000; border: none; font-weight: 700; }}
    QPushButton#start:hover  {{ background: {t['start']}cc; color: #000; }}
    QPushButton#stop    {{ background: {t['stop']};  color: #fff; border: none; font-weight: 700; }}
    QPushButton#stop:hover   {{ background: {t['stop']}cc; }}
    QPushButton#sync    {{ background: {t['sync']};  color: #000; border: none; font-weight: 700; }}
    QPushButton#sync:hover   {{ background: {t['sync']}cc; color: #000; }}
    QPushButton#accent  {{ background: {t['sync']}; color: #000; border: none; border-radius: 6px; padding: 6px 14px; font-weight: 700; }}
    QPushButton#accent:hover {{ background: {t['sync']}cc; color: #000; }}
    QPushButton#handoff {{ background: {t['handoff']}; color: #000; border: none; font-weight: 700; }}
    QPushButton#handoff:hover {{ background: {t['handoff']}cc; }}

    {_input}

    {_tabs}

    QTabWidget#subtab::pane  {{ background: {t['bg']}; border: none; border-top: 1px solid {t['border']}; }}
    QTabBar#subtabbar::tab {{
        background: transparent; color: {t['muted']};
        border: none; border-bottom: 2px solid transparent;
        padding: 5px 14px; font-size: 11px; font-weight: 500; margin-right: 2px;
    }}
    QTabBar#subtabbar::tab:selected {{ color: {t['sync']}; border-bottom: 2px solid {t['sync']}; font-weight: 700; }}
    QTabBar#subtabbar::tab:hover    {{ color: {t['text']}; }}

    QScrollBar:vertical   {{ background: {t['bg']}; width: 7px; border-radius: 4px; }}
    QScrollBar::handle:vertical {{ background: {t['border']}; border-radius: 4px; min-height: 20px; }}
    QScrollBar::handle:vertical:hover {{ background: {t['muted']}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar:horizontal {{ background: {t['bg']}; height: 7px; border-radius: 4px; }}
    QScrollBar::handle:horizontal {{ background: {t['border']}; border-radius: 4px; }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

    QComboBox {{
        background: {t['bg']}; color: {t['text']};
        border: 1px solid {t['border']}; border-radius: 6px; padding: 4px 8px;
    }}
    QComboBox:hover  {{ border-color: {t['muted']}; }}
    QComboBox:focus  {{ border-color: {t['sync']}; }}
    QComboBox::drop-down {{ border: none; }}
    QComboBox QAbstractItemView {{
        background: {t['card']}; color: {t['text']};
        border: 1px solid {t['border']};
        selection-background-color: {t['border']};
    }}

    QCheckBox             {{ color: {t['text']}; spacing: 8px; background: transparent; }}
    QCheckBox::indicator  {{
        width: 18px; height: 18px;
        border: 1px solid {t['border']}; border-radius: 4px; background: {t['bg']};
    }}
    QCheckBox::indicator:checked {{ background: {t['sync']}; border-color: {t['sync']}; }}
    QCheckBox::indicator:hover   {{ border-color: {t['muted']}; }}

    QSplitter::handle {{ background: {t['border']}; }}
    QProgressBar {{
        background: {t['bg']}; border: 1px solid {t['border']};
        border-radius: 4px; text-align: center; color: {t['text']};
    }}
    QProgressBar::chunk {{ background: {t['sync']}; border-radius: 4px; }}

    QStatusBar {{ background: {t['card']}; color: {t['muted']}; border-top: 1px solid {t['border']}; }}

    QInputDialog QWidget {{ background: {t['card']}; color: {t['text']}; }}
    QMessageBox           {{ background: {t['bg']}; color: {t['text']}; }}
    QMessageBox QLabel    {{ color: {t['text']}; background: transparent; }}
    QMessageBox QPushButton {{
        background: {t['card']}; color: {t['text']};
        border: 1px solid {t['border']}; border-radius: 6px;
        padding: 6px 16px; min-width: 60px;
    }}

    QSlider::groove:horizontal {{ background: {t['border']}; height: 4px; border-radius: 2px; }}
    QSlider::handle:horizontal {{
        background: {t['sync']}; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px;
    }}
    QSlider::sub-page:horizontal {{ background: {t['sync']}; border-radius: 2px; }}
    """
