import socket
import socketserver
import sys
import threading
import unittest
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))

from privado_ci_mock import SocksHandler, SocksServer, recv_exact


class EchoHandler(socketserver.BaseRequestHandler):
    def handle(self):
        while data := self.request.recv(4096):
            self.request.sendall(data)


class PrivadoCiMockTests(unittest.TestCase):
    def test_socks5_connect_relays_bytes(self):
        echo = socketserver.ThreadingTCPServer(("127.0.0.1", 0), EchoHandler)
        socks = SocksServer(("127.0.0.1", 0), SocksHandler)
        servers = (echo, socks)
        threads = [threading.Thread(target=server.serve_forever) for server in servers]
        for thread in threads:
            thread.start()

        try:
            with socket.create_connection(socks.server_address) as client:
                client.sendall(b"\x05\x01\x00")
                self.assertEqual(recv_exact(client, 2), b"\x05\x00")

                host, port = echo.server_address
                request = b"\x05\x01\x00\x01" + socket.inet_aton(host) + port.to_bytes(2, "big")
                client.sendall(request)
                self.assertEqual(recv_exact(client, 10), b"\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00")

                client.sendall(b"umbrelarr")
                self.assertEqual(recv_exact(client, 9), b"umbrelarr")
        finally:
            for server in servers:
                server.shutdown()
                server.server_close()
            for thread in threads:
                thread.join()


if __name__ == "__main__":
    unittest.main()
