# PyInstaller recipe. Run it with build.bat, not by hand.
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

datas = []
binaries = []

# faster-whisper ships a small voice-detector model as a data file.
datas += collect_data_files("faster_whisper")
# ctranslate2 and onnxruntime carry their own DLLs.
binaries += collect_dynamic_libs("ctranslate2")
binaries += collect_dynamic_libs("onnxruntime")
binaries += collect_dynamic_libs("av")

datas += [("assets/murmur.ico", "assets")]

hiddenimports = [
    "sounddevice",
    "anthropic",
]

# Qt is the interface now. Ship only the modules the app actually uses.
qt_excludes = [
    "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtQuick3D", "PySide6.Qt3DCore",
    "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtWebEngineQuick",
    "PySide6.QtMultimedia", "PySide6.QtMultimediaWidgets", "PySide6.QtCharts",
    "PySide6.QtDataVisualization", "PySide6.QtBluetooth", "PySide6.QtNfc",
    "PySide6.QtPositioning", "PySide6.QtSerialPort", "PySide6.QtSql",
    "PySide6.QtTest", "PySide6.QtDesigner", "PySide6.QtHelp", "PySide6.QtPdf",
    "PySide6.QtPdfWidgets", "PySide6.QtOpenGL", "PySide6.QtOpenGLWidgets",
    "PySide6.QtSensors", "PySide6.QtSpatialAudio", "PySide6.QtTextToSpeech",
    "PySide6.QtWebChannel", "PySide6.QtWebSockets", "PySide6.QtSvgWidgets",
    "PySide6.QtNetworkAuth", "PySide6.QtRemoteObjects", "PySide6.QtScxml",
    "PySide6.QtStateMachine", "PySide6.QtUiTools", "PySide6.QtConcurrent",
    "PySide6.QtHttpServer", "PySide6.QtGraphs", "PySide6.QtQuickWidgets",

]

a = Analysis(
    ["entry.py"],
    pathex=["src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["matplotlib", "pytest", "IPython", "tkinter", "pystray"] + qt_excludes,
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Murmur",
    console=False,          # no black window
    icon="assets/murmur.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="Murmur",
)
