# Likebook WiFi Book Uploader

CLI to manage books on a Likebook (or compatible) e-reader running WiFi Book Transfer. List, download, upload, and delete books from the command line.

## Requirements

- Python 3.8+
- E-reader with WiFi Book Transfer enabled and on the same network

## Installation

```bash
pip install -r requirements.txt
```

## Usage

If no host is specified, the script scans your local network for the WiFi Book Transfer server.

```bash
# List books (auto-discovers server)
python likebook-wifi-book-uploader.py

# Use specific IP
python likebook-wifi-book-uploader.py -H 192.168.1.196

# Download book by index
python likebook-wifi-book-uploader.py -g 3

# Download book by name
python likebook-wifi-book-uploader.py -g "book.pdf"

# Download to specific directory
python likebook-wifi-book-uploader.py -g 1 -o ~/books

# Upload file(s)
python likebook-wifi-book-uploader.py -u book.pdf
python likebook-wifi-book-uploader.py -u book1.pdf book2.epub

# Delete book (asks confirmation)
python likebook-wifi-book-uploader.py -d 5
python likebook-wifi-book-uploader.py -d "book.pdf"

# Full help
python likebook-wifi-book-uploader.py -h
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
