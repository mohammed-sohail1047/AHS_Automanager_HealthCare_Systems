import sys
from pathlib import Path

# Add project root to path so imports resolve (Django package, apps, libs)
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Delegate to actual Django WSGI application
from HclsPro.HclsPro.wsgi import application  # noqa: E402, F401

# Export `application` for the server
__all__ = ["application"]
