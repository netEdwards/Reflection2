from tabnanny import check
import os, time, sqlite3

conn = sqlite3.connect(r"C:\Reflection\cache\embed_cache.sqlite", check_same_thread=False)