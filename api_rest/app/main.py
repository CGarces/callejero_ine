import time
from fastapi import FastAPI, HTTPException, status, Response
import duckdb

app = FastAPI()
start = time.time()
con = duckdb.connect("callejero.duckdb", config={"access_mode": "READ_ONLY"})
end = time.time()
print(f"Loaded TRAM table in {end - start:.2f} seconds")


@app.get(
    "/cp/{cpos}",
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
    "/cp/{cpos}/{nviac}",
    summary="Busqueda de calles por codigo postal y coincidencia parcial",
    responses={
        200: {
            "description": "Listado de calles para un codigo postal y una coincidencia parcial"
        },
        404: {
            "description": "Sin resultados para la el codigo postal y el texto parcial"
        },
    },
)
def get_via_by_cpos(cpos: int, nviac: str):
    """Devuelve el nombre de la via en funcion del codigo postal y una coincidencia parcial."""

    if len(nviac) < 3:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    cur = con.execute(
        """
        SELECT cpos, TRAM.cpro, TRAM.cmun, TRAM.cvia, NENTSIC, TVIA, NVIA
        FROM TRAM
        INNER JOIN VIAS ON TRAM.cpro = VIAS.cpro AND TRAM.cmun = VIAS.cmun AND TRAM.cvia = VIAS.cvia
        WHERE cpos = ? and TRAM.nviac LIKE ?
        GROUP BY cpos, TRAM.cpro, TRAM.cmun, TRAM.cvia,  NENTSIC, TVIA, NVIA
    """,
        [cpos, f"%{nviac.upper()}%"],
    )

    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    items = [dict(zip(cols, r)) for r in rows]

    if not items:
        raise HTTPException(
            status_code=404,
            detail="Sin resultados para la el codigo postal y el texto parcial",
        )

    # Capitaliza TVIA, NVIA en la respuesta
    items = [
        {**item, "tvia": item["tvia"].title(), "nvia": item["nvia"].title()}
        for item in items
    ]

    return items


@app.get(
    "/{cpro}/{cmun}/{cun}/{nviac}",
    summary="Busqueda de calles por por unidad poblacional y una coincidencia parcial",
    responses={
        200: {
            "description": "Listado de calles para la provincia/municipio/unidad poblacional y una coincidencia parcial"
        },
        404: {
            "description": "Sin resultados para la provincia/municipio/unidad poblacional"
        },
    },
)
def get_via_by_cun(cpro: int, cmun: int, cun: int, nviac: str):
    """Devuelve el nombre de la via en funcion del la unidad poblacional y una coincidencia parcial."""

    if len(nviac) < 3:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    cur = con.execute(
        """
        SELECT cpos, TRAM.cpro, TRAM.cmun, TRAM.cvia, TRAM.cun, NENTSIC, TVIA, NVIA
        FROM TRAM
        INNER JOIN VIAS ON TRAM.cpro = VIAS.cpro AND TRAM.cmun = VIAS.cmun AND TRAM.cvia = VIAS.cvia
        WHERE TRAM.cpro = ? and TRAM.cmun = ? and TRAM.cun = ? and TRAM.nviac LIKE ?
        GROUP BY  cpos, TRAM.cpro, TRAM.cmun, TRAM.cvia, TRAM.cun, NENTSIC, TVIA, NVIA
    """,
        [cpro, cmun, cun, f"%{nviac.upper()}%"],
    )

    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    items = [dict(zip(cols, r)) for r in rows]

    if not items:
        raise HTTPException(
            status_code=404,
            detail="Sin resultados para la provincia/municipio/unidad poblacional",
        )

    # Capitaliza TVIA, NVIA en la respuesta
    # La funcion init_cap no existe en DUCKDB, y realizar SUBSTR es lijeramente mas costoso
    # TODO Reevaluar si se imeplenta https://github.com/duckdb/duckdb/discussions/12999
    items = [
        {**item, "tvia": item["tvia"].title(), "nvia": item["nvia"].title()}
        for item in items
    ]

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
    summary="Codigos postales por unidad poblacional",
    responses={
        200: {
            "description": "Listado de codigos postales para la provincia/municipio/unidad poblacional"
        },
        404: {
            "description": "Sin resultados para la provincia/municipio/unidad poblacional"
        },
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
            status_code=404,
            detail="Sin resultados para esa provincia/municipio/unidad poblacional ",
        )

    return items
