import re

def password_validator(passw):
    if len(passw) < 9:
        return False
    elif not bool(re.search(r'\d', passw)):
        return False
    else:
        return True
