"""
Environment configuration module for loading API keys and sensitive data.
"""
import os
from pathlib import Path


def load_env_file(env_file='.env'):
    """
    Load environment variables from a .env file.
    
    Args:
        env_file (str): Path to the .env file relative to project root
    """
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    env_path = project_root / env_file
    
    if not env_path.exists():
        print(f"No {env_file} file found at {env_path}")
        print("Using system environment variables only.")
        return
    
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse KEY=VALUE pairs
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    # Only set if not already in environment
                    if key not in os.environ:
                        os.environ[key] = value
    
    except Exception as e:
        print(f"Error loading {env_file} file: {e}")


def get_api_credentials(exchange_name):
    """
    Get API credentials for a given exchange.
    
    Args:
        exchange_name (str): Name of the exchange (e.g., 'bybit', 'binance')
    
    Returns:
        dict: Dictionary with 'api_key' and 'api_secret' keys, or empty dict if not found
    """
    exchange_upper = exchange_name.upper()
    api_key = os.getenv(f"{exchange_upper}_API_KEY")
    api_secret = os.getenv(f"{exchange_upper}_API_SECRET")
    
    if api_key and api_secret:
        return {
            'api_key': api_key,
            'api_secret': api_secret
        }
    return {}


def has_api_credentials(exchange_name):
    """
    Check if API credentials are available for a given exchange.
    
    Args:
        exchange_name (str): Name of the exchange
    
    Returns:
        bool: True if both API key and secret are available
    """
    credentials = get_api_credentials(exchange_name)
    return bool(credentials.get('api_key') and credentials.get('api_secret'))


# Load .env file when module is imported
load_env_file()
