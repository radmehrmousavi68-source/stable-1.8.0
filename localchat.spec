# PyInstaller spec — run from the project root via build_installer.bat
import os

# --- Workaround for Python 3.10.0's broken `dis` module -----------------------
# On CPython 3.10.0, dis.get_instructions() can raise IndexError for some
# library bytecode, which aborts PyInstaller's analysis. Skip the instructions
# of such a code object instead of crashing (hiddenimports below cover the rest).
import sys as _sys
if _sys.version_info[:3] == (3, 10, 0):
    import PyInstaller.lib.modulegraph.util as _mg_util
    _orig_iter = _mg_util.iterate_instructions

    def _safe_iter(code_object):
        try:
            for inst in _orig_iter(code_object):
                yield inst
        except IndexError:
            return

    _mg_util.iterate_instructions = _safe_iter
# -------------------------------------------------------------------------------

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
PKG = os.path.join(ROOT, "local_chat")

a = Analysis(
    [os.path.join(ROOT, "localchat_app.py")],
    pathex=[ROOT],
    datas=[
        (os.path.join(PKG, "static"), os.path.join("local_chat", "static")),
        (os.path.join(PKG, "capability_docs"), os.path.join("local_chat", "capability_docs")),
        (os.path.join(PKG, "smtp_settings.example.json"), "local_chat"),
    ],
    hiddenimports=[
        "local_chat.server", "local_chat.capabilities", "local_chat.memory",
        "local_chat.settings", "local_chat.launcher", "local_chat.files", "local_chat.models_catalog", "local_chat.search_providers", "pypdf", "webview", "webview.platforms.edgechromium", "clr", "tkinter", "tkinter.filedialog",
    ],
    excludes=["pytest", "unittest.mock", "numpy", "pandas", "matplotlib"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="LocalChat",
    icon=os.path.join(ROOT, "packaging", "icon.ico"),
    console=False,          # no black console window
    disable_windowed_traceback=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name="LocalChat")
