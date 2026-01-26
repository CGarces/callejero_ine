# Análisis de Archivos de Datos del Proyecto

## Resumen
El proyecto Callejero INE transforma los archivos de datos administrativos en un directorio de calles eficiente y buscable. El sistema ingiere archivos de texto catastrales estándar (PSEU, SECC, TRAM, UP, VIAS), los consolida en una base de datos DuckDB para consultas de alto rendimiento y expone los datos a través de una interfaz web moderna y una API REST.

## Estructura de Archivos

```
caj_esp_072025/
├── TRAM.D250630.G250702    (417 MB)  - Tramos/segmentos de carreteras
└── VIAS.D250630.G250702    (121 MB)  - Carreteras/calles
```


### Archivos de Datos Catastrales Españoles (caj_esp_072025/)

Estos son archivos de datos catastrales (registro de la propiedad) basados en texto del Catastro Español (catastro de la propiedad). Todos los archivos siguen la convención de nomenclatura: `[TIPO].D[FECHA_DESDE].G[FECHA_HASTA]`


#### TRAM.D250630.G250702 - Tramos/Segmentos de Carreteras

- **Tamaño**: 417 MB
- **Contenido**: Datos de segmentos de carreteras con coordenadas y nombres
- **Registros de Ejemplo**:
  ```
  010010101001   000170101001000000   0124010001 0027    20250630 010001   0001701                    ALEGRIA-DULANTZI                    ALEGRIA-DULANTZI                    010001TORRONDOA
  ```
- **Propósito**: Datos detallados de red de carreteras con información de segmentos

#### VIAS.D250630.G250702 - Carreteras/Calles

- **Tamaño**: 121 MB
- **Contenido**: Datos de nombres de calles y carreteras
- **Registros de Ejemplo**:
  ```
  010010101TORRONDOA          20250630 01001KALE TORRONDOA                    TORRONDOA
  010010102AÑUA BIDEA         20250630 01002KALE AÑUA BIDEA                   AÑUA BIDEA
  ```
- **Propósito**: Nombres oficiales de calles y designaciones

## Estructura Detallada de los Archivos del Callejero INE

Los archivos del Callejero del Instituto Nacional de Estadística (INE) utilizan una estructura jerárquica y relacional basada en códigos administrativos.

### Jerarquía de Códigos Administrativos

Los códigos siguen una estructura posicional de 12 dígitos:

- **Posiciones 1-2**: Código de Provincia (CPRO)
- **Posiciones 3-5**: Código de Municipio dentro de la provincia (CMUN)
- **Posiciones 6-7**: Código de Entidad Colectiva (CC)
- **Posiciones 8-9**: Código de Entidad Singular (SS)
- **Posición 10**: Dígito de control
- **Posiciones 11-12**: Código de Núcleo (Si =99, es *DISEMINADO*)

### Descripción Detallada por Archivo

De los ficheros unicamente se extraen los dos campos esenciales para el proyecto.

## DISEÑO DEL FICHERO DE VIAS

| Campo      | Descripción         | Formato   |   Longitud |
|------------|---------------------|-----------|------------|
| CPRO       | Código de Provincia | N         |          2 |
| CMUN       | Código de Municipio | N         |          3 |
| CVIA       | Código de Vía       | N         |          5 |
| TVIA       | Tipo de Vía         | A         |          5 |


## DISEÑO DEL FICHERO DE PSEUDOVÍAS.

| Campo     | Descripción                  | Formato   |   Longitud |
|-----------|------------------------------|-----------|------------|
| CPRO      | Código de Provincia          | N         |          2 |
| CMUN      | Código de Municipio          | N         |          3 |
| CUN       | Código de Unidad Poblacional | N         |          7 |
| CVIA      | Código de Vía                | N         |          5 |
| CPOS      | Código Postal                |	N         |          5 |
| NENTSIC   | Nombre Corto de E.Singular   | A         |         25 |
| NVIAC     | Nombre Corto                 | A         |         25 |

# Componentes de la Arquitectura

El proyecto esta diseñado para ser desplegado en AWS utilizando una arquitectura serverless para maximizar la escalabilidad y minimizar los costos operativos. 

Los principales componentes de la arquitectura son:

1. **AWS Lambda**: Aloja la API backend (FastAPI + DuckDB), que escala automáticamente según la demanda.
2. **Amazon S3**: Almacena los archivos de datos en bruto, las bases de datos procesadas y aloja los activos estáticos del frontend.
3. **Amazon CloudFront**: Red de entrega de contenido (CDN) para servir el frontend globalmente con baja latencia.
4. **Amazon ECR (Elastic Container Registry)**: Almacena las imágenes de Docker para las funciones Lambda.
5. **Terraform**: Herramienta de Infraestructura como Código (IaC) utilizada para definir y aprovisionar la infraestructura en la nube de AWS.

## Despliege del Proyecto Callejero INE
El proyecto Callejero INE se despliega utilizando Terraform para gestionar la infraestructura en AWS. Ver el archivo [terraform/README.md](terraform/README.md) para instrucciones detalladas sobre cómo desplegar la infraestructura y la aplicación.

## Despliege en local

Para ejecutar el proyecto en local, es necesario tener instalado previamente python 3.9 o superior sigue estos pasos:

1. Clona el repositorio:
   ```bash
   git clone
   ```
2. Navega al directorio del proyecto:
   ```bash
   cd callejero-ine
   ```
3. Configura un entorno virtual e instala las dependencias:

   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows usa `venv\Scripts\activate`
   pip install -r scripts/requirements.txt
   pip install -r api_rest/requirements.txt
   ```

4. Ejecuta los scripts de procesamiento de datos para generar la base de datos DuckDB:

   ```bash
   python scripts/donwload_callejero.py
   python scripts/parse_callejero.py
   ```

5. Inicia el servidor FastAPI:

   ```bash
   uvicorn api_rest.app.main:app --reload
   ```

6. Abre el navegador y navega a `http://localhost:8000` para acceder a la interfaz web o `http://localhost:8000/docs` para la documentación de la API.

Si se quiere usar la demo en Angular es necesario tener instalado pnpn y nodejs sigue estos pasos:

1. En otro terminal, navega al directorio del frontend:

   ```bash
   cd frontend/callejero-ine
   ```

2. Instala las dependencias:

   ```bash
   pnpm install
   ```

3. Inicia el servidor de desarrollo:

   ```bash
   pnpm start
   ```

4. Abre el navegador y navega a `http://localhost:4200` para acceder a la aplicación frontend.