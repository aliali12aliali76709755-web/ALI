import os
import sys
import subprocess
import re
import time
import logging
import urllib.request
from pathlib import Path

logger = logging.getLogger("tunnel")

CLOUDFLARED_EXE = Path(__file__).parent / "cloudflared.exe"
DOWNLOAD_URL = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"

class CloudflareTunnel:
    def __init__(self, port: int = 8000):
        self.port = port
        self.process = None
        self.url = None

    def download_cloudflared(self):
        if CLOUDFLARED_EXE.exists():
            return
        logger.info(f"Downloading cloudflared.exe from {DOWNLOAD_URL}...")
        try:
            urllib.request.urlretrieve(DOWNLOAD_URL, str(CLOUDFLARED_EXE))
            logger.info("Successfully downloaded cloudflared.exe")
        except Exception as e:
            logger.error(f"Failed to download cloudflared: {e}")
            raise e

    def start(self) -> str:
        self.download_cloudflared()
        logger.info(f"Starting Cloudflare Quick Tunnel on port {self.port}...")
        
        # Log file to prevent pipe deadlock
        log_path = Path(__file__).parent / "cloudflared.log"
        self.log_file = open(log_path, "w", encoding="utf-8", errors="ignore")
        
        # Start cloudflared tunnel
        cmd = [str(CLOUDFLARED_EXE), "tunnel", "--protocol", "http2", "--url", f"http://127.0.0.1:{self.port}"]
        
        # On Windows, hide the console window for the subprocess
        startupinfo = None
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0 # SW_HIDE

        self.process = subprocess.Popen(
            cmd,
            stdout=self.log_file,
            stderr=subprocess.STDOUT,
            startupinfo=startupinfo
        )

        # Read the log file line by line to find the trycloudflare URL
        self.url = None
        start_time = time.time()
        
        # Open in read mode
        time.sleep(1) # Wait a bit for file to be created and written to
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            while time.time() - start_time < 30:
                line = f.readline()
                if not line:
                    time.sleep(0.5)
                    # Check if subprocess exited early
                    if self.process.poll() is not None:
                        logger.error("cloudflared process terminated prematurely")
                        break
                    continue
                
                # Look for trycloudflare.com URL pattern
                match = re.search(r"https://[a-zA-Z0-9\-]+\.trycloudflare\.com", line)
                if match:
                    self.url = match.group(0)
                    logger.info(f"🎉 Cloudflare tunnel started successfully! Public URL: {self.url}")
                    break
        
        if not self.url:
            logger.error(f"Could not establish Cloudflare tunnel within 30 seconds. Exit status: {self.process.poll()}.")
            raise TimeoutError("Failed to obtain TryCloudflare URL")
            
        return self.url

    def stop(self):
        if self.process:
            logger.info("Stopping Cloudflare tunnel...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            logger.info("Cloudflare tunnel stopped.")
            
        if hasattr(self, "log_file") and self.log_file:
            try:
                self.log_file.close()
            except Exception:
                pass
