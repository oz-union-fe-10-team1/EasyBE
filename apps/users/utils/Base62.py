import random
import string


def generate_base62_code(length=6):
    base62_chars = string.digits + string.ascii_uppercase + string.ascii_lowercase
    return "".join(random.choice(base62_chars) for _ in range(length))  # 인코딩 된 6자리 코드 생성
