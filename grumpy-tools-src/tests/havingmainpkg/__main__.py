import sys

def main():
    print '__name__ is', __name__
    print '__package__ is', __package__
    from . import SPAM
    print(SPAM)
    sys.exit(0)

if __name__ == '__main__':
    print '__name__ IS __main__'
    print '__package__ is', __package__
    main()
