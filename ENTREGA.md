# Checklist de entrega (deadline 17 nov)

Todo lo que hay que hacer para entregar, en orden. Marquen con [x] conforme avancen.

## 1. Nombre y archivos (analista)

- [ ] confirmar el nombre EXACTO del equipo como lo pusimos todos en el registro
- [ ] el csv se llama `<nombre_equipo>.csv` y el documento `<nombre_equipo>.pdf` (el scorer usa el nombre del archivo para la tabla)
- [ ] todos tenemos cuenta de Google para el form (solo una respuesta por equipo, se puede editar, cuenta la ultima)

## 2. Documento tecnico (analista + Memo)

El borrador esta en `docs/technical_document.md`, ya en ingles y con todas las secciones que piden.
- [ ] poner nombre del equipo, integrantes y URL del repo arriba
- [ ] el analista llena la parte de la seccion 8 que dice `<analyst: ...>` (porteros, balones aereos, saques de banda)
- [ ] si cambiamos de version (v2), actualizar secciones 3, 4 y 5
- [ ] exportar a PDF (o mandarlo como .md, tambien lo aceptan)

## 3. Repo publico (Memo)

```bash
cd ~/Developer/mtah2027-posesion
git status                      # NO debe aparecer nada de data/, outputs/, models/, data_externa/
gh repo create <nombre-repo> --public --source=. --push
```
(o crear el repo vacio en github.com y `git remote add origin ...` + `git push -u origin main`)

- [ ] revisar en la pagina de github que NO esten: videos, `*_atd.txt`, homografias, smart tagging, `ball_video.csv`, ninguna entrega csv
- [ ] SI pueden estar: `evaluation/gt/` (es el GT publico de 5 min, viene en el repo oficial con licencia MIT)
- [ ] poner la URL en el documento tecnico

## 4. Probar que se reproduce (alguien que NO sea Memo, en su compu)

```bash
git clone <url del repo> && cd <repo>
# copiar la data del drive a data/tactical/ con los nombres originales
bash reproducir.sh prueba
```
- [ ] tiene que terminar con "Valid" y el md5 `bf458c4d098e0c0cc823bae755b03b5d` (si es la v1)
- [ ] si el md5 sale distinto avisar ANTES de entregar

## 5. Generar el archivo final y validarlo

```bash
bash reproducir.sh <nombre_equipo>
python evaluation/validate_submission.py outputs/<nombre_equipo>.csv
```
- [ ] validar EXACTAMENTE el archivo que se va a subir, no uno viejo

## 6. Correo a los organizadores (analista, cuanto antes)

Borrador en ingles abajo. Mandarlo hoy, las respuestas tardan.

## 7. Form

- [ ] Team Name
- [ ] Possession file: `<nombre_equipo>.csv`
- [ ] Public code repository URL
- [ ] Short technical document: `<nombre_equipo>.pdf`

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
> <name>, team <team name>
