import time
from fastapi import FastAPI, HTTPException, status, Response
import duckdb

app = FastAPI(root_path="/api")
start = time.time()
con = duckdb.connect("callejero.duckdb", config={"access_mode": "READ_ONLY"})
end = time.time()
print(f"Loaded TRAM table in {end - start:.2f} seconds")

dict_auto = {
    "01": "ANDALUCIA",
    "02": "ARAGON",
    "03": "ASTURIAS",
    "04": "BALEARES",
    "05": "CANARIAS",
    "06": "CANTABRIA",
    "07": "CASTILLA Y LEON",
    "08": "CASTILLA LA MANCHA",
    "09": "CATALUNA",
    "10": "COMUNITAT VALENCIANA",
    "11": "EXTREMADURA",
    "12": "GALICIA",
    "13": "MADRID",
    "14": "MURCIA",
    "15": "NAVARRA",
    "16": "PAIS VASCO",
    "17": "RIOJA, LA",
    "18": "CEUTA",
    "19": "MELILLA",
}

dict_provincia = {
    "01": {"PRO": "ALAVA", "CCOM": "16"},
    "02": {"PRO": "ALBACETE", "CCOM": "08"},
    "03": {"PRO": "ALICANTE/ALACANT", "CCOM": "10"},
    "04": {"PRO": "ALMERIA", "CCOM": "01"},
    "05": {"PRO": "AVILA", "CCOM": "07"},
    "06": {"PRO": "BADAJOZ", "CCOM": "11"},
    "07": {"PRO": "BALEARS, ILLES", "CCOM": "04"},
    "08": {"PRO": "BARCELONA", "CCOM": "09"},
    "09": {"PRO": "BURGOS", "CCOM": "07"},
    "10": {"PRO": "CACERES", "CCOM": "11"},
    "11": {"PRO": "CADIZ", "CCOM": "01"},
    "12": {"PRO": "CASTELLON/CASTELLO", "CCOM": "10"},
    "13": {"PRO": "CIUDAD REAL", "CCOM": "08"},
    "14": {"PRO": "CORDOBA", "CCOM": "01"},
    "15": {"PRO": "CORUNA, A", "CCOM": "12"},
    "16": {"PRO": "CUENCA", "CCOM": "08"},
    "17": {"PRO": "GIRONA", "CCOM": "09"},
    "18": {"PRO": "GRANADA", "CCOM": "01"},
    "19": {"PRO": "GUADALAJARA", "CCOM": "08"},
    "20": {"PRO": "GIPUZKOA", "CCOM": "16"},
    "21": {"PRO": "HUELVA", "CCOM": "01"},
    "22": {"PRO": "HUESCA", "CCOM": "02"},
    "23": {"PRO": "JAEN", "CCOM": "01"},
    "24": {"PRO": "LEON", "CCOM": "07"},
    "25": {"PRO": "LLEIDA", "CCOM": "09"},
    "26": {"PRO": "RIOJA, LA", "CCOM": "17"},
    "27": {"PRO": "LUGO", "CCOM": "12"},
    "28": {"PRO": "MADRID", "CCOM": "13"},
    "29": {"PRO": "MALAGA", "CCOM": "01"},
    "30": {"PRO": "MURCIA", "CCOM": "14"},
    "31": {"PRO": "NAVARRA", "CCOM": "15"},
    "32": {"PRO": "OURENSE", "CCOM": "12"},
    "33": {"PRO": "ASTURIAS", "CCOM": "03"},
    "34": {"PRO": "PALENCIA", "CCOM": "07"},
    "35": {"PRO": "PALMAS, LAS", "CCOM": "05"},
    "36": {"PRO": "PONTEVEDRA", "CCOM": "12"},
    "37": {"PRO": "SALAMANCA", "CCOM": "07"},
    "38": {"PRO": "SANTA CRUZ DE TENERIFE", "CCOM": "05"},
    "39": {"PRO": "CANTABRIA", "CCOM": "06"},
    "40": {"PRO": "SEGOVIA", "CCOM": "07"},
    "41": {"PRO": "SEVILLA", "CCOM": "01"},
    "42": {"PRO": "SORIA", "CCOM": "07"},
    "43": {"PRO": "TARRAGONA", "CCOM": "09"},
    "44": {"PRO": "TERUEL", "CCOM": "02"},
    "45": {"PRO": "TOLEDO", "CCOM": "08"},
    "46": {"PRO": "VALENCIA/VALENCIA", "CCOM": "10"},
    "47": {"PRO": "VALLADOLID", "CCOM": "07"},
    "48": {"PRO": "BIZKAIA", "CCOM": "16"},
    "49": {"PRO": "ZAMORA", "CCOM": "07"},
    "50": {"PRO": "ZARAGOZA", "CCOM": "02"},
    "51": {"PRO": "CEUTA", "CCOM": "18"},
    "52": {"PRO": "MELILLA", "CCOM": "19"},
}


@app.get(
    "/autonomias/",
    summary="Listado de todas las comunidades autonomas",
    responses={
        200: {"description": "Listado de autonomias"},
    },
)
def get_autonomias():
    """Devuelve el listado de comunidades autonomas con su codigo y nombre."""
    items = [{"CCOM": code, "AUTO": name} for code, name in dict_auto.items()]
    return items


@app.get(
    "/provincias/",
    summary="Listado de todas las provincias",
    responses={
        200: {"description": "Listado de provincias"},
        404: {"description": "No se encontro la comunidad autonoma"},
    },
)
def get_provincias():
    """Devuelve el listado de provincias con su codigo, nombre y comunidad autonoma."""
    items = [
        {
            "CODPRO": code,
            "PRO": info["PRO"],
            "CCOM": info["CCOM"],
            "AUTO": dict_auto[info["CCOM"]],
        }
        for code, info in dict_provincia.items()
    ]
    if len(items) == 0:
        raise HTTPException(
            status_code=404, detail="Sin resultados para esa comunidad autonoma"
        )
    return items


@app.get(
    "/provincias/{ccom}",
    summary="Listado de todas las provincias de una comunidad autonoma",
    responses={
        200: {"description": "Listado de provincias"},
    },
)
def get_provincias_by_ccom(ccom: int):
    """Devuelve el listado de provincias de una comunidad autonom con su codigo, nombre y comunidad autonoma."""
    items = [
        {
            "CODPRO": code,
            "PRO": info["PRO"],
            "CCOM": info["CCOM"],
            "AUTO": dict_auto[info["CCOM"]],
        }
        for code, info in dict_provincia.items()
        if int(info["CCOM"]) == ccom
    ]
    return items


@app.get(
    "/poblaciones/{cpro}",
    summary="Listado de poblaciones de una provincia con su codigo y nombre",
    responses={
        200: {"description": "Listado de poblaciones para la provincia"},
        404: {"description": "No se encontraron poblaciones para la provincia"},
    },
)
def get_poblaciones_by_cpro(cpro: int):
    """Devuelve el listado de poblaciones de una provincia con su codigo y nombre."""
    # TODO Eliminar el nucleo de poblacion directamente de la fuente de datos
    cur = con.execute(
        """
        SELECT cmun, FLOOR(cun / 1000) AS cun, NENTSIC
        FROM TRAM
        WHERE cpro = ?
        GROUP BY cmun, FLOOR(cun / 1000), NENTSIC
        ORDER BY cmun, cun
    """,
        [cpro],
    )

    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    items = [dict(zip(cols, r)) for r in rows]

    if not items:
        raise HTTPException(status_code=404, detail="Sin resultados para esa provincia")

    return items


@app.get(
    "/cp/{cpos}",
    summary="poblaciones por código postal",
    responses={
        200: {"description": "Listado de poblaciones para el CP"},
        204: {"description": "Sin contenido: el CP parcial tiene menos de 3 dígitos"},
        400: {"description": "Petición inválida: el CP no es numérico"},
        404: {"description": "No se encontraron poblaciones para el CP"},
    },
)
def get_poblaciones_by_cp(cpos: str):
    """
    Devuelve el codigo de provincia, municipio y descripcion para un codigo postal (cpos).
    Permite busquedas parciales con un minimo de 3 caracteres
    """
    # El cp se envia intencianadamente como str para mantener los ceros a la izquierda
    if not cpos.isdigit():
        raise HTTPException(status_code=400, detail="cpos debe ser numérico")

    if len(cpos) < 3:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    sql = """
        SELECT cpos, cpro, cmun, FLOOR(cun / 1000), NENTSIC
        FROM TRAM
    """

    cur = None
    if len(cpos) == 5:
        sql += "WHERE cpos = ?  GROUP BY cpos, cpro, cmun, FLOOR(cun / 1000), NENTSIC "
        cur = con.execute(sql, [int(cpos)])
    else:
        # Se completa con valores a la derecha para busquedas parciales, respetando los ceros a la izquierda
        cpos_min = int(cpos.ljust(5, "0"))
        cpos_max = int(cpos.ljust(5, "9"))

        sql += "WHERE cpos BETWEEN ? and ? GROUP BY cpos, cpro, cmun, FLOOR(cun / 1000), NENTSIC"
        cur = con.execute(sql, [cpos_min, cpos_max])

    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    items = [dict(zip(cols, r)) for r in rows]

    if not items:
        raise HTTPException(status_code=404, detail="Sin resultados para ese CP")

    return items


@app.get(
    "/vias/{cpos}/{nviac}",
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
        GROUP BY cpos, TRAM.cpro, TRAM.cmun, TRAM.cvia, NENTSIC, TVIA, NVIA
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
    "/vias/{cpro}/{cmun}/{cun}/{nviac}",
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
    "/cp/{cpro}/{cmun}/{cun}",
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
    """Devuelve el codigo postal, provincia, municipio, unidad poblacional y descripcion de una unidad poblacional."""

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
