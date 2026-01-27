import os
import zipfile
from datetime import date
import pathlib
import urllib3


def check_s3_file_exists(file) -> bool:
    """Comprueba si el callejero de S3 se corresponde con el origen de datos."""
    try:
        # El import se hace inline, esto es intencianado para hacer este paso opcional.
        # Si boto3 no está instalado, o el usuario no tiene accesso simplemente se ignora esta función.
        # Esto permite ejecutar el script en entornos sin AWS configurado.
        import boto3

        s3_client = boto3.client("s3")
        response = s3_client.head_object(
            Bucket="callejero-dev-cloudfront", Key="callejero.duckdb"
        )
        if "Metadata" in response and response["Metadata"].get("source") == file:
            print(f"[OK] Fichero ya existe en S3: {file}")
            return True
    except Exception:
        pass  # Si hay error, se asume que no existe y se continúa
    return False


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


def upload_s3(file: str):
    try:
        import boto3

        s3_client = boto3.client("s3")
        s3_client.upload_file(
            Filename=f"/tmp/{file}",
            Bucket="callejero-dev-cloudfront",
            Key="callejero.duckdb",
            ExtraArgs={"Metadata": {"source": file}},
        )
        print(f"[OK] Fichero subido a S3: {file}")
    except Exception:
        # Se ignoran intencionadamente los errores para permitir trabajar sin AWS
        pass


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
        response = http_pool.request("HEAD", url)
        if response.status == 200:
            # Se comprueba si el fichero ya existe en S3
            if check_s3_file_exists(file):
                return None

            response = http_pool.request("GET", url)
            with open(f"/tmp/{file}", "wb") as f:
                f.write(response.data)

            # unzip
            with zipfile.ZipFile(f"/tmp/{file}", "r") as zip_ref:
                zip_ref.extractall(input_dir)
            print(f"[OK] Fichero descargado y descomprimido: {file}")
            os.remove(f"/tmp/{file}")
            return file
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

    file = get_ine_file(input_dir)
    if file is None:
        # Si devuelve None, el fichero ya estaba en S3 y no es necesario continuar
        print("[INFO] Fichero ya actualizado en S3, no es necesario procesar nada.")
        return

    print("[INFO] Parseando archivos a DuckDB...")
    from parse_callejero import main as parse_main

    parse_main()

    # Se sube el fichero a S3 con metadata indicando el origen
    upload_s3(file)

    print("[OK] Pipeline completo: descarga → parseo → DuckDB")


if __name__ == "__main__":
    main()
