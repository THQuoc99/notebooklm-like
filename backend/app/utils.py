import uuid
import time


def gen_id() -> str:
    return str(uuid.uuid4())


def now_ts() -> int:
    return int(time.time())
