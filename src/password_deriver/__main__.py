import string
import argparse
import subprocess
import getpass
import hashlib
import random
import pathlib
import json
import sys

from . import config, algorithms


FINGERPRINT_CHARS = [" ", "░", "▒", "▓", "█"]


if sys.platform.startswith("linux"):
    def write_to_clipboard(data):
        process = subprocess.Popen("wl-copy", stdin=subprocess.PIPE)
        process.communicate(data.encode("ascii"))
        print("The password is copied to the clipboard")
elif sys.platform.startswith("darwin"):
    def write_to_clipboard(data):
        process = subprocess.Popen("pbcopy", stdin=subprocess.PIPE)
        process.communicate(data.encode("ascii"))
        print("The password is copied to the clipboard")


def password_hash(password, salt):
    return hashlib.scrypt(
        password, salt=salt, n=2 ** 15, r=8, p=1, maxmem=64 * 1024 ** 2
    )


def get_master_password():
    salt = config.get_or_init_salt().encode("ascii")
    master_password = getpass.getpass("Enter the master passphrase: ").encode("utf-8")
    h = config.get_master_password_hash()
    if h is not None:
        while password_hash(master_password, salt) != h:
            master_password = getpass.getpass("Wrong master passphrase, try again: ").encode("utf-8")
    else:
        r = getpass.getpass("Repeat the master passphrase: ").encode("utf-8")
        while master_password != r:
            print("Passphrases don't match. Let's do this again.")
            master_password = getpass.getpass("Enter the master passphrase: ").encode("utf-8")
            r = getpass.getpass("Repeat the master passphrase: ").encode("utf-8")
        h = password_hash(master_password, salt)
        config.set_master_password_hash(h)

    return master_password


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("specs")
    parser.add_argument("--print", action="store_true")
    args = parser.parse_args()
    specs = json.loads(args.specs)
    for spec in specs:
        if "error" in spec:
            exit(spec["error"])
    action = print if args.print else write_to_clipboard
    master_password = get_master_password()

    for spec in specs:
        password = algorithms.derive_and_format(master_password, spec)
        action(password)


if __name__ == "__main__":
    main()
