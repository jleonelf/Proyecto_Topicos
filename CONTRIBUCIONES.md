# Contribuciones del equipo

Este documento resume los aportes registrados en el historial de `main` hasta el commit `289c123`. Los nombres de usuario corresponden a los autores de los commits. Se citan commits representativos para que cada aporte pueda verificarse con `git show <hash>`.

## Carmen (`Carmen21-A`)

- Implementó las fases 1 y 2 del pipeline de NLP: normalización y tokenización, con pruebas para ambas (`0d9cc7e`).
- Desarrolló la primera interfaz de la tienda y la migró de Vue a React 18 con Vite, manteniendo los componentes de catálogo, chat, panel de métricas y visualización del procesamiento (`0d9cc7e`, `3cc23d4`, `d523bc0`).
- Documentó ejemplos antes y después de la normalización y tokenización en `backend/notebooks/02a_normalizacion_tokenizacion.ipynb` (`e2208a1`).

## Fernando Javier Calani García (`FernandojCg737`)

- Implementó las fases 3 y 4: stop words ajustadas al dominio, lematización con spaCy, stemming con Snowball y el `TextPreprocessor` que integra las fases 1 a 4. Añadió pruebas y la comparación de alternativas en el notebook 02b (`7b377f2`, `074a934`, `aea348b`, `f2ed38d`).
- Construyó y documentó conjuntos de datos de referencia, el dataset de intenciones y la carga/división estratificada; añadió el notebook de análisis exploratorio (`335f053`, `556366f`, `7c957fc`).
- Integró respuestas del chat con datos de la tienda, importación y análisis de inventario, métricas del modelo y mejoras en el frontend (`5a4ad65`, `5f78829`, `f4ddd37`, `4ae22cd`).
- Reorganizó el proyecto en `backend/`, `frontend/` y `database/` y agregó Docker Compose con PostgreSQL y su documentación (`26a0167`, `276e9a0`).

## Ramiro (`gonzales_ramiro`)

- Implementó la fase 5 de vectorización TF-IDF y su notebook de experimentación (`6a54783`).
- Desarrolló la base de la API FastAPI, los endpoints de predicción, chat y reportes, los esquemas y servicios asociados, y la extracción de entidades (`6a54783`).
- Añadió pruebas para la API, entidades y vectorización, además de guías de backend y vectorización (`6a54783`, `772d796`).

## Jorge (`jleonelf`)

- Creó la estructura inicial del repositorio (`f6fb96c`, `9fce904`).
- Preparó dependencias y configuración para el entrenamiento reproducible (`8674891`).
- Implementó la fase 6: entrenamiento y comparación del clasificador con línea base, Naive Bayes y regresión logística; inferencia y evaluación de consultas fuera de dominio, con datasets, métricas y artefactos (`995042c`).
- Documentó la evaluación y amplió el notebook de modelos y las pruebas de inferencia y rechazo fuera de dominio (`b6ef09c`).

## Alcance de la atribución

Los commits de integración pueden mover archivos entre carpetas; los hashes anteriores identifican el aporte original. Esta relación describe trabajo registrado en el historial y no atribuye tareas pendientes del plan ni cambios locales sin commit.
