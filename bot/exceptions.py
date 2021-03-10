import sys, inspect


class NotFound(Exception):
    pass

class UnAuthorized(Exception):
    pass

class OtherException(Exception):
    pass


clsmembers = inspect.getmembers(sys.modules[__name__], inspect.isclass)

customErrors = []
for c in clsmembers:
    customErrors.append(c[0])
