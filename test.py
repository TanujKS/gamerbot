def make_pretty(func):
    def inner():
        print("I got decorated")
        func()
    return inner

@make_pretty
def main():
    print("I am ordinary")

main()
