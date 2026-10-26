# Despliegue de PapaExpert en Render

El backend usa Firebase para los datos de la app. Render aloja la API y el
modelo YOLO; no necesita una base PostgreSQL.

## Crear el servicio

1. Sube el contenido de este repositorio a GitHub, incluyendo `render.yaml`,
   `Dockerfile` y `models/best.pt`.
2. En Render, crea un **Blueprint** y selecciona el repositorio. El Blueprint
   configura el servicio `papaexpert-api`, su comprobación en
   `/api/v1/health` y el despliegue automático al actualizar `main`.
3. En **Environment → Secret Files**, crea `firebase-service-account.json` y
   pega el contenido de la clave JSON de una cuenta de servicio de Firebase
   Admin del proyecto `papaexpert-9883d`. El servicio ya apunta a
   `/etc/secrets/firebase-service-account.json`.
4. Confirma que Firebase Authentication, Cloud Firestore y Firebase Cloud
   Messaging estén habilitados para ese proyecto. En Firestore, la app guarda
   datos en `users/{uid}/...`; el worker revisa
   `users/{uid}/treatments` y envía avisos a los tokens de
   `users/{uid}/notification_devices`.
5. Espera a que el health check marque el servicio como disponible. La primera
   inferencia puede tardar más mientras se carga YOLO en CPU.

No agregues `DATABASE_URL` para el flujo Firebase de la app. Las rutas antiguas
que dependen de SQL responden `503` mientras no haya una base SQL configurada.
El chat con OpenAI requiere agregar `OPENAI_API_KEY` en las variables del
servicio; YOLO y las notificaciones no la requieren.

## Conectar la app móvil

La app apunta por defecto a `https://papaexpert-api.onrender.com/api/v1` y
permite cambiarlo al compilar:

```powershell
flutter build apk --release --dart-define=PAPAEXPERT_API_BASE_URL=https://<url-del-servicio>.onrender.com/api/v1
```

Usa la URL exacta que Render muestra para el servicio. La app debe compilarse y
distribuirse de nuevo para que los dispositivos usen la URL de Render.
