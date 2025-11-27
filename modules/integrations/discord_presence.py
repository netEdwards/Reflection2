from __future__ import annotations

from concurrent.futures import thread
import os
import threading
import time
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

from click import Option
from pypresence import Presence

class DiscordRichPresence:
    def __init__(
        self,
        client_id: Optional[str] = None,
        update_interval: int = 15,
        ):
        self.client_id = client_id or os.getenv("DISCORD_APP_ID")
        if not self.client_id:
            raise ValueError("Missing discord app ID.")
        
        self.update_interval = update_interval
        self._rpc: Optional[Presence] = None
        self._thread: Optional[threading.Thread] = None
        self._running : bool = False
        
    def start(self) -> None:
        if self._running:
            return
        
        print(f"[Discord RPC] using app ID: {self.client_id}") 
        
        self._rpc = Presence(self.client_id)
        self._rpc.connect()
        print("[Discord RPC] connected") 
        self._running = True
        
        def _loop():
            while self._running:
                try:
                    self._rpc.update(
                        details="Using Reflection",
                        state="Empowering users cortex",
                        large_image="reflection",
                        large_text="Reflection",
                    )
                except Exception as e:
                    print(e)
                    pass
                time.sleep(self.update_interval)
        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()
        
    def stop(self) -> None:
        self._running = False
        if self._rpc is not None:
            try:
                self._rpc.clear()
                self._rpc.close()
            except Exception as e:
                pass
        