import traceback, sys
sys.path.insert(0, ".")
try:
    from routers.auth import router
    print("auth OK")
except Exception as e:
    print("FAIL auth:")
    traceback.print_exc()
