# AShare Motion Studio

Esta aplicación convierte indicadores del mercado de acciones A en vídeos verticales para el móvil. Elija un periodo, mire la vista previa hasta que se lea bien y exporte un MP4. No hace falta instalar nada más.

## Volumen negociado del mercado

El importe negociado cada día en todo el mercado: los importes de los índices compuestos de Shanghái y Shenzhen sumados, una barra por sesión.

- Solo se conservan los días en que negociaron todos los mercados incluidos, para que el festivo de uno de ellos no haga parecer que el total se desploma.
- Una sesión aún en curso se descarta. Un día sin terminar contiene solo su subasta de apertura y se dibujaría como una barra pegada al eje.
- La opción de Pekín añade el índice BSE 50, que cubre solo sus componentes y no la bolsa entera. Es otra medida, y menor.

## Volumen de un valor

El volumen de un valor frente a su tasa de rotación, en dos paneles superpuestos.

- De una sesión a otra, volumen y tasa de rotación son proporcionales, así que los dos paneles tienen casi la misma forma. Dentro de una jornada, el volumen por minuto y la rotación acumulada se ven de verdad distintos, y esa es la imagen más interesante.
- La fuente intradía solo guarda las últimas sesiones, así que ese modo ofrece esas en lugar de una fecha cualquiera.

## Carrera de sectores

Un conjunto de sectores o acciones dibujado como barras horizontales que se adelantan unas a otras, y el orden cambia hasta el último fotograma.

- Dos medidas: la variación del periodo en % y su volumen en centenas de millones de yuanes. Cambiar de medida solo re-tiñe los mismos datos; no vuelve a consultar.
- Cuatro listas: sectores Shenwan de nivel 1, temas de actualidad, personalizada (marcar casillas) y acciones individuales (añadir por búsqueda). La lista personalizada empieza rellena con los sectores Shenwan de nivel 1.
- El periodo puede ser de 1, 3, 6 o 12 meses, o fechas de inicio y fin personalizadas.
- Una lista tiene un mínimo y un máximo de elementos — pocas barras no es una carrera, demasiadas se amontonan.

## Matriz mensual

Barras mensuales dispuestas en una cuadrícula: el modo año muestra la estacionalidad de un instrumento a lo largo de una década; el modo comparación pone varios instrumentos en paralelo para mostrar la rotación.

- Modo año: elija un instrumento (búsqueda o un índice amplio preestablecido); el rango es de 1 a 10 años o todo. Una petición devuelve una década de barras mensuales.
- Modo comparación: de 2 a 14 instrumentos de una lista (sectores de nivel 1 / temas / índices amplios / personalizada / acciones) en paralelo, de 6 a 48 meses.
- La cuadrícula se enciende celda a celda en orden temporal; al final se muestran el mejor y el peor mes del rango, entre otras estadísticas.
- Los datos mensuales cubren una década de una vez, así que aquí no hay tope diario de días — pero demasiados instrumentos se salen del encuadre.

## Calendario de subidas y bajadas

Cualquier acción o índice chino, su subida o bajada diaria dispuesta en celdas de calendario por mes: rojo al alza, verde a la baja.

- Busque por código, nombre o pinyin; los preestablecidos son índices amplios. Solo acciones e índices de la bolsa china.
- La lista de favoritos se comparte con la página de acciones de la app: un favorito añadido en cualquiera de las dos aparece en ambas.
- El periodo es de 1, 3, 6 o 12 meses, o personalizado; un instrumento solo sigue sujeto al límite de unos 640 días calendario.
- Las estadísticas finales dan el recuento de sesiones al alza y a la baja.

## Vídeo

El encuadre es siempre 9:16. Todo lo demás lo decide usted.

- La duración cambia el ritmo, no recorta la animación: la entrada, el crecimiento de las barras y las estadísticas finales se reparten a lo largo de lo que elija.
- Los márgenes se anotan sobre un encuadre de 1080×1920 y se escalan a la resolución de exportación, así que una composición ajustada una vez sirve en todos los tamaños. El margen izquierdo decide además dónde caen las etiquetas del eje: si es demasiado pequeño, los números salen del encuadre.
- Las guías de zona segura marcan lo que una aplicación de móvil tapa con su propia interfaz. Se dibujan en la vista previa y nunca en un archivo.

## Dónde van los vídeos

Las exportaciones se escriben en una carpeta que usted elige con un selector. Mientras no haya ninguna, la primera exportación la pide y luego la recuerda; la configuración permite cambiarla u olvidarla.

## Los datos, y lo que no le dirán

Las cotizaciones vienen de los puntos de acceso públicos de Tencent Finance, y el encuadre siempre cita la fuente. Estos vídeos describen lo que ya se ha negociado. Son solo a título informativo y no constituyen asesoramiento de inversión.

- Los importes se convierten a cientos de millones de yuanes, y el volumen pasa a una unidad mayor cuando las cifras lo piden, para que el eje siga siendo legible.
- Un periodo de más de unos 640 días naturales se rechaza en lugar de recortarse en silencio, porque eso es todo lo que devuelve una petición a la fuente.

## ¿Algo va mal?

Escriba a gaqo@outlook.com contando qué estaba haciendo y qué esperaba en su lugar. El número de versión está en la página de configuración.
