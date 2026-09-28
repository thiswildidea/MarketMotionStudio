# Market Motion Studio

Esta aplicación convierte indicadores del mercado de acciones A en vídeos verticales para el móvil. Elija un periodo, mire la vista previa hasta que se lea bien y exporte un MP4. No hace falta instalar nada más.

## Elegir un mercado

En Ajustes se elige de qué mercado toma sus cotizaciones la aplicación; las acciones A por defecto. El cambio surte efecto tras reiniciar la aplicación.

- **Acciones A**: las siete páginas están disponibles.
- **Hong Kong**: la matriz de rentabilidad y el calendario funcionan; la carrera de sectores usa los cuatro subíndices Hang Seng; **no hay cifra para todo el mercado, así que esa página se oculta**.
- **Estados Unidos**: la matriz de rentabilidad y el calendario funcionan; la carrera de sectores usa diez ETF sectoriales SPDR; la página de volumen conserva solo el modo diario, porque el endpoint de minutos no sirve datos estadounidenses; **los importes están en dólares y la página de volumen del mercado se oculta**.

## Volumen negociado del mercado

El importe negociado cada día en todo el mercado: los importes de los índices compuestos de Shanghái y Shenzhen sumados, una barra por sesión.

- Solo se conservan los días en que negociaron todos los mercados incluidos, para que el festivo de uno de ellos no haga parecer que el total se desploma.
- Una sesión aún en curso se descarta. Un día sin terminar contiene solo su subasta de apertura y se dibujaría como una barra pegada al eje.
- O mirar solo un segmento: cada bolsa, cada board principal, STAR, ChiNext. Los boards principales se derivan del total de la bolsa menos su board de crecimiento; el BSE 50 sigue siendo una medida de componentes.
- Solo el mercado de acciones A da un total de todo el mercado. Con Hong Kong o Estados Unidos la página se retira de la navegación.

## Volumen y rotación

El volumen de un valor frente a su tasa de rotación, en dos paneles superpuestos.

- De una sesión a otra, volumen y tasa de rotación son proporcionales, así que los dos paneles tienen casi la misma forma. Dentro de una jornada, el volumen por minuto y la rotación acumulada se ven de verdad distintos, y esa es la imagen más interesante.
- La fuente intradía solo guarda las últimas sesiones, así que ese modo ofrece esas en lugar de una fecha cualquiera.
- Los datos por minuto solo se sirven para acciones A y Hong Kong; en Estados Unidos ese modo no se ofrece.

## Carrera de sectores

![La página completa: vista previa a la izquierda, barra de reproducción abajo, ajustes a la derecha.](media/sector-race.png)

Un conjunto de sectores o acciones dibujado como barras horizontales que se adelantan unas a otras, y el orden cambia hasta el último fotograma.

- Dos medidas: la variación del periodo en % y su volumen en centenas de millones de yuanes. Cambiar de medida solo re-tiñe los mismos datos; no vuelve a consultar.
- Cuatro listas: sectores Shenwan de nivel 1, temas de actualidad, personalizada (marcar casillas) y acciones individuales (añadir por búsqueda). La lista personalizada empieza rellena con los sectores Shenwan de nivel 1.
- Las listas integradas siguen al mercado: sectores Shenwan de nivel 1 y temas de actualidad para acciones A, los cuatro subíndices Hang Seng para Hong Kong, diez ETF sectoriales SPDR para Estados Unidos. Las listas personalizada y de acciones existen en todos los mercados.
- El periodo puede ser de 1, 3, 6 o 12 meses, o fechas de inicio y fin personalizadas.
- Una lista tiene un mínimo y un máximo de elementos — pocas barras no es una carrera, demasiadas se amontonan.

## Matriz de rentabilidad

![La página completa: vista previa a la izquierda, barra de reproducción abajo, ajustes a la derecha.](media/monthly-matrix.png)

Barras mensuales dispuestas en una cuadrícula: el modo año muestra la estacionalidad de un instrumento a lo largo de una década; el modo comparación pone varios instrumentos en paralelo para mostrar la rotación.

- Modo año: elija un instrumento (búsqueda o un índice amplio preestablecido); el rango es de 1 a 10 años o todo. Una petición devuelve una década de barras mensuales.
- Modo comparación: de 2 a 14 instrumentos de una lista (sectores de nivel 1 / temas / índices amplios / personalizada / acciones) en paralelo, de 6 a 48 meses.
- La cuadrícula se enciende celda a celda en orden temporal; al final se muestran el mejor y el peor mes del rango, entre otras estadísticas.
- Los datos mensuales cubren una década de una vez, así que aquí no hay tope diario de días — pero demasiados instrumentos se salen del encuadre.

## Calendario de subidas y bajadas

![La página completa: vista previa a la izquierda, barra de reproducción abajo, ajustes a la derecha.](media/gain-calendar.png)

Cualquier acción o índice chino, su subida o bajada diaria dispuesta en celdas de calendario por mes: rojo al alza, verde a la baja.

- Busque por código, nombre o pinyin; los preestablecidos son índices amplios. Solo instrumentos del mercado seleccionado.
- La lista de favoritos se comparte con la página de acciones de la app: un favorito añadido en cualquiera de las dos aparece en ambas.
- El periodo es de 1, 3, 6 o 12 meses, o personalizado; un instrumento solo sigue sujeto al límite de unos 640 días calendario.
- Las estadísticas finales dan el recuento de sesiones al alza y a la baja.

## Plan DCA

![La página completa: vista previa a la izquierda, barra de reproducción abajo, ajustes a la derecha.](media/dca-plan.png)

Comprar un valor con importe y cadencia fijos — cada día de bolsa, cada semana o cada mes — y ver en animación lo que la disciplina llegó a ser.

- Los instrumentos de un toque siguen al mercado: ETF amplios y de oro en las acciones A, los fondos rastreados de Hong Kong, SPY, QQQ y GLD en Estados Unidos.
- El importe y la frecuencia se ajustan a gusto; el período es de tres, cinco o diez años, o hasta donde lleguen los datos (unos trece años).
- La rentabilidad se calcula sobre cierres ajustados hacia atrás, sin comisiones. El resultado describe la serie de precios, no una factura que alguien pudiera haber ejecutado.

## Rentabilidad de cartera

![La página completa: vista previa a la izquierda, barra de reproducción abajo, ajustes a la derecha.](media/position.png)

Una sola compra, mantenida durante años — un millón en 中国平安 en 2015, por ejemplo — animada como lo que hicieron el valor y la rentabilidad.

- Los nombres sugeridos siguen al mercado: en China, las acciones que la gente de verdad dice haber mantenido (Ping An, Moutai, CMB…); en Hong Kong, Tencent, HSBC y el Tracker Fund; en Estados Unidos, Apple, Berkshire y SPY.
- El capital inicial y el periodo de tenencia son tuyos; el periodo puede ser de tres, cinco o diez años, o hasta donde lleguen los datos (unos trece años).
- La rentabilidad se calcula sobre cierres ajustados hacia atrás — dividendos reinvertidos, sin comisiones. El ajuste hacia atrás se ancla en la salida a bolsa y acumula los dividendos hacia delante, así que los primeros años de un gran pagador nunca se vuelven negativos, como puede pasar con el ajuste hacia delante.

## Vídeo

El encuadre es siempre 9:16. Todo lo demás lo decide usted.

- La duración cambia el ritmo, no recorta la animación: la entrada, el crecimiento de las barras y las estadísticas finales se reparten a lo largo de lo que elija.
- Los márgenes se anotan sobre un encuadre de 1080×1920 y se escalan a la resolución de exportación, así que una composición ajustada una vez sirve en todos los tamaños. El margen izquierdo decide además dónde caen las etiquetas del eje: si es demasiado pequeño, los números salen del encuadre.
- Las guías de zona segura marcan lo que una aplicación de móvil tapa con su propia interfaz. Se dibujan en la vista previa y nunca en un archivo.

## Dónde van los vídeos

Las exportaciones se escriben en una carpeta que usted elige con un selector. Mientras no haya ninguna, la primera exportación la pide y luego la recuerda; la configuración permite cambiarla u olvidarla.

## Imagen de fondo

La página de configuración puede colocar una imagen detrás de la ventana, atenuada. Las tarjetas y paneles siguen siendo opacos y el panel de navegación deja pasar solo un poco, de modo que la imagen se ve sobre todo a su alrededor. La vista previa del vídeo tiene su propio fondo sólido y no se ve afectada.

- Elija una imagen del equipo o use directamente uno de los fondos y las imágenes de pantalla de bloque que incluye Windows.
- La imagen elegida se copia a la carpeta de la aplicación; mover o eliminar el original no afecta al fondo.
- El control de intensidad de máscara define cuánto se oscurece la imagen, del 30 % al 95 %.
- No se muestra ninguna imagen mientras el alto contraste esté activado.
## Fondo de la animación

En la página de configuración puedes cambiar sobre qué se dibuja la animación: el degradado integrado, dos colores tuyos o una imagen. Se aplica por igual a la vista previa, al vídeo exportado y a la imagen de portada: los tres los dibuja el mismo motor, así que no hay un «se ve bien en la vista previa y distinto en el archivo».

- Al elegir colores indicas un tono superior y otro inferior, y el fotograma pasa de uno a otro. Mejor oscuros: todos los tonos de texto son claros y un fondo claro dificulta leer las cifras.

- Elegir una imagen funciona igual que en el fondo de la ventana: una de tu equipo o un fondo que Windows ya incluye. La que elijas se copia a la carpeta de la aplicación.

- La imagen rellena el fotograma y lo que sobra se recorta, así que nunca se deforma.

- El control de atenuación decide cuánto se retira la imagen hacia el fondo propio de la página, del 20 % al 95 %.

## Los datos, y lo que no le dirán

Las cotizaciones vienen de los puntos de acceso públicos de Tencent Finance, y el encuadre siempre cita la fuente. Estos vídeos describen lo que ya se ha negociado. Son solo a título informativo y no constituyen asesoramiento de inversión.

- Los importes se convierten a cientos de millones de yuanes, y el volumen pasa a una unidad mayor cuando las cifras lo piden, para que el eje siga siendo legible.
- Los importes se convierten a cientos de millones — de yuanes en el continente y Hong Kong, de dólares en Estados Unidos. Cada mercado mantiene su propia divisa.
- Un periodo de más de unos 640 días naturales se rechaza en lugar de recortarse en silencio, porque eso es todo lo que devuelve una petición a la fuente.

## Actualizar

Cuando Microsoft Store tiene una versión más reciente, aparece un botón **Actualizar** junto a Configuración en el panel de navegación; con un clic se instala.

- Solo aparece cuando la Store tiene de verdad una versión más reciente. Una compilación de desarrollo o instalada aparte nunca lo ve, y eso es lo esperado.
- La aplicación se cierra mientras se instala y vuelve a abrirse con la nueva versión, y el botón desaparece. Si hay una exportación en curso, pregunta antes.
- Si no se puede instalar, dice por qué —solo por Wi-Fi, batería demasiado baja— y también se puede instalar desde Microsoft Store.

## ¿Algo va mal?

Escriba a gaqo@outlook.com contando qué estaba haciendo y qué esperaba en su lugar. El número de versión está en la página de configuración.
