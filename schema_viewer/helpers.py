import re


def extract_default(s):
    r = re.findall(r"(?:The)?[dD]efault value is (\w+)\b", s)

    if r:
        return r[0]

    return ""


def format_description(d):
    return re.sub(r"https://([\w\.\/\-\#\d\?\=\+]+)", r'<a href="https://\1">https://\1</a>', d)
