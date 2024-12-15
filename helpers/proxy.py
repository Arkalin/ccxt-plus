import os
import random
import subprocess

import yaml

from helpers.logger import Logger

_proxy_path = os.path.join("config", "proxies.yml")


class ProxyManager:
    """
    A class to manage proxy servers by loading configurations, starting processes,
    and providing proxies for HTTP and HTTPS connections.

    Attributes:
        _config_file (str): Path to the configuration file.
        _processes (list): List of active subprocesses for proxies.
        _proxies (list): List of configured proxy addresses.
        _bin_path (str): Path to the proxy binary executable.
        _commands (list): List of proxy command configurations.
        _is_running (bool): Whether the proxies are currently running.
        enabled (bool): Whether the proxy manager is enabled.
    """

    _config_file = _proxy_path
    _processes = []
    _proxies = []
    _bin_path = None
    _commands = None
    _is_running = False
    enabled = True

    @staticmethod
    def _load_config():
        """
        Load proxy configurations from the YAML file.

        Returns:
            list: A list of commands and local ports for each proxy.
        """
        if ProxyManager._commands is not None:
            return ProxyManager._commands
        with open(ProxyManager._config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        ProxyManager._bin_path = config.get("bin_path")
        nodes = config.get("proxies", [])
        base_port = config.get("base_port")
        commands = []
        for i, node in enumerate(nodes):
            method = node.get("cipher")
            password = node.get("password")
            server = node.get("server")
            port = node.get("port")
            local_port = base_port + i
            # Example ss-local startup parameters:
            # ss-local -s server -p server_port -l local_port -k password -m method
            cmd = [
                ProxyManager._bin_path,
                "-s",
                str(server),
                "-p",
                str(port),
                "-l",
                str(local_port),
                "-k",
                str(password),
                "-m",
                str(method),
                "--fast-open",  # Optional parameter, add as needed
            ]
            commands.append((cmd, local_port))
        ProxyManager._commands = commands
        return commands

    @staticmethod
    def start_proxies():
        """
        Start all proxy processes and prevent duplicate startups.

        Returns:
            int: Number of proxy processes started, or -1 on failure.
        """
        if ProxyManager._is_running:
            return -1
        if not os.path.exists(_proxy_path):
            ProxyManager.enabled = False
            Logger.info(f"Failed to enable proxies, configuration file not found: {_proxy_path}")
        if not ProxyManager.enabled:
            return -1
        commands = ProxyManager._load_config()
        for cmd, local_port in commands:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            ProxyManager._processes.append(p)
            # Configure requests to use the SOCKS5 proxy
            proxy = {
                "http": f"socks5h://127.0.0.1:{local_port}",
                "https": f"socks5h://127.0.0.1:{local_port}",
            }
            ProxyManager._proxies.append(proxy)
        ProxyManager._is_running = True
        return len(commands)

    @staticmethod
    def stop_proxies():
        """
        Stop all running proxy processes gracefully.
        """
        for p in ProxyManager._processes:
            # Gracefully terminate the process
            p.terminate()

        # Wait for processes to exit
        for p in ProxyManager._processes:
            try:
                p.wait(timeout=3)
            except subprocess.TimeoutExpired:
                p.kill()

        ProxyManager._processes.clear()
        ProxyManager._proxies.clear()
        ProxyManager._is_running = False

    @staticmethod
    def get_random_proxy():
        """
        Retrieve a random proxy from the list of configured proxies.

        Returns:
            dict or None: A proxy dictionary for HTTP and HTTPS, or None if no proxies are available.
        """
        if not ProxyManager._proxies:
            return None
        return random.choice(ProxyManager._proxies)
