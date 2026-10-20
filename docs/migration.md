# Migración de Flask a Node.js y React Native

Se migra la aplicación de `app.py`: registro, acceso, perfil, lectura del catálogo, planificación semanal y configuración avanzada. Flask y sus plantillas permanecen disponibles para volver al servicio anterior. Los scripts Selenium, sus correos y cron existentes siguen ejecutándose en Python; no forman parte del servidor web migrado. La API escribe las mismas tablas que consumen esos procesos.

## Backend

Requiere Node.js 22.16+ y MariaDB/MySQL. Desde `backend`:

```powershell
npm ci
Copy-Item .env.example .env
# Completar variables de BD y TOKEN_SECRET (mínimo 32 caracteres aleatorios).
npm start
```

El archivo `.env` de la raíz no se carga automáticamente. Copia únicamente los valores necesarios a `backend/.env`. No lo distribuyas con la app. `DB_PASS` conserva el nombre usado por Python. El puerto predeterminado es 5052 para convivir con Flask.

El arranque comprueba columnas e índice único `(user_id, dia)` de `bookings` sin modificar el esquema. No se ejecutan migraciones automáticamente. `/api/health` indica que el proceso responde; no comprueba la disponibilidad continua de MySQL.

### Base existente

1. Crea una copia de seguridad verificable y una base de pruebas separada antes del cambio.
2. Inspecciona `SHOW CREATE TABLE` de `usuarios`, `configs`, `bookings`, `current_classes` y `current_hours`.
3. Confirma que `configs` contiene `tipo_app` y `bookings` tiene índice único `(user_id, dia)` y columna `fecha_evento`.
4. El SQL antiguo en `database/estructura.sql` incluye `tipo` y un `AFTER id` inválido para `configs`, aunque Flask usa `tipo_app`. Si falta **solo** `tipo_app`, aplica una vez `backend/database/001-config-tipo-app.sql`. Si existe `tipo`, inspecciona sus valores y copia los proveedores con la sentencia comentada. No sobrescribas una columna `tipo_app` existente.
5. Si falta el índice semanal, comprueba primero `SELECT user_id, dia, COUNT(*) FROM bookings GROUP BY user_id, dia HAVING COUNT(*) > 1;`. Resuelve duplicados manualmente antes de crear `ALTER TABLE bookings ADD UNIQUE KEY unique_user_day (user_id, dia);`. No borres reservas automáticamente.
6. Usa ambas interfaces sobre una base de pruebas; no ejecutes cron contra datos reales durante las pruebas.

Para una instalación **nueva y vacía**, importa `backend/database/schema.sql`. No lo importes sobre tablas existentes. No se ha aplicado SQL desde esta migración.

No se modifica el formato de los días ni `fecha_evento`: las actualizaciones conservan la fecha existente y sustituyen la hora como Flask. El servidor usa `NOW()` de la conexión MySQL existente; no cambia su zona horaria. Los scripts Python conservan el cálculo de fechas de reservas.

### Compatibilidad y seguridad

- Contraseñas de acceso: hashes Werkzeug `scrypt` y `pbkdf2` compatibles; registros nuevos usan `scrypt:32768:8:1`, también verificable desde Werkzeug. Ningún reinicio de contraseñas requerido.
- Tokens firmados con caducidad, guardados en SecureStore. Salir elimina el token del dispositivo; un token copiado sigue válido hasta caducar. Cambiar `TOKEN_SECRET` invalida todas las sesiones de la API. Las sesiones Flask son independientes.
- Identidad obtenida del token y de `usuarios`; nunca del `user_id` recibido. Consultas parametrizadas y escrituras por usuario autenticado.
- Registro de usuario y configuración, y guardado de siete días, usan transacciones. Reintentar los PUT no crea reservas duplicadas cuando existe el índice obligatorio.
- La API serializa registros con un bloqueo MySQL. La tabla antigua no garantiza un usuario único: desactiva registro Flask al abrir registro Node para evitar carreras entre versiones. El esquema nuevo sí incluye índice único.
- La contraseña del proveedor no se devuelve al móvil. Campo vacío al guardar conserva la existente. Sigue almacenada en el formato legado porque Selenium la necesita para iniciar sesión; restringe acceso a la BD y sus copias. No se introduce cifrado incompatible con los trabajadores Python.
- Login y registro tienen límite de intentos. Publica la API detrás de HTTPS. Si usas un proxy, configura `trust proxy` para sus IP concretas antes de confiar en cabeceras del cliente.
- No hay CORS abierto: este cliente es nativo. No se incluye cliente web ni WebView.

## Mobile

Proyecto Expo SDK 58 con JavaScript, React Native, Safe Area Context y SecureStore. Las dependencias se resuelven con `expo install` para coincidir con el SDK: [documentación Expo](https://docs.expo.dev/versions/latest/).

Desde `mobile`:

```powershell
npm ci
Copy-Item .env.example .env
# EXPO_PUBLIC_API_URL=https://tu-servidor/api
npm start
```

Para un teléfono físico usa la IP LAN del equipo durante desarrollo y permite el puerto 5052 en el firewall. `localhost` en el teléfono es el propio teléfono. Producción requiere HTTPS. No se añade excepción HTTP a la configuración nativa. Un cambio en `EXPO_PUBLIC_API_URL` requiere reiniciar Metro y actualizar el bundle o recompilar la app distribuida.

Abre con un cliente Expo compatible con SDK 58 o una compilación de desarrollo. No se configuran identificadores, firma, builds de tiendas ni despliegue. Ejecutar desde Windows no valida iOS.

Interfaz nativa adaptable a móvil/tablet, claro/oscuro, formularios con teclado, estados de carga/error, siete días, selectores mediante modales nativos y contraseña visible opcional. Al guardar horarios se validan clases/horas contra catálogo del usuario; días inactivos conservan selecciones antiguas. Si falta catálogo, configura proveedor y ejecuta el scraper existente. El móvil no ejecuta Selenium ni muestra reservas como confirmadas por guardar un horario.

## Contrato API

Respuestas: `{ success: true, data?, message? }` o `{ success: false, error: { message } }`.
Todas las rutas salvo salud, registro y login requieren `Authorization: Bearer <token>`.

| Método | Ruta | Datos |
| --- | --- | --- |
| GET | `/api/health` | Estado del proceso |
| POST | `/api/auth/register` | `usuario`, `contrasena` (8-256), `email`, `full_name` |
| POST | `/api/auth/login` | `usuario`, `contrasena`; devuelve `data.token` |
| GET | `/api/dashboard` | `data.user`, `config`, `bookings`, `classes`, `hours` |
| PUT | `/api/config` | `tipo_app`, `gym`, `periodicidad`, `aimharder_user`, `aimharder_pass` opcional |
| PUT | `/api/bookings` | `bookings`: siete objetos `{ dia, hora, clase, activo }`; `activo` booleano |

Proveedores: `aimharder`, `trainingmyapp`, `resamania`. Periodicidades: `hourly`, `daily`, `weekly`. Días: `Lunes`, `Martes`, `Miercoles`, `Jueves`, `Viernes`, `Sabado`, `Domingo`.

## Validación y vuelta atrás

```powershell
cd backend
npm test
npm run check
cd ../mobile
npm run check
npx expo install --check
npm run bundle
```

Las pruebas HTTP usan repositorio simulado; verifican autenticación, identidad del propietario, validación y rollback simulado. No equivalen a integración MariaDB ni E2E.

La instalación inicial detectó 22 avisos de auditoría en dependencias móviles (7 moderados, 15 altos), incluidos `braces`, `node-forge` y `uuid` transitivos. Las propuestas automáticas incluyen retroceder Expo/React Native a versiones incompatibles con SDK 58. No se aplica `audit fix --force`; revisa los avisos y las actualizaciones compatibles antes de publicar. La instalación del backend no reportó vulnerabilidades.

Antes de sustituir Flask, valida contra una BD de pruebas: login de una cuenta antigua, registro nuevo, duplicados, catálogo por usuario, siete días, guardado de ambos formularios, contraseña conservada/cambiada, `fecha_evento`, reconexión, sesión caducada y aislamiento de dos cuentas. Confirma registros y rollback real con MariaDB. En Android/iOS prueba teclado, modo oscuro, pantalla pequeña, tablet, recuperación de sesión y red caída. Valida después que los trabajadores Python leen la configuración guardada.

Para volver atrás: detén la API y vuelve a servir Flask, conservando tablas y datos. No reviertas escrituras de usuarios: son compatibles. La columna aditiva `tipo_app` puede quedarse; eliminarla rompería el contrato que ya usa Flask. No se modifica CI/CD ni cron.
