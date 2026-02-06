#!/usr/bin/env python3
"""
Script to get the list of books from WiFi Book Transfer.
Uses the JSON API /files which returns an array with {name, size} for each file.
If --host is not given, scans the local network to find the server.
"""

import argparse
import os
import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional
from urllib.parse import quote

import requests

WIFI_BOOK_PORT = 8080


def _get_subnet_ips():
    """Get IPs to scan based on local network. Returns list of IP strings."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        local_ip = s.getsockname()[0]
    except OSError:
        # Fallback: scan common home subnets
        return [f"192.168.{a}.{b}" for a in (0, 1) for b in range(1, 255)]
    finally:
        s.close()

    parts = local_ip.split(".")
    if len(parts) != 4:
        return []
    base = ".".join(parts[:3])
    return [f"{base}.{i}" for i in range(1, 255)]


def _check_host(ip: str, timeout: float = 2) -> Optional[str]:
    """Check if host runs WiFi Book Transfer. Returns IP if found, else None."""
    try:
        url = f"http://{ip}:{WIFI_BOOK_PORT}/"
        r = requests.get(url, timeout=timeout)
        if r.status_code == 200 and "WiFi Book Transfer" in r.text:
            return ip
    except requests.exceptions.RequestException:
        pass
    return None


def discover_servers() -> list[str]:
    """Scan local network for WiFi Book Transfer servers. Returns list of IPs."""
    ips = _get_subnet_ips()
    found = []
    with ThreadPoolExecutor(max_workers=64) as executor:
        futures = {executor.submit(_check_host, ip): ip for ip in ips}
        for future in as_completed(futures):
            result = future.result()
            if result:
                found.append(result)
    return sorted(found)


def get_book_list(base_url: str):
    """Fetches the list of books from the WiFi Book Transfer JSON API."""
    files_url = f"{base_url}/files"
    try:
        # JS client uses timestamp to avoid cache
        url = f"{files_url}?{int(time.time() * 1000)}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to {base_url}: {e}")
        return []
    except ValueError as e:
        print(f"Error parsing JSON: {e}")
        return []


def download_book(name: str, directory: str, base_url: str) -> bool:
    """Downloads a book by name. Returns True on success."""
    files_url = f"{base_url}/files"
    try:
        url = f"{files_url}/{quote(name, safe='')}"
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


def upload_book(path: str, base_url: str) -> bool:
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

    files_url = f"{base_url}/files"
    try:
        with open(path, "rb") as f:
            files = {"newfile": (name, f)}
            data = {"fileName": quote(name)}
            response = requests.post(files_url, files=files, data=data, timeout=120)
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
  %(prog)s -H 192.168.1.196   Use specific host IP (or auto-discover if omitted)
  %(prog)s -h                 Show full help
"""


def delete_book(name: str, base_url: str) -> bool:
    """Deletes a book by name. Returns True on success."""
    files_url = f"{base_url}/files"
    try:
        url = f"{files_url}/{quote(name, safe='')}"
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
    parser.add_argument(
        "-H", "--host",
        metavar="IP",
        help="WiFi Book Transfer server IP (auto-discovers on local network if omitted)",
    )
    args = parser.parse_args()

    if args.host:
        base_url = f"http://{args.host.strip()}:{WIFI_BOOK_PORT}"
    else:
        print("Scanning local network for WiFi Book Transfer...")
        servers = discover_servers()
        if not servers:
            print("No WiFi Book Transfer server found. Use -H IP to specify manually.", file=sys.stderr)
            return 1
        base_url = f"http://{servers[0]}:{WIFI_BOOK_PORT}"
        if len(servers) > 1:
            print(f"Found: {', '.join(servers)}")
        print(f"Using: {base_url}\n")

    print(f"Fetching book list from {base_url}...\n")
    books = get_book_list(base_url)

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
            if upload_book(path, base_url):
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
            if delete_book(name, base_url):
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
        if download_book(name, output_dir, base_url):
            print(f"✓ Saved: {os.path.join(output_dir, name)}")
        else:
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
