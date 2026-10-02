# Market Motion Studio

Esta aplicación convierte indicadores del mercado de acciones A en vídeos verticales para el móvil. Elija un periodo, mire la vista previa hasta que se lea bien y exporte un MP4. No hace falta instalar nada más.

## Elegir un mercado

En Ajustes se elige de qué mercado toma sus cotizaciones la aplicación; las acciones A por defecto. El cambio surte efecto tras reiniciar la aplicación.

- **Acciones A**: las ocho páginas están disponibles.
- **Hong Kong**: la matriz de rentabilidad y el calendario funcionan; la carrera de sectores usa los cuatro subíndices Hang Seng; **no hay cifra para todo el mercado, así que esa página se oculta**.
- **Estados Unidos**: la matriz de rentabilidad y el calendario funcionan; la carrera de sectores usa diez ETF sectoriales SPDR; la página de volumen conserva solo el modo diario, porque el endpoint de minutos no sirve datos estadounidenses; **los importes están en dólares y la página de volumen del mercado se oculta**.



## Moverse entre páginas

Los dos botones de la izquierda de la barra de título retroceden y avanzan por las páginas visitadas, como lo hace un navegador: **Alt+Flecha izquierda** y **Alt+Flecha derecha**, o los botones laterales del ratón.

- Cada página se conserva tal como la dejaste, así que volver a ella devuelve el periodo y la vista previa en el estado en que estaban, no una página recién abierta.
- Como en un navegador, elegir una página nueva borra lo que había por delante.
- También funcionan con el panel de navegación plegado, justo cuando la vista previa más necesita el ancho.

## Volumen negociado del mercado

El importe negociado cada día en todo el mercado: los importes de los índices compuestos de Shanghái y Shenzhen sumados, una barra por sesión.

- Solo se conservan los días en que negociaron todos los mercados incluidos, para que el festivo de uno de ellos no haga parecer que el total se desploma.
- Una sesión aún en curso se descarta. Un día sin terminar contiene solo su subasta de apertura y se dibujaría como una barra pegada al eje.
- O mirar solo un segmento: cada bolsa, cada board principal, STAR, ChiNext. Los boards principales se derivan del total de la bolsa menos su board de crecimiento; el BSE 50 sigue siendo una medida de componentes.
- Solo el mercado de acciones A da un total de todo el mercado. Con Hong Kong o Estados Unidos la página se retira de la navegación.

## Velas

Las velas de un instrumento: diarias, semanales o mensuales, dibujadas de cuatro formas, con sus medias y su volumen debajo.

- **Intervalo** decide cuánto tiempo de mercado cubre una vela: un día, una semana o un mes. Cambiarlo vuelve a consultar la fuente, porque en ella las tres son series distintas.
- **Tipo de dibujo** decide cómo se dibujan los mismos cuatro precios: velas, barras OHLC, línea de cierre o área de cierre. Pasar de uno a otro no vuelve a consultar nada.
- **Animación** es o bien la llegada de las velas una tras otra hasta trazar todo el periodo, o bien una ventana fija que avanza. La segunda es lo que mantiene la vela lo bastante ancha para leerse en un periodo largo, y esa anchura es el ajuste **Ventana**.
- Las medias móviles MA5, MA10 y MA20 pueden superponerse a las velas; el panel de volumen de abajo se puede apagar, y el panel de precio recupera ese espacio.
- Una semana o un mes aún en curso queda fuera. Una vela hecha de tres días no es una semana.
- Todos los mercados se leen en su serie ajustada, así que un día de split no se dibuja como una caída, ni un dividendo tampoco.

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




## Carrera de capitalización

Las quince mayores compañías de un mercado como barras horizontales ordenadas por
capitalización, con el orden cambiando hasta el último fotograma. Muestreo mensual.

- **La clasificación se rehace en cada periodo.** La descarga pregunta primero a la fuente la
  clasificación actual por capitalización, toma las doscientas primeras como grupo y añade los
  valores pesados que estaban en ella y han salido; cada periodo muestra después los quince mayores
  de ese grupo. Así los miembros entran y salen de verdad — 2016 era petróleo y bancos, 2026 ha
  sumado 茅台, 宁德时代 e 工业富联. Un grupo escrito en el programa se dejó una compañía que salió
  a bolsa y se puso primera de inmediato; ahora el grupo se pregunta en vez de recordarse.
- **Una capitalización pasada se calcula**: la capitalización de hoy por el cociente de precios
  ajustado del periodo. Las ampliaciones y los desdoblamientos se anulan en la serie ajustada; los
  dividendos no — se reinvierten, así que el valor pasado de un pagador fuerte queda bajo. Solo la
  cifra del último fotograma viene directamente de la fuente.
- **Una compañía que aún no cotizaba crece desde cero**: los valores que salieron a bolsa en 2018
  suben desde la línea base el día de su entrada, sin ocupar un sitio de antemano.
- **El intervalo es el mes, no el día**: ciento veinte periodos en diez años, doce en uno, y el
  encabezado del fotograma cuenta meses. Una clasificación por capitalización es una magnitud
  lenta, y una muestra mensual obtiene toda la historia en una petición.
- **Cada mercado tiene sus propios quince.** Los tres nunca se mezclan: su dinero no es el mismo.
  Hong Kong y Nueva York mantienen un grupo fijo, porque ninguna clasificación accesible a esta
  aplicación les sirve.





## Prima A/H

Cuánto más cara es la cotización continental de una compañía que la de Hong Kong, para las
compañías que cotizan en ambos lados: mes a mes, en barras que se adelantan.

- **Prima = precio A ÷ (precio H × HKD/CNY) − 1.** Aquí nada se calcula: las dos partes son precios
  realmente pagados en el mismo instante, y por eso esta es la única página que toma precios **sin
  ajustar**. Una serie ajustada hacia atrás infla los precios recientes, y dos mercados ajustados
  por separado no son comparables: la acción A de ICBC marca 8,28 en pantalla y la serie ajustada
  declara 13,34, con lo que una prima del +26% pasa a +245%.
- **La misma diferencia se escribe en los dos sentidos.** Esta página da A frente a H, la forma
  habitual: +194% significa que la acción continental cuesta casi el triple que la de Hong Kong.
  Algunos servicios muestran la misma cifra al revés (溢价(H/A)) y para 新华制药 dan −66% el mismo
  día. Es el mismo hecho (1 ÷ (1 − 0,66) − 1 = 1,94): ni otro precio ni un error de cálculo.
- **El fotograma dibuja las quince más caras**, así que las barras crecen hacia la derecha:
  incluso la decimoquinta superaba el veinte por ciento. Solo dos de las sesenta y nueve van al
  revés, con la acción H por encima de la A, y ambas quedan al final de la lista, fuera de cuadro.
- **Cuanto más largo el periodo, menos compañías quedan.** Hay sesenta y nueve dobles cotizaciones
  conocidas como candidatas, pero solo se dibuja la pareja cuyas dos partes cubren todo el periodo:
  una cotización en Hong Kong de menos de dos años se descarta.
- **Muestreo mensual.** «El más largo» son unos nueve años, y el límite es la serie del tipo de
  cambio, que solo llega a 2016. Las tres partes cierran el mes en días distintos, así que se agrupa
  por mes natural y se toma el último precio del mes, en vez de intersecar por fecha.
- **La lista es interna.** Ninguna de las dos fuentes responde a «qué cotizaciones continentales
  tienen también una en Hong Kong». Lo que sí se puede es comprobarla: cada pareja se releyó de la
  fuente el 2026-10-02, y 海通证券 es lo que esa comprobación eliminó (acciones H excluidas de
  cotización tras la fusión con 国泰海通).

## Días extremos

Un instrumento y los días en que más se movió — barras horizontales ordenadas por magnitud.
**Las filas de este tablero son días, no empresas**, algo que no hace ninguna otra página: el valor
de una fila es cuánto se movió ese día respecto al cierre del día anterior, y una vez ocurrido ese
día el valor ya no cambia.

- **El movimiento es la variación del cierre ajustado.** Ajustado, porque un día de descuento de
  dividendo no es un desplome: esa mañana el precio cae el importe del dividendo, y una serie sin
  ajustar pondría ese día a la cabeza de las mayores caídas de la historia, cuando nadie perdió
  nada.
- **Ordenado por magnitud, no por signo.** −7,7 % y +8,1 % son movimientos del mismo tamaño y por
  eso se colocan juntos; ordenar por el valor con signo pondría cada bajada debajo de cada subida.
  Las barras crecen hacia los dos lados: **una subida hacia la derecha, en rojo; una bajada hacia
  la izquierda, en verde**.
- **Un día se clasifica solo cuando ha ocurrido.** Los veinticuatro movimientos más grandes del
  periodo son los candidatos y el fotograma dibuja los quince mayores; un día no participa hasta
  que llega su fecha, así que el tablero se llena con los años en lugar de empezar lleno.
- **Cualquier instrumento que cotice en el mercado, no solo los índices amplios.** Escriba un
  código, un nombre o pinyin en el buscador: una acción concreta y un fondo cotizado pertenecen a
  este tablero tanto como un índice, y la lista de abajo es solo un atajo a los habituales. Cambiar
  de mercado sustituye esa lista y deja atrás un instrumento de otro mercado; elegir instrumento o
  periodo solo guarda una preferencia — nada se descarga hasta pulsar 取数.
- **El periodo más largo es de unos treinta y cinco años**, que es el límite de la fuente: una
  petición trae unas 640 barras diarias y el retroceso hace veinte como máximo. Un periodo con
  menos de sesenta días de negociación se rechaza — el día más grande de un mes tranquilo no es un
  dato que merezca un tablero.
- **La fecha en la parte superior es el eje del tiempo** y la barra de abajo es el progreso. La
  línea de encabezado lleva el periodo, el número de días de negociación y el de días candidatos.

## Corredores de divisas

Una fila por par, y **la fila es el corredor mismo**: un extremo es el nivel más bajo que el par
ha tenido en el periodo elegido, el otro el más alto, y la marca es la cotización de hoy. Este
tablero no es como los demás — en los demás la longitud de una barra dice *cuánto*, aquí la fila
ocupa todo el ancho en cada fotograma, y lo que se mueve es la marca, junto con el corredor.

- **El corredor se ensancha.** Sus paredes son el mínimo y el máximo **hasta ahora**, no los de todo
  el periodo. Un mes que va más lejos que todos los anteriores empuja una de las dos hacia afuera, y
  un par al 100% está en lo más caro que ha estado nunca — no en un límite.
- **Cada par se mide contra su propio rango.** 157,92 en USD/JPY y 1,1245 en EUR/USD no son dos
  puntos de una misma escala; es la normalización la que permite que seis pares quepan en un cuadro.
  El precio es que un corredor estrecho y uno ancho se ven igual, y por eso ambos extremos se
  imprimen bajo cada fila.
- **Velas mensuales, sin ajustar.** Una divisa no tiene dividendo ni split que ajustar, y la página
  toma el mismo camino en crudo por la fuente que toma la página A+H.
- **La cobertura difiere, y por eso hay dos listas**: USD/CNY llega hasta 2005, los otros cinco
  pares del renminbi hasta 2016; los principales cruces empiezan todos en 2005-07 y traen 325 meses.
  En un solo tablero se leería cuándo empezó la fuente a cotizar cada par.
- **El ajuste de mercado no aplica aquí**: un par de divisas no pertenece a ninguna bolsa, y el
  tablero es el mismo sea cual sea el mercado en vigor.
- El periodo más largo es de unos veinte años, la cobertura mensual de la fuente; menos de doce meses
  se rechaza — son unas semanas de movimiento, no un corredor.

## Carrera de índices

Una fila por índice, y la fila es **cuánto ha avanzado ese índice desde su propio primer mes en
el periodo** — no su nivel. 3.800 en el Shanghai Composite y 5.700 en el S&P 500 no son dos puntos de
una misma escala: dibujar niveles sería un tablero sobre dónde empezó a contar cada índice.

- **Un índice que llega tarde no está en el tablero hasta que llega.** El S&P llega hasta 1950, el Dow
  solo hasta 2009, y el índice Hang Seng Tech empieza en 2020. Está ausente, no aparcado en el 0,00%
  — ahí se situaría por encima de todo índice que haya caído alguna vez, y se leería como un mercado
  en el que no pasó nada.
- **Mensual, y ahora ajustado.** Un índice no reparte nada, pero una acción paga dividendos y
  desdobla sus títulos: Apple marca +193 % en diez años sin ajustar y +1183 % ajustado, porque la
  serie sin ajustar lleva acantilados por los que ningún tenedor cayó nunca. Los índices no se
  alteran: si se pide ajuste, la fuente responde a un índice con las mismas filas de siempre, y los
  doce resultaron idénticos en ambas vías. Lo que sí trae el tablero es una diferencia que conviene
  declarar: la fila de un índice es una rentabilidad **de precio**, porque un índice no es una
  posición, mientras que la de una acción es **total**, con dividendos y desdoblamientos
  incorporados.
- **El ajuste de mercado no gobierna esta página**: lee tres mercados a la vez, y cambiar de mercado
  no la cambia. Pueden tomarse las seis del continente, las tres de Hong Kong, las tres de Nueva York
  o las doce.
- El periodo más largo está limitado por el techo mensual de la fuente — 430 velas, unos treinta y
  cinco años; menos de doce meses se rechaza: eso es un esprint, no una carrera de fondo.
- **O su propia lista.** El último grupo del menú es una lista propia: escriba un código, un
  nombre o pinyin para añadir uno, y un valor continental, uno de Hong Kong y uno de Nueva York
  pueden convivir en ella — este tablero nunca consulta el ajuste de mercado. Una lista para cuatro
  tableros: una acción añadida aquí también se ofrece en la carrera de activos, en las caídas y en
  la tasa de acierto. Con menos de tres se rechaza la descarga.

## Clases de activos

Una fila por clase de activo, y la fila es **lo que ganó mantenerlo** — no su cotización. Las ocho
son fondos cotizados en una bolsa continental, comprados con el mismo dinero, así que se pueden
comparar directamente.

- **Los dividendos se reintegran, y también los splits.** Un bono y un fondo monetario pagan casi
  por completo en rentas: el precio del ETF monetario pasó de 100,161 a 100,901 en trece años, lo
  que sin ajuste es +0,0 % — y dibujaría al final del tablero la única fila de aquí que nunca cayó.
  Un fondo que dividió sus participaciones es aún más claro: el ETF Nasdaq da +136 % sin ajuste,
  mientras que el índice que sigue se sextuplicó en la misma década.
- **Deliberadamente lo contrario de la carrera de índices.** Un índice no paga dividendos, así que
  aquella página se deja intacta; un fondo sí paga, así que esta debe ajustarse. Los dos caminos no
  se mezclan.
- **Las dos filas extranjeras llevan el tipo de cambio.** Los ETF de Nasdaq y Hang Seng cotizan en
  yuanes, así que la divisa ya está dentro — que es lo que un tenedor continental recibió de verdad.
- **Los inicios difieren.** La fila más antigua empieza en 2012 y el fondo de materias primas solo
  en 2019. Una fila que aún no ha entrado está ausente, no en 0,00 %.
- **El ajuste de mercado no gobierna esta página**: las ocho cotizan en el continente. Menos de doce
  meses se rechaza.
- **O su propia lista.** El último grupo del menú es una lista propia: escriba un código, un
  nombre o pinyin para añadir uno, y en ella pueden mezclarse los tres mercados. Una lista para
  cuatro tableros: una acción añadida aquí también se ofrece en los otros tres; se descarga
  ajustada, exactamente como los ocho fondos, de modo que dividendos y desdoblamientos están en la
  cifra. Con menos de tres se rechaza la descarga.

## Caídas

Una fila es **cuánto por debajo de su propio máximo está una inversión** — no lo que ganó, sino
lo que costó ganarlo. Las mismas ocho inversiones que la carrera de clases de activos, medidas
contra sí mismas en lugar de entre sí.

- **La curva es el punto.** En el resto de la aplicación un valor se dibuja como una longitud, y
  una longitud solo puede decir cuán profunda está el agua en ese instante. Una profundidad es una
  forma en el tiempo: el mínimo y la salida de él son dos lugares de la curva, y la distancia que
  los separa en el fotograma es el número de meses transcurridos.
- **Los dos números no suben juntos.** En los últimos diez años el fondo Nasdaq cayó un 25,52% y
  volvió a estar nivelado en seis meses; el fondo CSI 500 cayó un 56,07% y tardó ochenta y seis.
  Impreso como un solo número, el segundo parece una versión agravada del primero — y no lo es.
- **Una sola escala de profundidad para todo el tablero.** Escalar cada fila según su propio peor
  momento dibujaría el 0,2% del fondo monetario como un abismo del tamaño del 56% del CSI 500, en
  un tablero cuyo propósito entero es decir que esos dos no son comparables. Así que esa fila es
  una línea plana pegada a su línea de máximo — y **esa planicie es lo que dice**.
- **Ajustado, mensual y desde el primer mes propio de cada inversión**, por las razones que da la
  carrera de clases de activos: las distribuciones de un fondo nunca aparecen en su precio, y una
  inversión que llega en 2019 no se mide contra un máximo que no tenía.
- **Las filas siguen compitiendo.** Se ordenan por cuán por debajo de su propio máximo están — la
  más cerca de su máximo arriba — e intercambian puestos a medida que pasan los meses.
- **El oro y el fondo de materias primas seguían bajo el agua cuando se midió esto** — el tablero
  reporta ese tipo de caída como abierta, porque el periodo terminó antes de que se reparara.
- **O su propia lista.** El último grupo del menú es una lista propia: escriba un código, un
  nombre o pinyin para añadir uno, y en ella pueden mezclarse los tres mercados. Una lista para
  cuatro tableros: una acción añadida aquí también se ofrece en los otros tres; se descarga
  ajustada, exactamente como los ocho fondos, de modo que dividendos y desdoblamientos están en la
  cifra. Con menos de tres se rechaza la descarga.

No depende del ajuste de mercado: los ocho cotizan en una bolsa continental. Menos de doce meses
en el periodo se rechaza.

## Tasa de acierto

Una fila es **la proporción de entradas terminadas que ganaron** — de todos los meses en que se
pudo entrar y mantener el mismo tiempo, la parte que acabó en ganancia. Las mismas ocho inversiones
que la carrera de clases de activos y el tablero de caídas, puntuadas por si mantenerlas funcionó,
no por cuánto dieron.

- **Una entrada es suerte; ochenta y cuatro son una tasa.** Cada mes del periodo es una entrada y
  todas se mantienen el mismo tiempo, así que mantener tres años a lo largo de diez son ochenta y
  cuatro entradas por fila, no una. Comparten meses, y ahí está el punto: reducirlas a tres
  independientes dejaría una tasa con tres observaciones dentro.
- **Una entrada cuenta desde el mes en que termina.** Lo comprado en los últimos tres años del
  periodo no ha terminado, y contar una entrada sin terminar como pérdida doblaría cada fila hacia
  abajo al final por la sola razón del calendario. El tablero empieza por tanto en el primer mes en
  que una entrada podía haber terminado.
- **Una fila entra cuando han terminado seis entradas.** Una entrada es 0 % o 100 %, y cualquiera
  de esas dos cifras en un extremo de la clasificación es un extremo que no ha ganado.
- **Ajustado, mensual y desde el primer mes propio de cada inversión**, por las razones que da la
  carrera de clases de activos: las distribuciones de un fondo nunca aparecen en su precio, y un
  fondo lanzado en 2019 no tiene entradas de 2016 que ganar o perder.
- **El periodo de tenencia es la única elección nueva de este tablero.** Un año y cinco años sobre
  los mismos diez años son dos preguntas distintas con dos respuestas distintas, y las ocho filas
  se reordenan entre una y otra.
- **Las filas siguen corriendo.** Se ordenan por su tasa — la que más veces acaba en ganancia
  arriba — y se intercambian los puestos mientras pasan los meses.
- **O su propia lista.** El último grupo del menú es una lista propia: escriba un código, un
  nombre o pinyin para añadir uno, y en ella pueden mezclarse los tres mercados. Una lista para
  cuatro tableros: una acción añadida aquí también se ofrece en los otros tres; se descarga
  ajustada, exactamente como los ocho fondos, de modo que dividendos y desdoblamientos están en la
  cifra. Con menos de tres se rechaza la descarga.

Medido en los últimos diez años con una tenencia de tres años: el fondo Nasdaq acabó en ganancia
en las ochenta y cuatro entradas y el fondo de Hong Kong en el cuarenta por ciento de ellas — dos
filas que la carrera de clases de activos separa por diez años de rentabilidad total y este tablero
separa por si entrar, sencillamente, funcionó.

No depende del ajuste de mercado: las ocho cotizan en un mercado continental. Menos de doce meses
en el periodo se rechaza.

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
- Además de 3, 5 y 10 años y del tramo más largo, el rango puede ser **Personalizado**: indica una fecha inicial y una final y pulsa el botón de obtener datos. Se puede retroceder unos 35 años: la fuente entrega unos 640 días naturales por petición y el recorrido hace veinte como máximo.

## Rentabilidad de cartera

![La página completa: vista previa a la izquierda, barra de reproducción abajo, ajustes a la derecha.](media/position.png)

Una sola compra, mantenida durante años — un millón en 中国平安 en 2015, por ejemplo — animada como lo que hicieron el valor y la rentabilidad.

- Los nombres sugeridos siguen al mercado: en China, las acciones que la gente de verdad dice haber mantenido (Ping An, Moutai, CMB…); en Hong Kong, Tencent, HSBC y el Tracker Fund; en Estados Unidos, Apple, Berkshire y SPY.
- El capital inicial y el periodo de tenencia son tuyos; el periodo puede ser de tres, cinco o diez años, o hasta donde lleguen los datos (unos trece años).
- La rentabilidad se calcula sobre cierres ajustados hacia atrás — dividendos reinvertidos, sin comisiones. El ajuste hacia atrás se ancla en la salida a bolsa y acumula los dividendos hacia delante, así que los primeros años de un gran pagador nunca se vuelven negativos, como puede pasar con el ajuste hacia delante.
- El mismo rango **Personalizado** vale para la tenencia: indica dos fechas y pulsa obtener datos. Si el instrumento empezó a cotizar después de la fecha indicada, la tenencia comienza su primer día de negociación.

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

- El control de opacidad decide cuánto se usan los dos colores: al 100 % el fotograma es la pareja elegida y por debajo deja ver el degradado oscuro propio de la página. Es lo que mantiene legible una combinación clara.

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
