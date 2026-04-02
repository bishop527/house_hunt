import os

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
        # Fall back to hardcoded addresses for backward compatibility
        return {
            'WORK_ADDR1': "123 Main St. Anytown, MA 00000",
            'WORK_ADDR2': "200 Chauncy St. Mansfield, MA 02048"
        }
    
    try:
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    addresses[key.strip()] = value.strip()
        
        return addresses
    except Exception as e:
        print(f"Error loading work addresses: {e}")
        # Fall back to hardcoded addresses
        return {
            'WORK_ADDR1': "123 Main St. Anytown, MA 00000",
            'WORK_ADDR2': "200 Chauncy St. Mansfield, MA 02048"
        }
