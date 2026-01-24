"""
Tests para la API REST del Callejero
Todos los tests utilizan TestClient de FastAPI para simular peticiones HTTP
"""

import pytest
from fastapi.testclient import TestClient
from .main import app

# Crear cliente de pruebas
client = TestClient(app)


# ============================================================
# Tests para /autonomias/
# ============================================================


def test_get_autonomias():
    """Prueba que devuelve todas las comunidades autónomas correctamente"""
    response = client.get("/api/autonomias/")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 19  # España tiene 19 comunidades autónomas

    # Verificar que contiene campos esperados
    assert "CCOM" in data[0]
    assert "AUTO" in data[0]

    # Verificar una comunidad específica
    andalucia = next((item for item in data if item["CCOM"] == "01"), None)
    assert andalucia is not None
    assert andalucia["AUTO"] == "ANDALUCÍA"


# ============================================================
# Tests para /provincias/
# ============================================================


def test_get_provincias():
    """Prueba que devuelve todas las provincias correctamente"""
    response = client.get("/api/provincias/")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 52  # España tiene 52 provincias

    # Verificar que contiene campos esperados
    assert "CODPRO" in data[0]
    assert "PRO" in data[0]
    assert "CCOM" in data[0]
    assert "AUTO" in data[0]


def test_get_provincias_by_ccom_valid():
    """Prueba que devuelve las provincias de Andalucía (CCOM=01) correctamente"""
    response = client.get("/api/provincias/1")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 8  # Andalucía tiene 8 provincias

    # Verificar que todas pertenecen a Andalucía
    for provincia in data:
        assert provincia["CCOM"] == "01"
        assert provincia["AUTO"] == "ANDALUCÍA"


def test_get_provincias_by_ccom_invalid_low():
    """Prueba que devuelve error 422 para código de comunidad menor que 1"""
    response = client.get("/api/provincias/0")
    assert response.status_code == 422


def test_get_provincias_by_ccom_invalid_high():
    """Prueba que devuelve error 422 para código de comunidad mayor que 19"""
    response = client.get("/api/provincias/20")
    assert response.status_code == 422


def test_get_provincias_by_ccom_madrid():
    """Prueba que devuelve correctamente la provincia de Madrid (CCOM=13)"""
    response = client.get("/api/provincias/13")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1  # Madrid tiene solo 1 provincia
    assert data[0]["PRO"] == "MADRID"


# ============================================================
# Tests para /poblaciones/{cpro}
# ============================================================


def test_get_poblaciones_by_cpro_valid():
    """Prueba que devuelve poblaciones para la provincia de Madrid (28)"""
    response = client.get("/api/poblaciones/28")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

    # Verificar estructura de respuesta
    assert "cmun" in data[0]
    assert "cun" in data[0]
    assert "nentsic" in data[0]


def test_get_poblaciones_by_cpro_invalid_low():
    """Prueba que devuelve error 422 para código de provincia menor que 1"""
    response = client.get("/api/poblaciones/0")
    assert response.status_code == 422


def test_get_poblaciones_by_cpro_invalid_high():
    """Prueba que devuelve error 422 para código de provincia mayor que 52"""
    response = client.get("/api/poblaciones/53")
    assert response.status_code == 422


# ============================================================
# Tests para /cp/{cpos}
# ============================================================


def test_get_poblaciones_by_cp_complete():
    """Prueba búsqueda de población por código postal completo (28001 - Madrid Centro)"""
    response = client.get("/api/cp/28001")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

    # Verificar estructura
    assert "cpos" in data[0]
    assert "cpro" in data[0]
    assert "cmun" in data[0]
    assert "nentsic" in data[0]

    # Verificar que el código postal coincide
    assert data[0]["cpos"] == 28001


def test_get_poblaciones_by_cp_partial():
    """Prueba búsqueda parcial por código postal (280 - códigos postales de Madrid)"""
    response = client.get("/api/cp/280")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

    # Verificar que todos los códigos postales empiezan por 280
    for item in data:
        assert str(item["cpos"]).startswith("280")


def test_get_poblaciones_by_cp_too_short():
    """Prueba que devuelve 422 para código postal muy corto (menos de 3 dígitos)"""
    response = client.get("/api/cp/28")
    assert response.status_code == 422


def test_get_poblaciones_by_cp_non_numeric():
    """Prueba que devuelve error 400 para código postal no numérico"""
    response = client.get("/api/cp/abcde")
    assert response.status_code == 400
    assert response.json()["detail"] == "cpos debe ser numérico"


def test_get_poblaciones_by_cp_not_found():
    """Prueba que devuelve 404 para código postal que no existe"""
    response = client.get("/api/cp/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Sin resultados para ese CP"


def test_get_poblaciones_by_cp_with_leading_zeros():
    """Prueba búsqueda con códigos postales que tienen ceros a la izquierda"""
    response = client.get("/api/cp/01001")
    assert response.status_code == 200

    data = response.json()
    # Verificar que se encuentran resultados (Álava)
    if len(data) > 0:
        assert data[0]["cpos"] == 1001


# ============================================================
# Tests para /vias/{cpos}/{nviac}
# ============================================================


def test_get_via_by_cpos_valid():
    """Prueba búsqueda de vía por código postal y nombre parcial"""
    response = client.get("/api/vias/28001/MAYOR")
    # Puede devolver 200 con datos o 404 si no hay vías con ese nombre
    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)

        if len(data) > 0:
            # Verificar estructura de respuesta
            assert "cpos" in data[0]
            assert "cpro" in data[0]
            assert "cmun" in data[0]
            assert "cvia" in data[0]
            assert "nentsic" in data[0]
            assert "tvia" in data[0]
            assert "nvia" in data[0]

            # Verificar que el nombre contiene el texto buscado
            assert "MAYOR" in data[0]["nvia"].upper()

            # Verificar capitalización
            assert data[0]["tvia"].istitle() or data[0]["tvia"].isupper()


def test_get_via_by_cpos_too_short():
    """Prueba que devuelve 422 para nombre de vía muy corto (menos de 3 caracteres)"""
    response = client.get("/api/vias/28001/AB")
    assert response.status_code == 422


def test_get_via_by_cpos_not_found():
    """Prueba que devuelve 404 cuando no se encuentran vías"""
    response = client.get("/api/vias/28001/XYZABC123NOTEXIST")
    assert response.status_code == 404
    assert "Sin resultados" in response.json()["detail"]


def test_get_via_by_cpos_invalid_cp():
    """Prueba que devuelve error 422 para código postal inválido"""
    response = client.get("/api/vias/999/GRAN")
    assert response.status_code == 422


# ============================================================
# Tests para /vias/{cpro}/{cmun}/{cun}/{nviac}
# ============================================================


def test_get_via_by_cun_valid():
    """Prueba búsqueda de vía por unidad poblacional y nombre parcial"""
    # Madrid: cpro=28, cmun=79 (Madrid capital), cun=0
    response = client.get("/api/vias/28/79/0/MAYOR")
    # Puede devolver 200 con datos o 404 si no hay vías con ese nombre
    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)

        if len(data) > 0:
            # Verificar estructura de respuesta
            assert "cpos" in data[0]
            assert "cpro" in data[0]
            assert "cmun" in data[0]
            assert "cvia" in data[0]
            assert "cun" in data[0]
            assert "nentsic" in data[0]
            assert "tvia" in data[0]
            assert "nvia" in data[0]

            # Verificar que el nombre contiene el texto buscado
            assert "MAYOR" in data[0]["nvia"].upper()

            # Verificar que pertenece a la unidad correcta
            assert data[0]["cpro"] == 28
            assert data[0]["cmun"] == 79


def test_get_via_by_cun_too_short():
    """Prueba que devuelve 422 para nombre de vía muy corto"""
    response = client.get("/api/vias/28/79/0/AB")
    assert response.status_code == 422


def test_get_via_by_cun_not_found():
    """Prueba que devuelve 404 cuando no se encuentran vías para la unidad poblacional"""
    response = client.get("/api/vias/28/79/0/XYZABC123NOTEXIST")
    assert response.status_code == 404
    assert "Sin resultados" in response.json()["detail"]


def test_get_via_by_cun_invalid_cpro():
    """Prueba que devuelve error 422 para código de provincia inválido"""
    response = client.get("/api/vias/0/79/0/ALCALA")
    assert response.status_code == 422


def test_get_via_by_cun_invalid_cmun():
    """Prueba que devuelve error 422 para código de municipio inválido"""
    response = client.get("/api/vias/28/0/0/ALCALA")
    assert response.status_code == 422


# ============================================================
# Tests para /{cpro}/{cmun}
# ============================================================


def test_get_localidades_by_cpro_cmun_valid():
    """Prueba que devuelve códigos postales para Madrid capital (28/79)"""
    response = client.get("/api/28/79")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

    # Verificar estructura
    assert "cpos" in data[0]
    assert "cpro" in data[0]
    assert "cmun" in data[0]
    assert "nentsic" in data[0]

    # Verificar que pertenecen al municipio correcto
    for item in data:
        assert item["cpro"] == 28
        assert item["cmun"] == 79


def test_get_localidades_by_cpro_cmun_invalid_cpro():
    """Prueba que devuelve error 422 para código de provincia inválido"""
    response = client.get("/api/0/79")
    assert response.status_code == 422


def test_get_localidades_by_cpro_cmun_invalid_cmun():
    """Prueba que devuelve error 422 para código de municipio inválido"""
    response = client.get("/api/28/0")
    assert response.status_code == 422


def test_get_localidades_by_cpro_cmun_not_found():
    """Prueba que devuelve 404 para provincia/municipio inexistente"""
    response = client.get("/api/28/999")
    assert response.status_code == 404
    assert "Sin resultados" in response.json()["detail"]


# ============================================================
# Tests para /cp/{cpro}/{cmun}/{cun}
# ============================================================


def test_get_by_cun_valid():
    """Prueba que devuelve información para una unidad poblacional específica"""
    # Madrid capital: cpro=28, cmun=79, cun=1000 (primer tramo)
    response = client.get("/api/cp/28/79/1000")
    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Verificar estructura
        assert "cpos" in data[0]
        assert "cpro" in data[0]
        assert "cmun" in data[0]
        # El campo puede ser 'cun' o 'cun_var' dependiendo del query
        assert "cun" in data[0] or "cun_var" in data[0]
        assert "nentsic" in data[0]

        # Verificar que pertenecen a la unidad correcta
        for item in data:
            assert item["cpro"] == 28
            assert item["cmun"] == 79


def test_get_by_cun_invalid_cpro():
    """Prueba que devuelve error 422 para código de provincia inválido"""
    response = client.get("/api/cp/0/79/0")
    assert response.status_code == 422


def test_get_by_cun_invalid_cmun():
    """Prueba que devuelve error 422 para código de municipio inválido"""
    response = client.get("/api/cp/28/0/0")
    assert response.status_code == 422


def test_get_by_cun_negative_cun():
    """Prueba que devuelve error 422 para código de unidad poblacional negativo"""
    response = client.get("/api/cp/28/79/-1")
    assert response.status_code == 422


def test_get_by_cun_not_found():
    """Prueba que devuelve 404 para unidad poblacional inexistente"""
    response = client.get("/api/cp/28/79/99999")
    assert response.status_code == 404
    assert "Sin resultados" in response.json()["detail"]


# ============================================================
# Tests de integración
# ============================================================


def test_integration_full_address_lookup():
    """
    Test de integración: búsqueda completa de una dirección
    1. Buscar comunidad autónoma
    2. Buscar provincias de esa comunidad
    3. Buscar poblaciones de una provincia
    4. Buscar código postal
    5. Buscar vía en ese código postal
    """
    # 1. Obtener comunidad autónoma de Madrid
    response = client.get("/api/autonomias/")
    assert response.status_code == 200
    autonomias = response.json()
    madrid_auto = next((a for a in autonomias if a["AUTO"] == "MADRID"), None)
    assert madrid_auto is not None

    # 2. Obtener provincias de Madrid
    response = client.get(f"/api/provincias/{int(madrid_auto['CCOM'])}")
    assert response.status_code == 200
    provincias = response.json()
    assert len(provincias) == 1

    # 3. Obtener poblaciones de la provincia de Madrid
    response = client.get("/api/poblaciones/28")
    assert response.status_code == 200
    poblaciones = response.json()
    assert len(poblaciones) > 0

    # 4. Buscar código postal de Madrid centro
    response = client.get("/api/cp/28001")
    assert response.status_code == 200
    cps = response.json()
    assert len(cps) > 0

    # 5. Buscar vía en ese código postal
    response = client.get("/api/vias/28001/CALLE")
    # Puede devolver 200 o 404 dependiendo de los datos disponibles
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        vias = response.json()
        # Puede haber o no resultados dependiendo de los datos
        assert isinstance(vias, list)


def test_response_headers_content_type():
    """Prueba que todas las respuestas tienen el Content-Type correcto"""
    endpoints = [
        "/api/autonomias/",
        "/api/provincias/",
        "/api/provincias/1",
        "/api/poblaciones/28",
        "/api/cp/28001",
    ]

    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
