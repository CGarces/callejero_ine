#!/usr/bin/env python3
"""
Parser de ficheros del callejero/catastro (caj_esp_072025) a DuckDB mediante Parquet.

- Lee ficheros de ancho fijo en ISO-8859-1 (latin-1)
- Usa especificaciones conocidas para SECC, PSEU, VIAS, TRAM y UP
- Para TRAM y UP conserva la línea completa en `raw_line` como referencia
- Escribe un Parquet por fichero de entrada en la carpeta de salida

Dependencias: pandas, pyarrow, duckdb, urllib3
"""
import pathlib
import os
from typing import Iterable, List, Dict, Tuple
from datetime import date

import pandas as pd
import duckdb
import urllib3
import zipfile


FieldSpec = Tuple[str, int, int, str]

DTYPE_MAP = {
    "string": pd.StringDtype(),
    "Int8": pd.Int8Dtype(),
    "Int16": pd.Int16Dtype(),
    "Int32": pd.Int32Dtype(),
    "Int64": pd.Int64Dtype(),
}

# ---------------------------------------------------------------------------
# Especificaciones de ancho fijo conocidas (incluyen dtype esperado)
# ---------------------------------------------------------------------------

# PSEU: longitudes según diseño de pseudovías (total 147)
PSEU_SPEC: List[FieldSpec] = [
    ("cpro", 0, 2, "Int8"),  # Código provincia
    ("cmun", 2, 5, "Int16"),  # Código municipio
    ("acpsvia", 5, 10, "Int32"),  # Código pseudovía
    ("anpsvia", 10, 60, "string"),  # Nombre pseudovía
    ("tipoinf", 60, 61, "string"),
    ("cdev", 61, 63, "string"),
    ("fvar", 63, 71, "Int32"),
    ("cvar", 71, 72, "string"),
    ("ncpsvia", 72, 77, "Int32"),
    ("nnpsvia", 77, 127, "string"),
    ("vector", 127, 147, "string"),
]

# VIAS: longitudes según diseño de vías (total 152)
VIAS_SPEC: List[FieldSpec] = [
    ("cpro", 0, 2, "Int8"),
    ("cmun", 2, 5, "Int16"),
    # ("cvia", 5, 10, "Int32"),
    # ("aviac", 10, 35, "string"),
    # ("tipoinf", 35, 36, "string"),
    # ("cdev", 36, 38, "string"),
    # ("fvar", 38, 46, "Int32"),
    # ("cvar", 46, 47, "string"),
    ("cvia_var", 47, 52, "Int32"),
    ("tvia", 52, 57, "string"),
    # ("nvia", 57, 107, "string"),
    # ("nviac", 107, 132, "string"),
    # ("vector", 132, 152, "string"),
]

SECC_WIDTH = 10

# TRAM: diseño de tramos (total 273 caracteres)
TRAM_SPEC: List[FieldSpec] = [
    # Datos Identificación (inicio)
    ("cpro", 0, 2, "Int8"),
    ("cmun", 2, 5, "Int16"),
    # ("dist", 5, 7, "Int8"),
    # ("secc", 7, 10, "Int16"),
    # ("lsecc", 10, 11, "string"),
    # ("subsc", 11, 13, "string"),
    # ("cun", 13, 20, "Int32"),
    # ("cvia", 20, 25, "Int32"),
    # ("cpsvia", 25, 30, "Int32"),
    # ("manz", 30, 42, "string"),
    ("cpos", 42, 47, "Int32"),
    # ("tinum", 47, 48, "Int8"),
    # ("ein", 48, 52, "Int16"),
    # ("cein", 52, 53, "string"),
    # ("esn", 53, 57, "Int16"),
    # ("cesn", 57, 58, "string"),
    # ("tipoinf", 58, 59, "string"),
    # ("cdev", 59, 61, "string"),
    # ("fvar", 61, 69, "Int32"),
    # ("cvar", 69, 70, "string"),
    # # Datos Variación (final)
    # ("dist_var", 70, 72, "Int8"),
    # ("secc_var", 72, 75, "Int16"),
    # ("lsecc_var", 75, 76, "string"),
    # ("subsc_var", 76, 78, "string"),
    ("cun_var", 78, 85, "Int32"),
    # ("nentcoc", 85, 110, "string"),
    ("nentsic", 110, 135, "string"),
    # ("nnuclec", 135, 160, "string"),
    ("cvia_var", 160, 165, "Int32"),
    ("nviac", 165, 190, "string"),
    # ("cpsvia_var", 190, 195, "Int32"),
    # ("dpsvia", 195, 245, "string"),
    # ("manz_var", 245, 257, "string"),
    # ("cpos_var", 257, 262, "Int32"),
    # ("tinum_var", 262, 263, "Int8"),
    # ("ein_var", 263, 267, "Int16"),
    # ("cein_var", 267, 268, "string"),
    # ("esn_var", 268, 272, "Int16"),
    # ("cesn_var", 272, 273, "string"),
]

# UP: relación de unidades poblacionales (total 604 caracteres)
UP_SPEC: List[FieldSpec] = [
    ("cpro", 0, 2, "Int8"),
    ("cmun", 2, 5, "Int16"),
    ("cun", 5, 12, "Int32"),
    ("tipoinf", 12, 13, "string"),
    ("cdev", 13, 15, "string"),
    ("fvar", 15, 23, "Int32"),
    ("cvar", 23, 24, "string"),
    ("nmun", 24, 94, "string"),
    ("nmun50", 94, 144, "string"),
    ("nmun_c", 144, 169, "string"),
    ("nentco", 169, 239, "string"),
    ("nentco50", 239, 289, "string"),
    ("nentcoc", 289, 314, "string"),
    ("nentsi", 314, 384, "string"),
    ("nentsi50", 384, 434, "string"),
    ("nentsic", 434, 459, "string"),
    ("nnucle", 459, 529, "string"),
    ("nnucle50", 529, 579, "string"),
    ("nnuclec", 579, 604, "string"),
]

# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------


def read_lines(path: pathlib.Path, limit: int | None) -> Iterable[str]:
    """Lee líneas en latin-1 respetando CRLF si existe."""
    with path.open("r", encoding="latin-1", errors="replace", newline="") as f:
        for i, line in enumerate(f):
            if limit is not None and i >= limit:
                break
            yield line.rstrip("\r\n")


def parse_fixed_width(line: str, spec: List[FieldSpec]) -> Dict[str, str]:
    # Garantizar longitud mínima para slicing
    padded = line.ljust(spec[-1][2])
    return {name: padded[start:end] for name, start, end, _ in spec}


def apply_spec(df: pd.DataFrame, spec: List[FieldSpec]) -> pd.DataFrame:
    """Aplica tipado según spec: numéricos a enteros anulables, resto a string."""
    dtype_map = {name: dtype for name, _, _, dtype in spec}

    for col in df.columns:
        dtype = dtype_map.get(col, "string")
        dtype_obj = DTYPE_MAP.get(dtype, pd.StringDtype())
        series = df[col].astype("string").str.strip()

        if dtype.lower().startswith("int"):
            cleaned = series.replace({"": pd.NA})
            df[col] = pd.to_numeric(cleaned, errors="coerce").astype(dtype_obj)
        else:
            df[col] = series.astype(dtype_obj)

    return df


# ---------------------------------------------------------------------------
# Parsers por fichero
# ---------------------------------------------------------------------------


def parse_secc(path: pathlib.Path, limit: int | None) -> pd.DataFrame:
    records = []
    for line in read_lines(path, limit):
        code = line[:SECC_WIDTH].strip()
        records.append({"section_code": code})
    return pd.DataFrame.from_records(records)


def parse_pseu(path: pathlib.Path, limit: int | None) -> pd.DataFrame:
    records = []
    for line in read_lines(path, limit):
        records.append(parse_fixed_width(line, PSEU_SPEC))
    df = pd.DataFrame.from_records(records)
    return apply_spec(df, PSEU_SPEC)


def parse_vias(path: pathlib.Path, limit: int | None) -> pd.DataFrame:
    records = []
    for line in read_lines(path, limit):
        records.append(parse_fixed_width(line, VIAS_SPEC))
    df = pd.DataFrame.from_records(records)
    return apply_spec(df, VIAS_SPEC)


def parse_tram(path: pathlib.Path, limit: int | None) -> pd.DataFrame:
    records = []
    for line in read_lines(path, limit):
        row = parse_fixed_width(line, TRAM_SPEC)
        # row["raw_line"] = line
        records.append(row)
    df = pd.DataFrame.from_records(records)
    return apply_spec(df, TRAM_SPEC)


def parse_up(path: pathlib.Path, limit: int | None) -> pd.DataFrame:
    records = []
    for line in read_lines(path, limit):
        row = parse_fixed_width(line, UP_SPEC)
        # row["raw_line"] = line
        records.append(row)
    df = pd.DataFrame.from_records(records)
    return apply_spec(df, UP_SPEC)


PARSERS = {
    "SECC": parse_secc,
    "PSEU": parse_pseu,
    "VIAS": parse_vias,
    "TRAM": parse_tram,
    "UP": parse_up,
}


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


def main():
    output_dir = pathlib.Path("output")
    input_dir = pathlib.Path("input")

    # Elimina los directorios de trabajo previos
    remove_directory_tree(output_dir)
    remove_directory_tree(input_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    input_dir.mkdir(parents=True, exist_ok=True)

    get_ine_file(input_dir)
    con = duckdb.connect()
    # Elimina el fichero de base de datos previo
    if os.path.exists("callejero.duckdb"):
        os.remove("callejero.duckdb")
    con.execute("ATTACH 'callejero.duckdb'")

    for stem, func in PARSERS.items():
        files = sorted(input_dir.glob(f"caj_esp_??????/{stem}*.*"))
        if not files:
            print(f"[WARN] No se encontró fichero para {stem} en {input_dir}")
            continue
        path = files[0]
        table = path.stem.split(".", 1)[0]
        if table not in ["VIAS", "TRAM"]:
            print(f"[INFO] Saltando {path.name} (no se carga en BBDD final)")
            continue
        print(f"[INFO] Procesando {path.name} -> Parquet")
        df = func(path, None)
        df = df.drop_duplicates()
        out_path = output_dir / f"{path.stem.split(".", 1)[0]}.parquet"
        df.to_parquet(out_path, index=False, engine="pyarrow", compression="gzip")
        print(f"[OK] {out_path} ({len(df)} filas)")
        # Carga en DuckDB
        con.execute(f"CREATE TABLE {stem} AS SELECT * FROM read_parquet('{out_path}')")

    con.execute("COPY FROM DATABASE memory TO callejero")
    con.execute("DETACH callejero")


if __name__ == "__main__":
    main()
