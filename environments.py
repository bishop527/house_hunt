import os
import logging

logger = logging.getLogger(__name__)

def setup_directories(*folders):
    """Create essential data directories if they do not exist."""
    for folder in folders:
        os.makedirs(folder, exist_ok=True)

def load_work_addresses(path):
    """
    Load work addresses from secure file.
    
    Expected format in work_addresses.txt:
    WORK_ADDR1=123 Main St. City, State 12345
    WORK_ADDR2=456 Oak Ave. Town, State 67890
    
    Returns:
        dict: {'WORK_ADDR1': str, 'WORK_ADDR2': str}
    """
    addresses = {}
    
    if not os.path.exists(path):
        logger.warning(f"Work addresses file not found: {path}. Returning empty dictionary.")
        return {}
    
    try:
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    addresses[key.strip()] = value.strip()
        
        return addresses
    except Exception as e:
        logger.error(f"Error loading work addresses: {e}")
        return {}

_WORK_ADDRESS_CACHE = None

def get_work_address(name, path):
    """
    Lazily load and cache work addresses.
    
    Args:
        name (str): Key to look up (e.g., 'WORK_ADDR1')
        path (str): Path to the work addresses file.
        
    Returns:
        str: The address if found, otherwise a default placeholder.
    """
    global _WORK_ADDRESS_CACHE
    if _WORK_ADDRESS_CACHE is None:
        _WORK_ADDRESS_CACHE = load_work_addresses(path)
        
    return _WORK_ADDRESS_CACHE.get(name, f"{name}_NOT_SET")
