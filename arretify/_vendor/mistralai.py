# File for conditionally importing the mistralai package if it exists.
try:
    from mistralai import *  # noqa: F401, F403
except ImportError:
    pass
