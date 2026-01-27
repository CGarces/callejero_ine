import os
import zipfile
from datetime import date
import pathlib
import urllib3


def remove_directory_tree(start_directory: pathlib.Path):
    """Elimina de forma recursiva y permanente el directorio especificado, todos sus
    subdirectorios y cada archivo contenido en cualquiera de esas carpetas."""
    if not start_directory.exists():
        return

    for path in start_directory.iterdir():
        if path.is_file():
            path.unlink()
        else:
            remove_directory_tree(path)
    start_directory.rmdir()


def get_ine_file(input_dir: pathlib.Path):
    """Descarga el fichero del callejero del INE y lo descomprime en input_dir."""
    # Descarga ficheros de callejero desde la URL del INE
    http_pool = urllib3.PoolManager()
    # El fichero puede ser de Enero o Julio, se prueban ambas variantes
    today = date.today()
    fechas: list[str] = []

    if today.month >= 7:
        fechas.append(f"07{today.year}")
        fechas.append(f"01{today.year-1}")
    else:
        fechas.append(f"01{today.year}")
        fechas.append(f"07{today.year-1}")

    for fecha in fechas:
        file = f"caj_esp_{fecha}.zip"
        url = f"https://www.ine.es/prodyser/callejero/caj_esp/{file}"
        response = http_pool.request("GET", url)
        if response.status == 200:
            with open(f"/tmp/{file}", "wb") as f:
                f.write(response.data)
            # unzip

            with zipfile.ZipFile(f"/tmp/{file}", "r") as zip_ref:
                zip_ref.extractall(input_dir)
            print(f"[OK] Fichero descargado y descomprimido: {file}")
            os.remove(f"/tmp/{file}")
            return None
        print(
            f"[WARN] No se encontró fichero para periodo {fecha} (HTTP {response.status})"
        )

    raise RuntimeError("No se pudo descargar ningún fichero del callejero del INE")


def main():
    output_dir = pathlib.Path("output")
    input_dir = pathlib.Path("input")

    # Elimina los directorios de trabajo previos
    remove_directory_tree(output_dir)
    remove_directory_tree(input_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    input_dir.mkdir(parents=True, exist_ok=True)

    get_ine_file(input_dir)


if __name__ == "__main__":
    main()
