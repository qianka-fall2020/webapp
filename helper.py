import re


def password_validator(passw):
    if len(passw) < 9:#length >=8
        return False
    if not bool(re.search(r'\d', passw)):#contains digits
        return False
    if not bool(re.search(r'[a-zA-Z]', passw)):#conatins letters
        return False
    return True