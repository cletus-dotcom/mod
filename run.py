import os
import socket

from app import create_app

app = create_app()


def _bootstrap():
    with app.app_context():
        from app.seed import ensure_seeded

        ensure_seeded()
    app.extensions["motorela_seeded"] = True


def _lan_ip():
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.connect(("8.8.8.8", 80))
        address = probe.getsockname()[0]
        probe.close()
        return address
    except OSError:
        return None


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8036"))
    _bootstrap()
    print(f"Motorela registry: http://127.0.0.1:{port}")
    lan = _lan_ip()
    if lan:
        print(f"On this network: http://{lan}:{port}")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
