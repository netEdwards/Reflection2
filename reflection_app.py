from modules.user_interface.host.app import main as run_desktop
from modules.integrations.discord_presence import DiscordRichPresence

import logging 

logging.getLogger("pywebview").setLevel(logging.DEBUG)


if __name__ == "__main__":
    rpc = None
    try:
        try:
            rpc = DiscordRichPresence()
            rpc.start()
        except Exception as e:
            print(f"[Discord RPC] disabled: {e}")
            
        run_desktop()
    finally:
        if rpc is not None:
            rpc.stop()