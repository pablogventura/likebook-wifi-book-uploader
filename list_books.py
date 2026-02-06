#!/usr/bin/env python3
"""
Script to get the list of books from WiFi Book Transfer (http://192.168.1.196:8080/).
Uses the JSON API /files which returns an array with {name, size} for each file.
"""

import argparse
import os
import sys
import time
from urllib.parse import quote

import requests

BASE_URL = "http://192.168.1.196:8080"
FILES_URL = f"{BASE_URL}/files"


def get_book_list():
    """Fetches the list of books from the WiFi Book Transfer JSON API."""
    try:
        # JS client uses timestamp to avoid cache
        url = f"{FILES_URL}?{int(time.time() * 1000)}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to {BASE_URL}: {e}")
        return []
    except ValueError as e:
        print(f"Error parsing JSON: {e}")
        return []


def download_book(name: str, directory: str = ".") -> bool:
    """Downloads a book by name. Returns True on success."""
    try:
        url = f"{FILES_URL}/{quote(name, safe='')}"
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        path = os.path.join(directory, name)
        with open(path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error downloading '{name}': {e}", file=sys.stderr)
        return False
    except OSError as e:
        print(f"Error saving '{name}': {e}", file=sys.stderr)
        return False


def upload_book(path: str) -> bool:
    """Uploads a book from a local path. Returns True on success."""
    if not os.path.isfile(path):
        print(f"File '{path}' does not exist.", file=sys.stderr)
        return False

    name = os.path.basename(path)
    formats = (
        "epub", "txt", "pdf", "mobi", "azw", "azw3", "fb2", "doc", "docx",
        "htm", "html", "cbz", "cbt", "cbr", "jvu", "djvu", "djv", "rtf",
        "zip", "rar",
    )
    if not name.lower().endswith(tuple(f".{ext}" for ext in formats)):
        print(f"Unsupported format: {name}", file=sys.stderr)
        return False

    try:
        with open(path, "rb") as f:
            files = {"newfile": (name, f)}
            data = {"fileName": quote(name)}
            response = requests.post(FILES_URL, files=files, data=data, timeout=120)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error uploading '{name}': {e}", file=sys.stderr)
        return False
    except OSError as e:
        print(f"Error reading '{path}': {e}", file=sys.stderr)
        return False


USAGE_HELP = """
Usage:
  %(prog)s                    List books (this output)
  %(prog)s -g 3               Download book by index
  %(prog)s -g "book.pdf"      Download book by name
  %(prog)s -g 1 -o ~/books    Download to specific directory
  %(prog)s -u book.pdf        Upload a file
  %(prog)s -u f1.pdf f2.epub  Upload multiple files
  %(prog)s -d 5               Delete book by index (asks confirmation)
  %(prog)s -d "book.pdf"      Delete book by name
  %(prog)s -h                 Show full help
"""


def delete_book(name: str) -> bool:
    """Deletes a book by name. Returns True on success."""
    try:
        url = f"{FILES_URL}/{quote(name, safe='')}"
        response = requests.post(url, data={"_method": "delete"}, timeout=10)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error deleting '{name}': {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="List, download, upload and delete books from WiFi Book Transfer."
    )
    parser.add_argument(
        "-d", "--delete",
        metavar="NAME_OR_INDEX",
        help="Delete the book specified by name or index number (e.g. 1, 5)",
    )
    parser.add_argument(
        "-g", "--download",
        metavar="NAME_OR_INDEX",
        dest="download",
        help="Download the book specified by name or index number",
    )
    parser.add_argument(
        "-o", "--output",
        default=".",
        metavar="DIRECTORY",
        help="Directory to save the download (default: current directory)",
    )
    parser.add_argument(
        "-u", "--upload",
        metavar="FILE",
        nargs="+",
        dest="upload",
        help="Upload one or more files (e.g. book.pdf or book1.pdf book2.epub)",
    )
    args = parser.parse_args()

    print(f"Fetching book list from {BASE_URL}...\n")
    books = get_book_list()

    if not books and not args.upload:
        print("No books found.")
        return 1

    if books:
        print(f"Books found ({len(books)}):\n")
        for i, item in enumerate(books, 1):
            name = item.get("name", "?")
            size = item.get("size", "")
            print(f"  {i}. {name}  ({size})")
        print(USAGE_HELP % {"prog": parser.prog})

    if args.upload:
        for path in args.upload:
            path = os.path.expanduser(path.strip())
            print(f"\nUploading '{path}'...")
            if upload_book(path):
                print(f"✓ Uploaded: {os.path.basename(path)}")
            else:
                return 1

    if args.delete and books:
        target = args.delete.strip()
        # If it's a number, look up by index
        if target.isdigit():
            idx = int(target)
            if 1 <= idx <= len(books):
                name = books[idx - 1].get("name", "")
            else:
                print(f"Invalid index. Use a number between 1 and {len(books)}.", file=sys.stderr)
                return 1
        else:
            name = target
            if not any(book.get("name") == name for book in books):
                print(f"Book '{name}' not found.", file=sys.stderr)
                return 1

        confirm = input(f"\nDelete '{name}'? [y/N]: ").strip().lower()
        if confirm in ("s", "si", "sí", "y", "yes"):
            if delete_book(name):
                print(f"✓ Deleted: {name}")
            else:
                return 1
        else:
            print("Cancelled.")

    if args.download and books:
        target = args.download.strip()
        if target.isdigit():
            idx = int(target)
            if 1 <= idx <= len(books):
                name = books[idx - 1].get("name", "")
            else:
                print(f"Invalid index. Use a number between 1 and {len(books)}.", file=sys.stderr)
                return 1
        else:
            name = target
            if not any(book.get("name") == name for book in books):
                print(f"Book '{name}' not found.", file=sys.stderr)
                return 1

        output_dir = os.path.expanduser(args.output)
        if not os.path.isdir(output_dir):
            print(f"Directory '{output_dir}' does not exist.", file=sys.stderr)
            return 1

        print(f"\nDownloading '{name}'...")
        if download_book(name, output_dir):
            print(f"✓ Saved: {os.path.join(output_dir, name)}")
        else:
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
