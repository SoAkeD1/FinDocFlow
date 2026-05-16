import re

def validate_pan(pan):
    """Verify PAN format: 5 uppercase letters, 4 digits, 1 uppercase letter."""
    if not pan:
        return False
    return bool(re.fullmatch(r'[A-Z]{5}[0-9]{4}[A-Z]', pan))
