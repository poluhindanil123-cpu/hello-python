import sys
import platform

from hello import __version__
from hello.greeting import greet, sum_range


def main() -> int:
    print(f"hello-python version {__version__}")
    print("Hello from Python! 🐍📦")
    print(f"OS: {platform.system().lower()}")
    print(f"Arch: {platform.machine()}")
    print(greet("GitHub"))
    print(f"Sum 1..10 = {sum_range(1, 10)}")

    if len(sys.argv) > 1:
        print("Аргументы:")
        for i, arg in enumerate(sys.argv[1:], start=1):
            print(f"  {i}: {arg}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
