// Apartado "Inventarios y métricas" (Fernando).
// Reemplaza las tres columnas del asistente por tres pestañas:
//   1. Métricas del modelo: resultados del entrenamiento oficial y del último experimento
//   2. Inventario: analíticas de productos y ventas guardados en la base de datos
//   3. Importar datos: carga masiva de CSV o Excel

import React, { useEffect, useState } from 'react'
import { apiInventario } from '../api/inventario.js'
import '../assets/inventario.css'

// ---------------------------------------------------------------------------
// Formatos
// ---------------------------------------------------------------------------
const pct = (v) => (v == null ? '—' : `${(v * 100).toFixed(1)} %`)
const f3 = (v) => (v == null ? '—' : Number(v).toFixed(3))
const entero = (v) => (v == null ? '—' : Number(v).toLocaleString('es-BO'))
const bs = (v) => (v == null ? '—' : `Bs ${Number(v).toLocaleString('es-BO', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`)
const etiqueta = (intencion) => String(intencion).replaceAll('_', ' ') // "consultar_stock" -> "consultar stock"

// Plantillas que el usuario puede descargar para ver el formato esperado
const PLANTILLAS = {
  'productos.csv': 'sku,nombre,categoria,talla,color,precio,stock\nJ-32-N,Jean Slim,pantalones,32,negro,250,8\nP-M-B,Polera Básica,poleras,M,blanco,80,3\n',
  'ventas.csv': 'fecha,sku,cantidad,precio_unitario\n2026-10-01,J-32-N,2,250\n2026-10-02,P-M-B,1,80\n',
  'frases.csv': 'texto,intencion\nhola buenas tardes,saludo\n¿cuánto cuesta el jean?,consultar_precio\n',
}

function descargarPlantilla(nombre) {
  // ﻿: marca BOM para que Excel abra el CSV con tildes correctas
  const blob = new Blob(['﻿' + PLANTILLAS[nombre]], { type: 'text/csv;charset=utf-8' })
  const enlace = document.createElement('a')
  enlace.href = URL.createObjectURL(blob)
  enlace.download = nombre
  enlace.click()
  URL.revokeObjectURL(enlace.href)
}

// ---------------------------------------------------------------------------
// Piezas reutilizables
// ---------------------------------------------------------------------------
function Tarjeta({ titulo, subtitulo, children, extra }) {
  return (
    <section className="im-card">
      <header className="im-card-head">
        <div>
          <h3 className="im-card-title">{titulo}</h3>
          {subtitulo && <p className="im-card-sub">{subtitulo}</p>}
        </div>
        {extra}
      </header>
      {children}
    </section>
  )
}

function Cifra({ valor, texto, detalle }) {
  return (
    <div className="im-stat">
      <span className="im-stat-value">{valor}</span>
      <span className="im-stat-label">{texto}</span>
      {detalle && <span className="im-stat-detail">{detalle}</span>}
    </div>
  )
}

function Aviso({ tipo = 'info', children }) {
  return <div className={`im-alert im-alert-${tipo}`}>{children}</div>
}

// Barras horizontales de una sola serie: la etiqueta y el valor van en texto,
// la barra solo muestra la magnitud. El "title" da el detalle al pasar el mouse.
function Barras({ filas, formato = entero, maximo }) {
  const tope = maximo ?? (Math.max(...filas.map((f) => f.valor), 0) || 1) // evita dividir por 0
  return (
    <div className="im-bars" role="list">
      {filas.map((f) => (
        <div key={f.etiqueta} className="im-bar-row" role="listitem" title={`${f.etiqueta}: ${formato(f.valor)}${f.detalle ? ` · ${f.detalle}` : ''}`}>
          <span className="im-bar-label">{f.etiqueta}</span>
          <span className="im-bar-track">
            <span className="im-bar-fill" style={{ width: `${(f.valor / tope) * 100}%` }} />
          </span>
          <span className="im-bar-value">{formato(f.valor)}</span>
        </div>
      ))}
    </div>
  )
}

// Matriz de confusión: filas = intención real, columnas = intención predicha.
// La intensidad del color es la proporción de la fila (escala de un solo tono).
function MatrizConfusion({ matriz, clases }) {
  if (!matriz?.length) return <p className="im-muted">Sin datos.</p>
  return (
    <div className="im-table-wrap">
      <table className="im-matrix">
        <thead>
          <tr>
            <th className="im-matrix-corner">Real ↓ · Predicho →</th>
            {clases.map((c, j) => <th key={c} title={etiqueta(c)}>{j + 1}</th>)}
          </tr>
        </thead>
        <tbody>
          {matriz.map((fila, i) => {
            const total = fila.reduce((a, b) => a + b, 0) || 1
            return (
              <tr key={clases[i]}>
                <th className="im-matrix-row">{i + 1}. {etiqueta(clases[i])}</th>
                {fila.map((valor, j) => (
                  <td
                    key={j}
                    // im-hit: acierto (diagonal); im-miss: confusión; im-dark: texto blanco sobre celda oscura
                    className={`${i === j ? 'im-hit' : valor > 0 ? 'im-miss' : ''} ${i === j && valor / total > 0.55 ? 'im-dark' : ''}`}
                    style={{ '--alpha': (valor / total).toFixed(2) }}
                    title={`Real: ${etiqueta(clases[i])} · Predicho: ${etiqueta(clases[j])} · ${valor} (${pct(valor / total)})`}
                  >
                    {valor || ''}
                  </td>
                ))}
              </tr>
            )
          })}
        </tbody>
      </table>
      <p className="im-muted im-small">La diagonal son los aciertos. Pasa el mouse sobre una celda para ver el detalle.</p>
    </div>
  )
}

// Precisión, recall, F1 y soporte de cada intención
function TablaPorClase({ porClase, clases }) {
  return (
    <div className="im-table-wrap">
      <table className="im-table">
        <thead>
          <tr><th>Intención</th><th className="num">Precisión</th><th className="num">Recall</th><th className="num">F1</th><th className="num">Soporte</th></tr>
        </thead>
        <tbody>
          {clases.filter((c) => porClase[c]).map((c) => {
            const m = porClase[c]
            return (
              <tr key={c} className={m.f1 < 0.7 ? 'im-row-weak' : ''}>
                <td>{etiqueta(c)}</td>
                <td className="num">{f3(m.precision)}</td>
                <td className="num">{f3(m.recall)}</td>
                <td className="num"><strong>{f3(m.f1)}</strong></td>
                <td className="num">{m.soporte}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
      <p className="im-muted im-small">Filas resaltadas: F1 menor que 0,70 (intenciones que el modelo confunde más).</p>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Pestaña 1: métricas del modelo
// ---------------------------------------------------------------------------
function PestanaMetricas({ recarga }) {
  const [datos, setDatos] = useState(null)
  const [experimento, setExperimento] = useState(null)
  const [error, setError] = useState('')
  const [seleccion, setSeleccion] = useState(null) // modelo elegido para ver su matriz

  useEffect(() => {
    setError('')
    Promise.all([apiInventario.metricasEntrenamiento(), apiInventario.ultimoExperimento()])
      .then(([m, e]) => { setDatos(m); setExperimento(e) })
      .catch((err) => setError(err.message))
  }, [recarga])

  if (error) return <Aviso tipo="error">{error}</Aviso>
  if (!datos) return <p className="im-muted">Cargando métricas…</p>
  if (!datos.disponible) return <Aviso>{datos.motivo}</Aviso>

  const produccion = datos.modelos.find((m) => m.en_produccion) || datos.modelos[0]
  const mostrado = datos.modelos.find((m) => m.clave === seleccion) || produccion
  const ood = datos.ood?.evaluacion_test || {}

  return (
    <div className="im-stack">
      <Tarjeta
        titulo={`En producción: ${datos.produccion.nombre}`}
        subtitulo={`${datos.produccion.criterio}. Entrenado el ${new Date(datos.fecha).toLocaleString('es-BO')}.`}
      >
        <div className="im-stats">
          <Cifra valor={f3(datos.produccion.cv_f1_macro)} texto="F1 macro (validación cruzada)" detalle="5 particiones estratificadas" />
          <Cifra valor={f3(datos.produccion.test_f1_macro)} texto="F1 macro (prueba)" />
          <Cifra valor={pct(datos.produccion.test_accuracy)} texto="Exactitud (prueba)" />
          <Cifra valor={entero(datos.total_muestras)} texto="Frases del dataset" detalle={`${entero(datos.muestras_train)} entrenamiento · ${entero(datos.muestras_test)} prueba`} />
          <Cifra valor={datos.clases.length} texto="Intenciones" />
          {ood.tasa_error_ood != null && (
            <Cifra valor={pct(ood.tasa_error_ood)} texto="Consultas ajenas aceptadas por error" detalle={`Detector ${datos.ood.estrategia} · ${ood.n_ood_test} consultas de prueba`} />
          )}
        </div>
        <p className="im-muted im-small">
          El modelo se eligió por F1 macro en validación cruzada sobre entrenamiento; el conjunto de prueba solo se usó para informar estas cifras.
        </p>
      </Tarjeta>

      <Tarjeta titulo="Comparación de modelos" subtitulo="Cada modelo con sus mejores hiperparámetros. La línea base muestra cuánto aporta el modelo frente a adivinar siempre la clase más frecuente.">
        <div className="im-table-wrap">
          <table className="im-table">
            <thead>
              <tr><th>Modelo</th><th>Hiperparámetros</th><th className="num">F1 macro CV</th><th className="num">Exactitud prueba</th><th className="num">F1 macro prueba</th><th className="num">F1 ponderado</th></tr>
            </thead>
            <tbody>
              {datos.modelos.map((m) => (
                <tr key={m.clave} className={m.en_produccion ? 'im-row-highlight' : ''}>
                  <td>{m.nombre}{m.en_produccion && <span className="im-chip">producción</span>}</td>
                  <td className="im-mono im-small">{Object.entries(m.parametros).map(([k, v]) => `${k.replace('modelo__', '')}=${v}`).join(', ') || '—'}</td>
                  <td className="num">{f3(m.cv_f1_macro)}</td>
                  <td className="num">{pct(m.accuracy)}</td>
                  <td className="num">{f3(m.f1_macro)}</td>
                  <td className="num">{f3(m.f1_weighted)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <Barras
          filas={datos.modelos.map((m) => ({ etiqueta: m.nombre, valor: m.f1_macro ?? 0 }))}
          formato={f3}
          maximo={1}
        />
      </Tarjeta>

      <Tarjeta
        titulo="Matriz de confusión y métricas por intención"
        subtitulo={`Conjunto de prueba (${entero(datos.muestras_test)} frases).`}
        extra={
          <div className="im-segmented">
            {datos.modelos.map((m) => (
              <button key={m.clave} type="button" className={m.clave === mostrado.clave ? 'active' : ''} onClick={() => setSeleccion(m.clave)}>
                {m.nombre}
              </button>
            ))}
          </div>
        }
      >
        <div className="im-grid-two">
          <MatrizConfusion matriz={mostrado.matriz_confusion} clases={datos.clases} />
          <TablaPorClase porClase={mostrado.por_clase} clases={datos.clases} />
        </div>
      </Tarjeta>

      {Object.keys(datos.terminos_influyentes || {}).length > 0 && (
        <Tarjeta titulo="Términos más influyentes" subtitulo="Los que más empujan la predicción hacia cada intención en el modelo en producción.">
          <div className="im-terms-grid">
            {Object.entries(datos.terminos_influyentes).map(([clase, terminos]) => (
              <div key={clase} className="im-terms">
                <h4>{etiqueta(clase)}</h4>
                <ol>{terminos.map(([t, peso]) => <li key={t}><span className="im-mono">{t}</span><span className="im-muted">{peso}</span></li>)}</ol>
              </div>
            ))}
          </div>
        </Tarjeta>
      )}

      {experimento?.disponible && <ResultadoExperimento exp={experimento} />}

      <Tarjeta titulo="Configuración del entrenamiento" subtitulo="Tomada de src/config.yaml al entrenar.">
        <div className="im-config">
          <div><span>Lema o raíz</span><strong>{datos.configuracion.nlp?.modo ?? '—'}</strong></div>
          <div><span>N-gramas</span><strong>{JSON.stringify(datos.configuracion.vectorizador?.ngram_range ?? '—')}</strong></div>
          <div><span>min_df / max_df</span><strong>{datos.configuracion.vectorizador?.min_df ?? '—'} / {datos.configuracion.vectorizador?.max_df ?? '—'}</strong></div>
          <div><span>max_features</span><strong>{String(datos.configuracion.vectorizador?.max_features ?? 'sin límite')}</strong></div>
        </div>
      </Tarjeta>
    </div>
  )
}

// Resultado del entrenamiento experimental, comparado con el modelo oficial
function ResultadoExperimento({ exp }) {
  const oficial = exp.oficial || {}
  return (
    <Tarjeta
      titulo={`Experimento con ${exp.archivo || 'archivo subido'}`}
      subtitulo={`${entero(exp.frases)} frases · ${exp.clases.length} intenciones · ${entero(exp.muestras_train)} entrenamiento / ${entero(exp.muestras_test)} prueba · ${exp.segundos} s. El modelo del chat no se modificó.`}
    >
      <div className="im-table-wrap">
        <table className="im-table">
          <thead><tr><th>Modelo evaluado con las frases de prueba del archivo</th><th className="num">Exactitud</th><th className="num">F1 macro</th><th className="num">F1 ponderado</th></tr></thead>
          <tbody>
            <tr className="im-row-highlight">
              <td>Experimento (entrenado con el archivo)</td>
              <td className="num">{pct(exp.experimento.accuracy)}</td>
              <td className="num">{f3(exp.experimento.f1_macro)}</td>
              <td className="num">{f3(exp.experimento.f1_weighted)}</td>
            </tr>
            <tr>
              <td>Modelo oficial (entrenado con el dataset del proyecto)</td>
              {oficial.disponible
                ? <><td className="num">{pct(oficial.accuracy)}</td><td className="num">{f3(oficial.f1_macro)}</td><td className="num">{f3(oficial.f1_weighted)}</td></>
                : <td colSpan={3} className="im-muted">{oficial.motivo}</td>}
            </tr>
          </tbody>
        </table>
      </div>
      {oficial.intenciones_desconocidas?.length > 0 && (
        <Aviso>El modelo oficial no conoce estas intenciones del archivo: {oficial.intenciones_desconocidas.map(etiqueta).join(', ')}.</Aviso>
      )}
      <div className="im-grid-two">
        <MatrizConfusion matriz={exp.experimento.matriz_confusion} clases={exp.clases} />
        <div>
          <h4 className="im-subhead">Frases por intención en el archivo</h4>
          <Barras filas={exp.clases.map((c) => ({ etiqueta: etiqueta(c), valor: exp.distribucion[c] }))} />
          <TablaPorClase porClase={exp.experimento.por_clase} clases={exp.clases} />
        </div>
      </div>
    </Tarjeta>
  )
}

// ---------------------------------------------------------------------------
// Pestaña 2: inventario
// ---------------------------------------------------------------------------
function PestanaInventario({ recarga, onImportar }) {
  const [datos, setDatos] = useState(null)
  const [error, setError] = useState('')
  const [umbral, setUmbral] = useState(5)

  useEffect(() => {
    setError('')
    apiInventario.resumenInventario(umbral).then(setDatos).catch((err) => setError(err.message))
  }, [recarga, umbral])

  if (error) return <Aviso tipo="error">{error}</Aviso>
  if (!datos) return <p className="im-muted">Cargando inventario…</p>

  const ind = datos.indicadores
  if (!datos.disponible || ind.productos === 0) {
    return (
      <Aviso>
        Todavía no hay inventario cargado. <button type="button" className="im-link" onClick={onImportar}>Importa un CSV o Excel</button> con productos y ventas.
      </Aviso>
    )
  }

  return (
    <div className="im-stack">
      <Tarjeta titulo="Resumen de la tienda" subtitulo={ind.desde ? `Ventas registradas del ${ind.desde} al ${ind.hasta}.` : 'Sin ventas registradas todavía.'}>
        <div className="im-stats">
          <Cifra valor={bs(ind.ingresos)} texto="Ingresos por ventas" />
          <Cifra valor={entero(ind.transacciones)} texto="Ventas registradas" detalle={`${entero(ind.unidades_vendidas)} unidades`} />
          <Cifra valor={bs(ind.ticket_promedio)} texto="Ticket promedio" />
          <Cifra valor={entero(ind.productos)} texto="Productos (SKU)" detalle={`${ind.categorias} categorías`} />
          <Cifra valor={entero(ind.unidades_en_stock)} texto="Unidades en stock" />
          <Cifra valor={bs(ind.valor_inventario)} texto="Valor del inventario" detalle="precio × stock" />
        </div>
      </Tarjeta>

      <div className="im-grid-two">
        <Tarjeta titulo="Productos más vendidos" subtitulo="Unidades vendidas.">
          {datos.mas_vendidos.length
            ? <Barras filas={datos.mas_vendidos.map((p) => ({ etiqueta: p.nombre, valor: p.unidades, detalle: bs(p.ingresos) }))} />
            : <p className="im-muted">Sin ventas.</p>}
        </Tarjeta>
        <Tarjeta titulo="Ventas por categoría" subtitulo="Ingresos.">
          {datos.ventas_por_categoria.length
            ? <Barras filas={datos.ventas_por_categoria.map((c) => ({ etiqueta: c.categoria, valor: c.ingresos, detalle: `${c.unidades} unidades` }))} formato={bs} />
            : <p className="im-muted">Sin ventas.</p>}
        </Tarjeta>
      </div>

      {datos.ventas_por_fecha.length > 0 && (
        <Tarjeta titulo="Ingresos por día" subtitulo="Pasa el mouse sobre una barra para ver la fecha y el monto.">
          <ColumnasPorFecha filas={datos.ventas_por_fecha} />
        </Tarjeta>
      )}

      <div className="im-grid-two">
        <Tarjeta
          titulo="Stock bajo"
          subtitulo={`Productos con ${umbral} unidades o menos.`}
          extra={
            <label className="im-inline-input">
              Umbral
              <input type="number" min="0" max="1000" value={umbral} onChange={(e) => setUmbral(Math.max(0, Number(e.target.value) || 0))} />
            </label>
          }
        >
          {datos.stock_bajo.length ? (
            <div className="im-table-wrap">
              <table className="im-table">
                <thead><tr><th>SKU</th><th>Producto</th><th>Talla</th><th>Color</th><th className="num">Stock</th></tr></thead>
                <tbody>
                  {datos.stock_bajo.map((p) => (
                    <tr key={p.sku}>
                      <td className="im-mono">{p.sku}</td>
                      <td>{p.nombre}</td>
                      <td>{p.talla || '—'}</td>
                      <td>{p.color || '—'}</td>
                      <td className="num"><span className={p.stock === 0 ? 'im-status im-status-critical' : 'im-status im-status-warning'}>{p.stock === 0 ? '⛔ agotado' : `⚠ ${p.stock}`}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : <p className="im-muted">Ningún producto bajo el umbral.</p>}
        </Tarjeta>
        <Tarjeta titulo="Stock por categoría" subtitulo="Unidades disponibles.">
          <Barras filas={datos.stock_por_categoria.map((c) => ({ etiqueta: c.categoria, valor: c.unidades, detalle: `${c.productos} productos` }))} />
        </Tarjeta>
      </div>
    </div>
  )
}

// Columnas verticales para la serie de ingresos diarios
function ColumnasPorFecha({ filas }) {
  const tope = Math.max(...filas.map((f) => f.ingresos), 0) || 1
  return (
    <div className="im-columns" role="list">
      {filas.map((f) => (
        <div key={f.fecha} className="im-column" role="listitem" title={`${f.fecha}: ${bs(f.ingresos)} · ${f.unidades} unidades`}>
          <span className="im-column-fill" style={{ height: `${(f.ingresos / tope) * 100}%` }} />
        </div>
      ))}
      <div className="im-columns-axis">
        <span>{filas[0].fecha}</span>
        <span>{filas[filas.length - 1].fecha}</span>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Pestaña 3: importación masiva
// ---------------------------------------------------------------------------
function PestanaImportar({ onImportado }) {
  const [archivo, setArchivo] = useState(null)
  const [reemplazar, setReemplazar] = useState(false)
  const [cargando, setCargando] = useState(false)
  const [resultado, setResultado] = useState(null)
  const [error, setError] = useState('')

  async function enviar(evento) {
    evento.preventDefault()
    if (!archivo) return setError('Elige un archivo .csv, .xlsx o .xls.')
    setCargando(true)
    setError('')
    setResultado(null)
    try {
      const r = await apiInventario.importar(archivo, reemplazar)
      setResultado(r)
      onImportado(r) // avisa al contenedor para recargar las otras pestañas
    } catch (err) {
      setError(err.message)
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className="im-stack">
      <Tarjeta
        titulo="Importación masiva"
        subtitulo="Sube un CSV o un Excel. Cada tabla (o cada hoja del Excel) se reconoce por sus columnas."
      >
        <ul className="im-formats">
          <li><strong>Productos</strong> <span className="im-mono">sku, nombre, categoria, talla, color, precio, stock</span> → se guardan en la base y alimentan las respuestas del chat.</li>
          <li><strong>Ventas</strong> <span className="im-mono">fecha, sku, cantidad, precio_unitario</span> → reportes de ventas y más vendidos.</li>
          <li><strong>Frases</strong> <span className="im-mono">texto, intencion</span> → entrena un modelo experimental y muestra sus métricas (el modelo del chat no cambia).</li>
        </ul>
        <div className="im-row">
          <span className="im-muted im-small">Plantillas:</span>
          {Object.keys(PLANTILLAS).map((n) => (
            <button key={n} type="button" className="im-btn-ghost" onClick={() => descargarPlantilla(n)}>{n}</button>
          ))}
        </div>

        <form onSubmit={enviar} className="im-upload">
          <label className="im-dropzone">
            <input
              type="file"
              accept=".csv,.xlsx,.xls"
              onChange={(e) => { setArchivo(e.target.files[0] || null); setResultado(null); setError('') }}
            />
            <span className="im-dropzone-icon">⇪</span>
            <span>{archivo ? archivo.name : 'Haz clic para elegir un archivo .csv, .xlsx o .xls (máximo 5 MB)'}</span>
          </label>
          <label className="im-check">
            <input type="checkbox" checked={reemplazar} onChange={(e) => setReemplazar(e.target.checked)} />
            Reemplazar los datos anteriores (si no, se agregan y los productos con el mismo SKU se actualizan)
          </label>
          <button type="submit" className="im-btn-primary" disabled={cargando}>
            {cargando ? 'Importando… (si hay frases, también se entrena el modelo)' : 'Importar'}
          </button>
        </form>
        {error && <Aviso tipo="error">{error}</Aviso>}
      </Tarjeta>

      {resultado && (
        <Tarjeta titulo={`Resultado: ${resultado.archivo}`}>
          <div className="im-table-wrap">
            <table className="im-table">
              <thead><tr><th>Hoja</th><th>Tipo</th><th className="num">Leídas</th><th className="num">Importadas</th><th className="num">Omitidas</th></tr></thead>
              <tbody>
                {resultado.hojas.map((h) => (
                  <tr key={`${h.hoja}-${h.tipo}`}>
                    <td>{h.hoja}</td>
                    <td>{h.tipo}</td>
                    <td className="num">{h.filas_leidas}</td>
                    <td className="num">{h.tipo === 'frases' ? 'entrenamiento' : h.filas_importadas}</td>
                    <td className="num">{h.filas_omitidas}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {resultado.hojas.filter((h) => h.errores.length).map((h) => (
            <details key={`err-${h.hoja}-${h.tipo}`} className="im-errors">
              <summary>Filas omitidas en {h.hoja} ({h.filas_omitidas})</summary>
              <ul>{h.errores.map((e) => <li key={e.fila}>Fila {e.fila}: {e.motivo}</li>)}</ul>
            </details>
          ))}
          {resultado.experimento && (
            <Aviso tipo="ok">
              Modelo experimental entrenado: F1 macro {f3(resultado.experimento.experimento.f1_macro)} con {resultado.experimento.frases} frases.
              Revisa la comparación completa en la pestaña “Métricas del modelo”.
            </Aviso>
          )}
        </Tarjeta>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Contenedor con las tres pestañas
// ---------------------------------------------------------------------------
const PESTANAS = [
  { id: 'metricas', texto: 'Métricas del modelo' },
  { id: 'inventario', texto: 'Inventario' },
  { id: 'importar', texto: 'Importar datos' },
]

export default function InventarioMetricas({ onVolver }) {
  const [pestana, setPestana] = useState('metricas')
  const [recarga, setRecarga] = useState(0) // al cambiar, las pestañas vuelven a pedir datos

  return (
    <main className="im-root fade-in">
      <div className="im-header">
        <div>
          <button type="button" className="im-back" onClick={onVolver}>← Volver al asistente</button>
          <h2 className="im-title">Inventarios y métricas</h2>
          <p className="im-subtitle">Resultados del entrenamiento del modelo y analíticas del inventario de la tienda.</p>
        </div>
        <nav className="im-tabs" role="tablist">
          {PESTANAS.map((p) => (
            <button key={p.id} type="button" role="tab" aria-selected={pestana === p.id} className={pestana === p.id ? 'active' : ''} onClick={() => setPestana(p.id)}>
              {p.texto}
            </button>
          ))}
        </nav>
      </div>

      {pestana === 'metricas' && <PestanaMetricas recarga={recarga} />}
      {pestana === 'inventario' && <PestanaInventario recarga={recarga} onImportar={() => setPestana('importar')} />}
      {pestana === 'importar' && <PestanaImportar onImportado={() => setRecarga((n) => n + 1)} />}
    </main>
  )
}
