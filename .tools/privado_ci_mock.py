#!/usr/bin/env python3

import json
import select
import socket
import socketserver
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def recv_exact(connection, length):
    data = b""
    while len(data) < length:
        chunk = connection.recv(length - len(data))
        if not chunk:
            raise ConnectionError("unexpected EOF")
        data += chunk
    return data


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps(
            {"state": "healthy", "credentialsConfigured": True, "detail": "Connected"}
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        pass


class SocksHandler(socketserver.BaseRequestHandler):
    def handle(self):
        client = self.request
        upstream = None
        try:
            version, methods = recv_exact(client, 2)
            if version != 5:
                return
            recv_exact(client, methods)
            client.sendall(b"\x05\x00")

            version, command, _reserved, address_type = recv_exact(client, 4)
            if version != 5 or command != 1:
                raise ConnectionError("unsupported SOCKS request")
            if address_type == 1:
                host = socket.inet_ntop(socket.AF_INET, recv_exact(client, 4))
            elif address_type == 3:
                host = recv_exact(client, recv_exact(client, 1)[0]).decode()
            elif address_type == 4:
                host = socket.inet_ntop(socket.AF_INET6, recv_exact(client, 16))
            else:
                raise ConnectionError("unsupported address type")
            port = int.from_bytes(recv_exact(client, 2), "big")

            upstream = socket.create_connection((host, port), timeout=20)
            client.sendall(b"\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00")
            while True:
                ready, _writable, _errors = select.select([client, upstream], [], [], 30)
                for source in ready:
                    data = source.recv(65536)
                    if not data:
                        return
                    (upstream if source is client else client).sendall(data)
        except Exception:
            try:
                client.sendall(b"\x05\x01\x00\x01\x00\x00\x00\x00\x00\x00")
            except Exception:
                pass
        finally:
            if upstream:
                upstream.close()


class SocksServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    dashboard = ThreadingHTTPServer(("0.0.0.0", 8080), DashboardHandler)
    threading.Thread(target=dashboard.serve_forever, daemon=True).start()
    SocksServer(("0.0.0.0", 1080), SocksHandler).serve_forever()


if __name__ == "__main__":
    main()
