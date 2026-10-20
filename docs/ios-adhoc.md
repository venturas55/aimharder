# IPA Ad Hoc de AimHarder

El workflow `.github/workflows/ios-reservas.yml` se ejecuta manualmente desde GitHub Actions. Compila `mobile/` con Expo SDK 57 para iPhone y iPad, firma una IPA Ad Hoc y la guarda como artifact `aimharder-adhoc-<número>`. No publica en App Store ni TestFlight.

## Variables y secretos del repositorio

En GitHub, configura Settings → Secrets and variables → Actions.

| Tipo | Nombre | Contenido |
| --- | --- | --- |
| Variable | `APPLE_BUNDLE_ID` | Identificador explícito registrado para esta app; debe coincidir con el perfil |
| Variable | `APPLE_TEAM_ID` | Team ID de Apple de 10 caracteres |
| Variable | `EXPO_PUBLIC_API_URL` | URL HTTPS pública del backend terminada en `/api` |
| Secret | `IOS_P12_BASE64` | Certificado Apple Distribution y clave privada exportados como `.p12`, codificados en base64 |
| Secret | `IOS_P12_PASSWORD` | Contraseña del `.p12` |
| Secret | `IOS_ADHOC_PROFILE_BASE64` | Perfil Ad Hoc `.mobileprovision` codificado en base64 |

No reutilices un perfil de DosHogares: su App ID puede ser distinto. El certificado puede compartirse si pertenece al mismo equipo y está incluido en el perfil. El perfil debe incluir los UDID de los iPhone/iPad donde se instalará la IPA.

`APPLE_BUNDLE_ID` se aplica a `app.json` únicamente dentro del runner, antes de Expo prebuild. El archivo del repositorio conserva el icono y `supportsTablet: true`; no se inventa un identificador. `EXPO_PUBLIC_API_URL` queda embebida en el bundle y no debe contener secretos. No se usa `.env` local ni credenciales MySQL en GitHub.

## Ejecución y diagnóstico

1. Sube workflow, `mobile/scripts/`, código, lockfile e icono del proyecto al repositorio.
2. Abre Actions → **AimHarder iOS - Ad Hoc iPhone y iPad** → Run workflow.
3. Descarga el artifact de la IPA. Instálala únicamente en dispositivos registrados en el perfil.

El workflow mantiene el runner `macos-26` y la selección Xcode del archivo original, con alternativa al Xcode predeterminado si la ruta concreta no existe. Instala dependencias desde `mobile/package-lock.json`. El perfil, equipo, caducidad, certificado y clave se verifican antes del archive. La firma manual se configura solo en el target de la app para evitar asignar un perfil a los Pods.

Si falla, descarga `aimharder-diagnostics-<número>` y revisa primero `aimharder-pods.log`, `aimharder-archive.log` o `aimharder-export.log`, según el paso. La generación de una IPA requiere ejecutar el workflow en macOS; validaciones locales de YAML, Bash y Python no demuestran un archive correcto ni instalación en un dispositivo.

Referencias: [firma en GitHub Actions](https://docs.github.com/en/actions/how-tos/deploy/deploy-to-third-party-platforms/sign-xcode-applications), [configuración Expo](https://docs.expo.dev/workflow/configuration/).
