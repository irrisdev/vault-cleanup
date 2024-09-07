import os
import subprocess
import platform
import sys
import shutil
import getpass
import json

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command '{command}': {e}")
        sys.exit(1)

def is_bw_installed():
    return shutil.which("bw") is not None

def install_bw():
    print("Bitwarden CLI (bw) is not installed. Installing...")

    os_type = platform.system().lower()

    if os_type == "linux":
        download_url = "https://vault.bitwarden.com/download/?app=cli&platform=linux"
    elif os_type == "darwin":
        download_url = "https://vault.bitwarden.com/download/?app=cli&platform=macos"
    elif os_type == "windows":
        download_url = "https://vault.bitwarden.com/download/?app=cli&platform=windows"
    else:
        print(f"Unsupported platform: {os_type}")
        sys.exit(1)

    zip_file = "bw.zip"
    run_command(f"curl -Lso {zip_file} {download_url}")
    
    # Unzip and move bw to a directory in PATH
    if os_type in ["linux", "darwin"]:
        run_command(f"unzip {zip_file}")
        run_command(f"sudo mv bw /usr/local/bin/bw")
    elif os_type == "windows":
        run_command(f"powershell -Command \"Expand-Archive -Path {zip_file} -DestinationPath .\"")
        run_command(f"move bw.exe %SYSTEMROOT%\\System32\\bw.exe")
    
    os.remove(zip_file)

def check_bw_status():
    status_output = run_command("bw status")
    status_json = json.loads(status_output)

    if status_json.get("serverUrl") is None:
        print("Server URL is not configured. Setting server URL...")
        configure_bw()
    else:
        print(f"Server URL is already configured: {status_json.get('serverUrl')}")

def configure_bw():
    server_url = "https://vault.bitwarden.com"
    print(f"Configuring Bitwarden CLI to use server: {server_url}")
    run_command(f"bw config server {server_url}")

def login_bw(client_id=None, client_secret=None):
    if not client_id:
        client_id = input("Enter your Bitwarden Client ID: ")
    if not client_secret:
        client_secret = getpass.getpass("Enter your Bitwarden Client Secret: ")

    # Set environment variables for client ID and secret
    os.environ["BW_CLIENTID"] = client_id
    os.environ["BW_CLIENTSECRET"] = client_secret

    print("Logging in to Bitwarden CLI using API key...")
    
    # Run the bw login command with the environment variables
    login_command = "bw login --apikey"
    run_command(f"BW_CLIENTID=$BW_CLIENTID BW_CLIENTSECRET=$BW_CLIENTSECRET {login_command}")

def unlock_bw():
    master_password = getpass.getpass("Enter your Bitwarden Master Password: ")
    print("Unlocking Bitwarden Vault...")
    # --raw flag is for return only session key
    session_key = run_command(f"bw unlock {master_password} --raw")
    print('Session key:', session_key)
    # Extract the session key from the login output
    if session_key:
        os.environ["BW_SESSION"] = session_key
        print("Session key has been set as an environment variable.")
    else:
        print("Failed to obtain the session key.")
        sys.exit(1)

def serve_bw():
    print("Starting Bitwarden serve...")
    run_command("bw serve")

def main():
    if not is_bw_installed():
        install_bw()

    check_bw_status()

    client_id = os.getenv("BW_CLIENTID")
    client_secret = os.getenv("BW_CLIENTSECRET")

    login_bw(client_id, client_secret)
    unlock_bw()
    serve_bw()

if __name__ == "__main__":
    main()
