# Fase 6: modelos e inferencia (Jorge)

Esta rama contiene el entrenamiento, la comparación de modelos, la inferencia y la evaluación de rechazo fuera de dominio (OOD). Incluye el notebook `notebooks/03_modelos.ipynb`, las pruebas de modelos, `requirements.txt` y los conjuntos `data/ood_val.csv` y `data/ood_test.csv`, creados para calibrar y evaluar el detector de Jorge.

## Dependencias de integración

El entrenamiento importa `src.data.dataset` (Carmen), `src.nlp.pipeline` (Fernando) y `src.nlp.vectorizacion` (Ramiro). **Sus implementaciones no están en esta rama.** El PR de Jorge se debe integrar después de los PR de esas fases. El dataset general `data/raw/intenciones.csv` también debe llegar desde el PR de datos.

`src/config.yaml` es un archivo de contrato compartido. En esta rama contiene los parámetros que necesita el entrenamiento; los responsables de NLP y vectorización deben revisar sus secciones al integrar.

## Instalación y ejecución tras integrar las dependencias

```bash
python -m venv .venv
pip install -r requirements.txt
python -m spacy download es_core_news_sm
python -m src.models.train
python -m pytest
python -m src.models.predict "¿tienen jeans en talla 32?"
```

El comando de entrenamiento genera `artifacts/modelo.joblib`, `artifacts/ood_detector.joblib` y `artifacts/metricas.json`. Los archivos `.joblib` están ignorados por Git. El JSON versionado conserva un resultado de referencia obtenido en la rama de integración con 1.040 frases; debe regenerarse cuando se integren los datasets y módulos definitivos.

El modelo se elige por F1 macro en validación cruzada estratificada sobre entrenamiento. El detector OOD se elige en una partición interna y `data/ood_val.csv`, maximizando F1 macro con rechazo sujeto a una tasa de aceptación OOD de hasta 20 %. Los conjuntos de prueba se usan después para informar el resultado final.

En la última prueba de integración, el clasificador obtuvo F1 macro de 0,8622. El detector aceptó por error 8 de 50 consultas OOD de prueba (16 %), incluidas 8 de 25 difíciles. Estas cifras describen ese conjunto de prueba y no garantizan rechazo de toda consulta ajena a la tienda.

El notebook `notebooks/03_modelos.ipynb` documenta la comparación de modelos, F1 por clase, matriz de confusión y análisis de errores. Se ejecuta después de integrar las dependencias con:

```bash
python -m jupyter nbconvert --to notebook --execute --inplace notebooks/03_modelos.ipynb
```
