## Bitwarden Duplicate Cleaner / Remover

This project is designed to clean duplicates in a Bitwarden vault by processing data to remove redundant entries. All data is processed in memory.
## Prerequisites

1. **Bitwarden CLI**:
   Ensure you have the Bitwarden CLI installed. You can download and install it from the [official Bitwarden CLI documentation](https://bitwarden.com/help/cli/).

2. **Configuration and Authentication**:
 
You need to get the api keys for client id and secret:
- Goto https://bitwarden.com
- setting
- security
- view api key
- enter password master
- copy clinet id and secret

## Manual Setup
Then: if you don't want to use `login.py` script, you can do it manually:

- Configure the Bitwarden CLI server with:
   ```bash
   bw config server <server-url>
   ```
- Log in using your API key:
   ```bash
   bw login --apikey
   ```
   will ask you for your client id and secret
- Unlock your vault:
   ```bash
   bw unlock
   ```
- Start the Bitwarden server:
   ```bash
   bw serve
   ```

## Usage

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/irrisdev/vault-cleanup.git
   cd vault-cleanup
   ```

2. **Install Dependencies**:
   Make sure you have Python 3.x installed. Install required Python packages using:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Script**:
   Execute the script to login:
   ```bash
   python login.py
   ```
   Execute the script to process the data:
   ```bash
   python script.py
   ```

# Login Script

It's very similar to the Configurations and Authentication section, but with python script.

# `script.py`

It's will show you the details of the duplicate items and ask you to delete them.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
