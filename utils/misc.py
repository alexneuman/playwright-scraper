
import contextlib

import contextlib

@contextlib.contextmanager
def suppress(optional = False):
    if optional:
        try:
            yield
        except:
            pass
    else:
        yield

