# ShopStarter - Guía de Instalación

Este proyecto está desarrollado con **Python**, **Django** y
**PostgreSQL**.

------------------------------------------------------------------------

## Requisitos

Antes de iniciar tener instalado:

-   **Python 3.11 o superior**
-   **pip**
-   **PostgreSQL**
-   **Git** (opcional)

Puedes verificar tu versión de Python con:

``` bash
python3 --version
```

Debe mostrar una versión **3.11+**.

------------------------------------------------------------------------

## 1. Clonar el repositorio

``` bash
git clone <URL_DEL_REPOSITORIO>
cd <NOMBRE_DEL_PROYECTO>
```

------------------------------------------------------------------------

## 2. Crear el entorno virtual

### macOS / Linux

``` bash
python3 -m venv envs/shopv
source ./envs/shopv/bin/activate
```

### Windows

``` bash
python -m venv envs/shopv
envs\shopv\Scripts\activate
```

------------------------------------------------------------------------

## 3. (Opcional) Actualizar pip

``` bash
pip3 install --upgrade pip
```

------------------------------------------------------------------------

## 4. Instalar dependencias

``` bash
pip3 install -r requirements.txt
```

------------------------------------------------------------------------

## 5. Configurar variables de entorno

Crear un archivo en la raíz del proyecto llamado:

    .env

Ejemplo de configuración (`.env.example`):

``` env
DEBUG=True

DB_NAME=shopstarter_db
DB_USER=postgres
DB_PASSWORD=root
DB_HOST=localhost
DB_PORT=5432

SECRET_KEY=your-secret-key
```

⚠️ Asegúrate de que la base de datos **shopstarter_db** exista en
PostgreSQL antes de ejecutar las migraciones.

------------------------------------------------------------------------

## 6. Ejecutar migraciones

``` bash
python3 manage.py migrate
```

------------------------------------------------------------------------

## 7. Ejecutar el servidor de desarrollo

``` bash
python3 manage.py runserver
```

El servidor estará disponible en:

    http://127.0.0.1:8000/

------------------------------------------------------------------------

## Notas

-   Asegúrate de tener **PostgreSQL en ejecución**.
-   El entorno virtual debe estar **activado** antes de ejecutar
    comandos de Django.
-   Si cambias variables del archivo `.env`, reinicia el servidor.
