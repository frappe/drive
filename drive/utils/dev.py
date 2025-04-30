from functools import wraps
from time import time


def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        print(
            " %2.4f s: func:%r "
            % (
                te - ts,
                f.__name__,
            )
        )
        return result

    return wrap
