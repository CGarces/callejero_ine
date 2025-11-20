from fastapi import FastAPI, HTTPException, status, Response
import duckdb

app = FastAPI()
con = duckdb.connect(":memory:")
con.execute("CREATE TABLE TRAM AS SELECT * FROM read_parquet('./output/TRAM.parquet')")
# con.execute("CREATE TABLE UP AS SELECT * FROM read_parquet('./output/UP.parquet')")


@app.get(
    "/CMUN/{cpos}",
    summary="Localidades por código postal",
    responses={
        200: {"description": "Listado de localidades para el CP"},
        204: {"description": "Sin contenido: el CP parcial tiene menos de 3 dígitos"},
        400: {"description": "Petición inválida: el CP no es numérico"},
        404: {"description": "No se encontraron localidades para el CP"},
    },
)
def get_localidades_by_cp(cpos: str):
    """
    Devuelve el codigo de provincia, municipio y descripcion para un codigo postal (cpos).
    Permite busquedas parciales con un minimo de 3 caracteres
    """
    if not cpos.isdigit():
        raise HTTPException(status_code=400, detail="cpos debe ser numérico")

    if len(cpos) < 3:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    sql = """
        SELECT cpos, cpro, cmun,  NENTSIC
        FROM TRAM
    """

    cur = None
    if len(cpos) == 5:
        sql += "WHERE cpos = ?  GROUP BY cpos, cpro, cmun,  NENTSIC "
        cur = con.execute(sql, [int(cpos)])
    else:
        # Se completa con valores a la derecha para busquedas parciales, respetando los ceros a la izquierda
        cpos_min = int(cpos.ljust(5, "0"))
        cpos_max = int(cpos.ljust(5, "9"))

        sql += "WHERE cpos BETWEEN ? and ? GROUP BY cpos, cpro, cmun, NENTSIC"
        cur = con.execute(sql, [cpos_min, cpos_max])

    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    items = [dict(zip(cols, r)) for r in rows]

    if not items:
        raise HTTPException(status_code=404, detail="Sin resultados para ese CP")

    return items


@app.get(
    "/{cpro}/{cmun}",
    summary="Codigos postales por provincia y municipio",
    responses={
        200: {"description": "Listado de codigos postales para la provincia/municipio"},
        404: {"description": "Sin resultados para la provincia/municipio"},
    },
)
def get_localidades_by_cpro_cnum(cpro: int, cmun: int):
    """
    Devuelve el codigo de provincia, municipio y descripcion para un codigo codigo de provincia y municipo.
    """
    cur = con.execute(
        """
        SELECT cpos, cpro, cmun,  NENTSIC
        FROM TRAM
        WHERE cpro = ? AND cmun = ?
        GROUP BY cpos, cpro, cmun,  NENTSIC
    """,
        [cpro, cmun],
    )

    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    items = [dict(zip(cols, r)) for r in rows]

    if not items:
        raise HTTPException(
            status_code=404, detail="Sin resultados para esa provincia/municipio"
        )

    return items


@app.get(
    "/{cpro}/{cmun}/{cun}",
    summary="Codigos postales por unicas poblacional",
    responses={
        200: {
            "description": "Listado de codigos postales para la provincia/municipio/cun"
        },
        404: {"description": "Sin resultados para la provincia/municipio/cun"},
    },
)
def get_by_cun(cpro: int, cmun: int, cun: int):
    """Devuelve el codigo de provincia, municipio, unidad poblacional y descripcion de una unidad poblacional."""

    cur = con.execute(
        """
        SELECT cpos, cpro, cmun, cun_var, NENTSIC
        FROM TRAM
        WHERE cpro = ? AND cmun = ? AND cun_var = ?
        GROUP BY cpos, cpro, cmun, cun_var, NENTSIC
    """,
        [cpro, cmun, cun],
    )

    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    items = [dict(zip(cols, r)) for r in rows]

    if not items:
        raise HTTPException(
            status_code=404, detail="Sin resultados para esa provincia/municipio"
        )

    return items


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
