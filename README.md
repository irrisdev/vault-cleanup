## Bitwarden Duplicate Cleaner / Remover

This project is designed to clean duplicates in a Bitwarden vault by processing data to remove redundant entries. All data is processed in memory.
## Prerequisites

1. **Bitwarden CLI**:
   Ensure you have the Bitwarden CLI installed. You can download and install it from the [official Bitwarden CLI documentation](https://bitwarden.com/help/cli/).

2. **Configuration and Authentication**:
   - Configure the Bitwarden CLI server with:
     ```bash
     bw config server <server-url>
     ```
   - Log in using your API key:
     ```bash
     bw login --apikey
     ```
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
   Execute the script to process the data:
   ```bash
   python script.py
   ```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
