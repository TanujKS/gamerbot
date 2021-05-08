import os

for file in os.listdir(os.path.dirname(os.path.realpath(__file__))):
    if file != "cleanup.py":
        os.remove(file)
