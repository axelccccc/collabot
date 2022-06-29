import sys, tty, termios, os, argparse

from main import load_json_data, save_json_data

# Used to select/filter artists in a database
# LEFT arrow key  : remove
# RIGHT arrow key : keep

# https://stackoverflow.com/questions/22397289/finding-the-values-of-the-arrow-keys-in-python-why-are-they-triples

class _Getch:
    def __call__(self):
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(3)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return ch

def get():
        inkey = _Getch()
        while(1):
                k=inkey()
                if k!='':break
        if k=='\x1b[A':
                return "up"
        elif k=='\x1b[B':
                return "down"
        elif k=='\x1b[C':
                return "right"
        elif k=='\x1b[D':
                return "left"
        else:
                return ""

def main():

    parser = argparse.ArgumentParser(
        description="Simple interactive artist filter",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )

    parser.add_argument("file", help="file to filter artists from")

    args = parser.parse_args()

    if args.file is None:

        print("You must specify a file to filter artists from")
        exit(1)

    

    artists = load_json_data(args.file)

    for i in range(0, len(artists)):
        os.system('clear')
        print(artists[i]['name'])
        x = get()
        if x == 'left':
            artists.remove(artists[i])
        elif x == 'right':
            pass
        elif x == 'down':
            break
    save_json_data(artists, 'artists_selected.json', 'w') # and here

if __name__=='__main__':
        main()