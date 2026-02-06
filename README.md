# Likebook WiFi Book Uploader

CLI to manage books on a Likebook (or compatible) e-reader running WiFi Book Transfer. List, download, upload, and delete books from the command line.

## Requirements

- Python 3.8+
- E-reader with WiFi Book Transfer enabled and on the same network

## Installation

**With pipx (recommended):**

```bash
pipx install .
```

Or from the git repository:

```bash
pipx install git+https://github.com/pablogventura/likebook-wifi-book-uploader.git
```

**With pip:**

```bash
pip install .
```

**Without installing (run from source):**

```bash
pip install -r requirements.txt
python likebook_wifi_book_uploader.py
```

## Usage

If no host is specified, the script scans your local network for the WiFi Book Transfer server.

```bash
# List books (auto-discovers server)
likebook-wifi-book-uploader

# Use specific IP
likebook-wifi-book-uploader -H 192.168.1.196

# Download book by index
likebook-wifi-book-uploader -g 3

# Download book by name
likebook-wifi-book-uploader -g "book.pdf"

# Download to specific directory
likebook-wifi-book-uploader -g 1 -o ~/books

# Upload file(s)
likebook-wifi-book-uploader -u book.pdf
likebook-wifi-book-uploader -u book1.pdf book2.epub

# Delete book (asks confirmation)
likebook-wifi-book-uploader -d 5
likebook-wifi-book-uploader -d "book.pdf"

# Full help
likebook-wifi-book-uploader -h
```

## Options

| Option | Description |
|--------|-------------|
| `-H`, `--host IP` | Server IP (auto-discovers on local network if omitted) |
| `-g`, `--download NAME_OR_INDEX` | Download book by name or index |
| `-o`, `--output DIR` | Output directory for downloads (default: current) |
| `-u`, `--upload FILE...` | Upload one or more files |
| `-d`, `--delete NAME_OR_INDEX` | Delete book by name or index |
| `-h`, `--help` | Show help |

## Supported formats

EPUB, TXT, PDF, MOBI, AZW, AZW3, FB2, DOC, DOCX, HTM, HTML, CBZ, CBT, CBR, JVU, DJVU, DJV, RTF, ZIP, RAR
