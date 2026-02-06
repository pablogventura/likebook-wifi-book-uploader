#!/usr/bin/env python3
"""
Script para obtener la lista de libros desde WiFi Book Transfer (http://192.168.1.196:8080/)
Usa la API JSON /files que devuelve un array con {name, size} por cada archivo.
"""

import argparse
import os
import sys
import time
from urllib.parse import quote

import requests

BASE_URL = "http://192.168.1.196:8080"
FILES_URL = f"{BASE_URL}/files"


def obtener_lista_libros():
    """Obtiene la lista de libros desde la API JSON de WiFi Book Transfer."""
    try:
        # El cliente JS usa timestamp para evitar caché
        url = f"{FILES_URL}?{int(time.time() * 1000)}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con {BASE_URL}: {e}")
        return []
    except ValueError as e:
        print(f"Error al parsear JSON: {e}")
        return []


def descargar_libro(nombre: str, directorio: str = ".") -> bool:
    """Descarga un libro por su nombre. Devuelve True si tuvo éxito."""
    try:
        url = f"{FILES_URL}/{quote(nombre, safe='')}"
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        ruta = os.path.join(directorio, nombre)
        with open(ruta, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error al descargar '{nombre}': {e}", file=sys.stderr)
        return False
    except OSError as e:
        print(f"Error al guardar '{nombre}': {e}", file=sys.stderr)
        return False


def subir_libro(ruta: str) -> bool:
    """Sube un libro desde una ruta local. Devuelve True si tuvo éxito."""
    if not os.path.isfile(ruta):
        print(f"El archivo '{ruta}' no existe.", file=sys.stderr)
        return False

    nombre = os.path.basename(ruta)
    formatos = (
        "epub", "txt", "pdf", "mobi", "azw", "azw3", "fb2", "doc", "docx",
        "htm", "html", "cbz", "cbt", "cbr", "jvu", "djvu", "djv", "rtf",
        "zip", "rar",
    )
    if not nombre.lower().endswith(tuple(f".{ext}" for ext in formatos)):
        print(f"Formato no soportado: {nombre}", file=sys.stderr)
        return False

    try:
        with open(ruta, "rb") as f:
            files = {"newfile": (nombre, f)}
            data = {"fileName": quote(nombre)}
            response = requests.post(FILES_URL, files=files, data=data, timeout=120)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error al subir '{nombre}': {e}", file=sys.stderr)
        return False
    except OSError as e:
        print(f"Error al leer '{ruta}': {e}", file=sys.stderr)
        return False


def borrar_libro(nombre: str) -> bool:
    """Borra un libro por su nombre. Devuelve True si tuvo éxito."""
    try:
        url = f"{FILES_URL}/{quote(nombre, safe='')}"
        response = requests.post(url, data={"_method": "delete"}, timeout=10)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error al borrar '{nombre}': {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Lista, descarga, sube y borra libros desde WiFi Book Transfer."
    )
    parser.add_argument(
        "-d", "--delete",
        metavar="NOMBRE_O_ÍNDICE",
        help="Borra el libro indicado por nombre o por número de índice (ej: 1, 5)",
    )
    parser.add_argument(
        "-g", "--download",
        metavar="NOMBRE_O_ÍNDICE",
        dest="download",
        help="Descarga el libro indicado por nombre o por número de índice",
    )
    parser.add_argument(
        "-o", "--output",
        default=".",
        metavar="DIRECTORIO",
        help="Directorio donde guardar la descarga (por defecto: directorio actual)",
    )
    parser.add_argument(
        "-u", "--upload",
        metavar="ARCHIVO",
        nargs="+",
        dest="upload",
        help="Sube uno o más archivos (ej: libro.pdf o libro1.pdf libro2.epub)",
    )
    args = parser.parse_args()

    print(f"Obteniendo lista de libros desde {BASE_URL}...\n")
    libros = obtener_lista_libros()

    if not libros and not args.upload:
        print("No se encontraron libros.")
        return 1

    if libros:
        print(f"Libros encontrados ({len(libros)}):\n")
        for i, item in enumerate(libros, 1):
            nombre = item.get("name", "?")
            tamaño = item.get("size", "")
            print(f"  {i}. {nombre}  ({tamaño})")

    if args.upload:
        for ruta in args.upload:
            ruta = os.path.expanduser(ruta.strip())
            print(f"\nSubiendo '{ruta}'...")
            if subir_libro(ruta):
                print(f"✓ Subido: {os.path.basename(ruta)}")
            else:
                return 1

    if args.delete and libros:
        target = args.delete.strip()
        # Si es un número, buscar por índice
        if target.isdigit():
            idx = int(target)
            if 1 <= idx <= len(libros):
                nombre = libros[idx - 1].get("name", "")
            else:
                print(f"Índice inválido. Usa un número entre 1 y {len(libros)}.", file=sys.stderr)
                return 1
        else:
            nombre = target
            if not any(lib.get("name") == nombre for lib in libros):
                print(f"No se encontró el libro '{nombre}'.", file=sys.stderr)
                return 1

        confirmar = input(f"\n¿Borrar '{nombre}'? [s/N]: ").strip().lower()
        if confirmar in ("s", "si", "sí", "y", "yes"):
            if borrar_libro(nombre):
                print(f"✓ Borrado: {nombre}")
            else:
                return 1
        else:
            print("Cancelado.")

    if args.download and libros:
        target = args.download.strip()
        if target.isdigit():
            idx = int(target)
            if 1 <= idx <= len(libros):
                nombre = libros[idx - 1].get("name", "")
            else:
                print(f"Índice inválido. Usa un número entre 1 y {len(libros)}.", file=sys.stderr)
                return 1
        else:
            nombre = target
            if not any(lib.get("name") == nombre for lib in libros):
                print(f"No se encontró el libro '{nombre}'.", file=sys.stderr)
                return 1

        output_dir = os.path.expanduser(args.output)
        if not os.path.isdir(output_dir):
            print(f"El directorio '{output_dir}' no existe.", file=sys.stderr)
            return 1

        print(f"\nDescargando '{nombre}'...")
        if descargar_libro(nombre, output_dir):
            print(f"✓ Guardado: {os.path.join(output_dir, nombre)}")
        else:
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
