import webview

_main_window: webview.Window  | None = None

def set_main_window(window: webview.Window):
    global _main_window
    _main_window = window
    
def get_main_window():
    if _main_window is not None:
        return _main_window
    if webview.windows:
        return webview.windows[0]
    
    raise RuntimeError("No webview windows available.")