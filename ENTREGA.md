# Estado de la entrega (deadline 17 nov)

## Lo que ya tenemos

**Archivo de posesion.** `src/generar_v3.py` genera `outputs/v3_segmentos.csv` (la v3 es la recomendada, ver bitacora 10). Pasa el validador oficial (199,319 filas, frames 0..199318, solo H/A/D/X). Sale identico byte por byte en cada corrida, md5 `6cb2046fe5924ae3878a475281a68c23`. Las versiones anteriores (v0, v1, v2) siguen en el repo como respaldo.

**Repo reproducible.** `bash reproducir.sh <nombre_equipo>` hace todo desde cero en ~5 min (genera la v3): entorno con versiones fijas (`requirements-nuestro.txt`), baja los partidos de Metrica en un commit fijo, entrena, genera el csv y lo valida. Probado en una copia limpia, mismo md5.

**Repo limpio para publicar.** El `.gitignore` deja fuera `data/`, `outputs/`, `models/`, `data_externa/` y los entornos de python. La data del reto, los videos, el csv del detector de balon y las entregas no se suben.

**Documento tecnico en ingles.** `docs/technical_document.md`, con todas las secciones que piden en SUBMISSION.md: enfoque y por que, assets usados y descartados, datos de entrenamiento, manejo del tracking con huecos, reglas de posesion, limitaciones, reproduccion, uso de IA.

**Documentacion interna.** `README.md`, `docs/COMO_FUNCIONA.md` y la bitacora por fases en `docs/bitacora/`.

## Lo que falta

**En el documento tecnico:**
- nombre del equipo e integrantes al inicio
- URL del repo publico
- la parte de la seccion 8 marcada `<analyst: ...>`: como tratamos atajadas del portero, balones aereos y saques de banda
- el documento ya describe la v3; si al final se entrega otra version, actualizar secciones 3, 4 y 5
- exportarlo a PDF (o subirlo como .md, tambien lo aceptan)

**Del repo:**
- publicarlo en GitHub
- revisar en la pagina que no se haya subido nada de data (videos, `*_atd.txt`, homografias, smart tagging, csv de balon o de entregas). `evaluation/gt/` si puede estar, es el GT publico del repo oficial con licencia MIT
- que alguien lo clone en otra compu, ponga la data en `data/tactical/`, corra `bash reproducir.sh prueba` y confirme el md5 `6cb2046fe5924ae3878a475281a68c23`

**Antes del form:**
- confirmar el nombre exacto del equipo como esta en el registro
- generar el archivo final con ese nombre: `bash reproducir.sh <nombre_equipo>`
- validar ese mismo archivo justo antes de subirlo
- tener cuenta de Google para el form (una respuesta por equipo, se puede editar, cuenta la ultima)

**Correo a los organizadores** con tres dudas (borrador abajo). Conviene mandarlo pronto porque las respuestas tardan.

## Lo que se sube al form

| campo | que va |
|---|---|
| Team Name | el del registro |
| Possession file | `<nombre_equipo>.csv` |
| Public code repository URL | la del repo en GitHub |
| Short technical document | `<nombre_equipo>.pdf` (o .md) |

## Lo que nos gustaria tener si da el tiempo

- respuesta de los organizadores sobre archivos intermedios, por si la version final usa el balon detectado en el video
- la seccion de reglas de posesion revisada contra el video por alguien que sepa de futbol

---

## Borrador del correo

> Subject: Initial Challenge, three clarification questions
>
> Hi,
>
> Thanks for the rules clarification. We have three short questions so we stay within the rules:
>
> 1. Intermediate files. Part of our exploration runs a pre-trained ball detector (trained on other matches) on the tactical video. GPU inference is not always bit-identical across machines. If we use it in our final pipeline, can we submit the detector output as an intermediate file (through the form or by email) and have the repository regenerate the submission from it? We would not publish it in the repository, since it is frame-level data derived from the video.
>
> 2. Public ground truth. Is it acceptable to run `run_evaluation.py` once on the public 5 minutes at the end, only to report the number in our technical document, without changing anything afterwards?
>
> 3. Self-training. Would pseudo-labels generated automatically from the provided tracking (no ground truth, no video, no human labels) count as "training on the provided game"? We are not using this now and want to know before considering it.
>
> Thank you,
> <team name>
