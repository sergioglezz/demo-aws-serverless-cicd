# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-11-22
### Security
- Las peticiones se validan: JSON mal formado, campos ausentes o de tipo
  incorrecto, textos de más de 1000 caracteres e ids que no son UUID devuelven
  `400` en lugar de un error interno.
- Los ids de las tareas se generan con `uuid4` (aleatorio). `uuid1` incluía la
  dirección MAC del servidor y la hora, y permitía adivinar ids.
- Los errores inesperados ya no exponen detalles internos al cliente.
- Ya no se escriben en los logs los datos de las tareas ni el endpoint de
  DynamoDB.
- Eliminada la dependencia `urllib3==1.26.6`, con vulnerabilidades conocidas
  (CVE-2023-43804, CVE-2023-45803, CVE-2024-37891), y `requests`, que las
  Lambdas no usaban.
- Plantilla SAM: permisos mínimos por función (`DynamoDBReadPolicy` /
  `DynamoDBCrudPolicy`) cuando no se usa el rol de AWS Academy, y límite de
  peticiones en API Gateway.
- Jenkins: ya no se imprime `samconfig.toml` en los logs.
- Jenkins (rama `develop`): el token de GitHub del stage *Promote* se
  escribía dentro de la URL del remoto, que puede acabar en los logs y en
  `.git/config`; ahora se usa el binding `gitUsernamePassword`. Además, ese
  stage subía los cambios a otro repositorio (`CasoPractico1-3`).

### Changed
- **Cambio incompatible:** `POST /todos` devuelve `201` con la tarea creada
  directamente (antes devolvía un JSON con otro JSON dentro de `body`).
- **Cambio incompatible:** `DELETE /todos/{id}` devuelve `204`.
- `PUT` y `DELETE` sobre una tarea que no existe devuelven `404`. Antes, `PUT`
  creaba una tarea nueva con ese id.
- Todas las respuestas incluyen `Content-Type: application/json`.
- Las fechas `createdAt` y `updatedAt` usan formato ISO 8601 en UTC.

### Fixed
- `GET /todos` devolvía como máximo 1 MB de tareas: ahora recorre todas las
  páginas del scan de DynamoDB.
- Los errores de DynamoDB se ocultaban y la API respondía `200` con `null`.
- `get_table` modificaba `boto3` de forma global en cada invocación.
- El pipeline de producción (`Jenkinsfile`) desplegaba la rama `develop` en
  lugar de `master`.
- Descripciones de los outputs de la plantilla con sintaxis de Serverless
  Framework (`${opt:stage}`) que CloudFormation no interpreta.

### Added
- Tests unitarios con `pytest` y `moto` para la capa de datos y los handlers.
- Integración continua con GitHub Actions: flake8, bandit, pip-audit,
  cfn-lint y tests con cobertura mínima del 90 %.

### Removed
- Carpeta `pipelines/` de la plantilla original del curso (Python 3.7), que no
  usan los pipelines actuales.
- Tests unitarios antiguos basados en `mock_dynamodb2`, que ya no existe en moto.

## [1.0.9] - 2021-01-08
### Added
- Versión inicial de código.
