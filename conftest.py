import asyncio
import socket
import sys
import pytest
import pytest_socket

pytest_plugins = "pytest_homeassistant_custom_component"

if sys.platform == "win32":
    # The HA plugin disables sockets during test setup (allow_unix_socket=True).
    # On Windows, asyncio event loops use socketpair() over AF_INET (not AF_UNIX)
    # for the internal self-pipe, which gets blocked by pytest-socket.
    # Override the event_loop fixture to temporarily re-enable sockets while
    # creating the loop, then re-disable them.
    @pytest.fixture
    def event_loop():
        pytest_socket.enable_socket()
        loop = asyncio.SelectorEventLoop()
        pytest_socket.disable_socket(allow_unix_socket=True)
        yield loop
        loop.close()
