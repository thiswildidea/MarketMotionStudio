# Market Motion Studio

Este aplicativo transforma indicadores do mercado de ações A em vídeos verticais para o celular. Você escolhe um período, olha a prévia até que ela se leia bem e exporta um MP4. Nada mais precisa ser instalado.

## Escolher um mercado

Em Configurações escolhe-se de qual mercado o app obtém suas cotações; ações A por padrão. A mudança vale após reiniciar o app.

- **Ações A**: as oito páginas estão disponíveis.
- **Hong Kong**: a matriz de retorno e o calendário funcionam; a corrida de setores usa os quatro subíndices Hang Seng; **não há número para o mercado inteiro, então essa página fica oculta**.
- **Estados Unidos**: a matriz de retorno e o calendário funcionam; a corrida de setores usa dez ETFs setoriais SPDR; a página de volume mantém só o modo diário, porque o endpoint de minutos não serve dados americanos; **os valores estão em dólares e a página de volume do mercado fica oculta**.



## Navegando entre as páginas

Os dois botões à esquerda da barra de título voltam e avançam pelas páginas visitadas, como faz um navegador: **Alt+Seta para a esquerda** e **Alt+Seta para a direita**, ou os botões laterais do mouse.

- A página é mantida como você a deixou, portanto voltar a ela traz de volta o período e a prévia no estado em que estavam, e não uma página recém-aberta.
- Como em um navegador, escolher uma nova página limpa o que estava à frente.
- Funcionam também com o painel de navegação recolhido, que é quando a prévia mais precisa de largura.

## Volume financeiro do mercado

O volume financeiro de cada dia em todo o mercado: os valores dos índices compostos de Xangai e Shenzhen somados, uma barra por pregão.

- Só ficam os dias em que todos os mercados incluídos negociaram, para que o feriado de um deles não faça o total parecer ter desabado.
- Um pregão ainda em andamento é deixado de fora. Um dia inacabado contém apenas seu leilão de abertura e seria desenhado como uma barra colada ao eixo.
- Ou olhar só um segmento: cada bolsa, cada quadro principal, STAR, ChiNext. Os quadros principais são derivados do total da bolsa menos o seu quadro de crescimento; o BSE 50 continua sendo uma medida de componentes.
- Só o mercado de ações A dá um total do mercado inteiro. Com Hong Kong ou Estados Unidos a página é removida da navegação.

## Candlestick

Os candles de um instrumento: diários, semanais ou mensais, desenhados de quatro formas, com médias e volume abaixo.

- **Intervalo** decide quanto tempo de mercado um candle cobre: um dia, uma semana ou um mês. Mudá-lo busca os dados de novo, porque na fonte as três são séries distintas.
- **Tipo de desenho** decide como os mesmos quatro preços são desenhados: candles, barras OHLC, linha de fechamento ou área de fechamento. Trocar de um para outro não busca nada.
- **Animação** é a chegada dos candles um após o outro até traçar todo o período, ou uma janela fixa que avança. A segunda é o que mantém o candle largo o bastante para ser lido num período longo, e essa largura é o ajuste **Janela**.
- As médias móveis MA5, MA10 e MA20 podem ser sobrepostas aos candles; o painel de volume abaixo pode ser desligado, e o painel de preço recupera o espaço.
- Uma semana ou um mês ainda em curso fica de fora. Um candle feito de três dias não é uma semana.
- Todo mercado é lido na sua série ajustada, então um dia de desdobramento não é desenhado como queda, e um dividendo tampouco.

## Volume e giro

O volume de uma ação diante da sua taxa de giro, em dois painéis sobrepostos.

- De um pregão para outro, volume e taxa de giro são proporcionais, então os dois painéis têm quase a mesma forma. Dentro de um dia, o volume por minuto e o giro acumulado ficam realmente diferentes, e essa é a imagem mais interessante.
- A fonte intradiária guarda apenas os últimos pregões, então esse modo oferece esses e não uma data qualquer.
- Os dados por minuto são servidos apenas para ações A e Hong Kong; nos Estados Unidos esse modo não é oferecido.

## Corrida de setores

![A página inteira: pré-visualização à esquerda, barra de reprodução abaixo, ajustes à direita.](media/sector-race.png)

Um conjunto de setores ou ações desenhado como barras horizontais que se ultrapassam, e a ordem muda até o último quadro.

- Duas medidas: a variação do período em % e seu volume em centenas de milhões de yuans. Trocar a medida só recoloriu os mesmos dados; não busca de novo.
- Quatro listas: setores Shenwan de nível 1, temas em alta, personalizada (marcar caixas) e ações individuais (adicionar pela busca). A lista personalizada começa preenchida com os setores Shenwan de nível 1.
- As listas integradas seguem o mercado: setores Shenwan de nível 1 e temas em alta para ações A, os quatro subíndices Hang Seng para Hong Kong, dez ETFs setoriais SPDR para os Estados Unidos. As listas personalizada e de ações existem em todos os mercados.
- O intervalo pode ser de 1, 3, 6 ou 12 meses, ou datas de início e fim personalizadas.
- Uma lista tem um mínimo e um máximo de itens — poucas barras não é uma corrida, muitas se amontoam.




## Corrida de valor de mercado

As quinze maiores companhias de um mercado como barras horizontais ordenadas por valor de
mercado, com a ordem mudando até o último quadro. Amostragem mensal.

- **A classificação é refeita a cada período.** A busca pergunta primeiro à fonte a classificação
  atual por valor de mercado, toma as duzentas primeiras como grupo e acrescenta os pesos-pesados
  que estavam nela e saíram; cada período mostra então as quinze maiores desse grupo. Os membros
  entram e saem de verdade — 2016 era petróleo e bancos, 2026 somou 茅台, 宁德时代 e 工业富联. Um
  grupo escrito no programa deixou passar uma companhia que abriu capital e foi direto ao topo;
  agora o grupo é perguntado em vez de lembrado.
- **Um valor de mercado passado é calculado**: o valor de hoje vezes a razão de preços ajustada do
  período. Bonificações e desdobramentos se cancelam na série ajustada; os dividendos não — são
  reinvestidos, então o valor passado de quem paga muito sai baixo. Só o número do último quadro
  vem direto da fonte.
- **Uma companhia que ainda não tinha aberto capital cresce do zero**: os papéis que estrearam em
  2018 sobem da linha de base no dia em que entraram, sem ocupar lugar antes.
- **O intervalo é o mês, não o dia**: cento e vinte períodos em dez anos, doze em um, e o cabeçalho
  do quadro conta meses. Uma classificação por valor de mercado é uma grandeza lenta, e uma amostra
  mensal obtém todo o histórico em uma requisição.
- **Cada mercado tem os seus quinze.** Os três nunca se misturam: o dinheiro deles não é o mesmo.
  Hong Kong e Nova York mantêm um grupo fixo, porque nenhuma classificação acessível a este
  aplicativo os atende.





## Prêmio A/H

Quanto mais cara é a cotação continental de uma companhia do que a de Hong Kong, para as
companhias cotadas dos dois lados — mês a mês, em barras que se ultrapassam.

- **Prêmio = preço A ÷ (preço H × HKD/CNY) − 1.** Nada aqui é calculado: as duas pontas são preços
  realmente pagos no mesmo instante, e é por isso que esta é a única página que busca preços **sem
  ajuste**. Uma série ajustada para trás infla os preços recentes, e dois mercados ajustados
  separadamente não são comparáveis — a ação A do ICBC aparece a 8,28 na tela e a série ajustada
  informa 13,34, transformando um prêmio de +26% em +245%.
- **A mesma diferença se escreve nos dois sentidos.** Esta página dá A contra H, a forma usual:
  +194% significa que a ação continental custa quase o triplo da de Hong Kong. Alguns serviços
  mostram o mesmo número ao contrário (溢价(H/A)) e dão −66% para 新华制药 no mesmo dia. É o mesmo
  fato (1 ÷ (1 − 0,66) − 1 = 1,94): não é outro preço nem erro de cálculo.
- **O quadro desenha as quinze mais caras**, então as barras crescem para a direita — até a
  décima quinta passava de vinte por cento. Só duas das sessenta e nove vão ao contrário, com a ação
  H acima da A, e ambas ficam no fim da lista, fora do quadro.
- **Quanto maior o período, menos companhias entram.** São sessenta e nove duplas cotações
  conhecidas como candidatas, mas só é desenhado o par cujas duas pontas cobrem todo o período: uma
  cotação em Hong Kong com menos de dois anos fica de fora.
- **Amostragem mensal.** O «mais longo» tem cerca de nove anos, e o limite é a série do câmbio, que
  só chega a 2016. As três pontas fecham o mês em dias diferentes, então agrupa-se por mês
  calendário e toma-se o último preço do mês, em vez de cruzar pela data.
- **A lista é interna.** Nenhuma das duas fontes responde «quais cotações continentais também têm
  uma em Hong Kong». Em compensação, ela é conferível: cada par foi relido da fonte em 2026-10-02, e
  海通证券 foi o que essa conferência removeu (ações H deslistadas após a fusão no 国泰海通).

## Dias extremos

Um instrumento e os dias em que ele mais se moveu — barras horizontais ordenadas por
tamanho. **As linhas deste quadro são dias, não empresas**, o que nenhuma outra página aqui faz: o
valor de uma linha é quanto aquele dia se moveu em relação ao fechamento do dia anterior e, depois
que o dia passa, o valor nunca mais muda.

- **O movimento é a variação do fechamento ajustado.** Ajustado, porque um dia de desconto de
  dividendo não é um crash: naquela manhã o preço cai o valor do dividendo, e uma série sem ajuste
  colocaria esse dia no topo das maiores quedas da história, quando ninguém perdeu nada.
- **Ordenado por tamanho, não por sinal.** −7,7 % e +8,1 % são movimentos do mesmo tamanho e por
  isso ficam lado a lado; ordenar pelo valor com sinal poria cada queda abaixo de cada alta. As
  barras crescem para os dois lados: **alta para a direita, em vermelho; queda para a esquerda, em
  verde**.
- **Um dia só entra na classificação quando acontece.** Os vinte e quatro maiores movimentos do
  período são os candidatos e o quadro desenha os quinze maiores deles; um dia não participa até
  que sua data chegue, então o quadro se preenche com os anos em vez de começar cheio.
- **Há um único instrumento, um dos índices amplos do mercado atual** (no mercado A: o composto de
  Xangai, o componente de Shenzhen, o CSI 300 e assim por diante). Mudar de mercado troca toda a
  lista; mudar o instrumento ou o período só salva uma preferência — nada é buscado até apertar 取数.
- **O período mais longo é de cerca de trinta e cinco anos**, que é o limite da fonte: um pedido
  traz cerca de 640 barras diárias e o retrocesso faz no máximo vinte. Um período com menos de
  sessenta dias de negociação é recusado — o maior dia de um mês tranquilo não é um fato que mereça
  um quadro.
- **A data no topo do quadro é o eixo do tempo** e a barra abaixo é o progresso. A linha de
  cabeçalho traz o período, o número de dias de negociação e o de dias candidatos.

## Corredores de câmbio

Uma linha por par, e **a linha é o corredor em si**: uma ponta é o nível mais baixo que o par
teve no período escolhido, a outra o mais alto, e o marcador é a cotação de hoje. Este quadro não é
como os outros — nos outros o comprimento de uma barra diz *quanto*, aqui a linha ocupa toda a
largura em cada quadro, e o que se move é o marcador, junto com o corredor.

- **O corredor se alarga.** Suas paredes são a mínima e a máxima **até agora**, não as de todo o
  período. Um mês que vai além de todos os anteriores empurra uma das duas para fora, e um par a
  100% está no mais caro que já esteve — não em um limite.
- **Cada par é medido contra a própria faixa.** 157,92 em USD/JPY e 1,1245 em EUR/USD não são dois
  pontos de uma mesma escala; é a normalização que permite que seis pares caibam num quadro. O preço
  é que um corredor estreito e um largo se parecem, e por isso os dois extremos são impressos sob
  cada linha.
- **Velas mensais, sem ajuste.** Uma moeda não tem dividendo nem desdobramento a ajustar, e a página
  toma o mesmo caminho bruto na fonte que a página A+H.
- **A cobertura difere, e por isso há duas listas**: USD/CNY chega a 2005, os outros cinco pares do
  renminbi a 2016; os principais cruzamentos começam todos em 2005-07 e trazem 325 meses. Num quadro
  só, ler-se-ia quando a fonte começou a cotar cada par.
- **A configuração de mercado não se aplica aqui**: um par de moedas não pertence a nenhuma bolsa, e
  o quadro é o mesmo seja qual for o mercado em vigor.
- O período mais longo é de cerca de vinte anos, a cobertura mensal da fonte; menos de doze meses é
  recusado — são algumas semanas de movimento, não um corredor.

## Corrida de índices

Uma linha por índice, e a linha é **o quanto aquele índice avançou desde o seu próprio primeiro
mês no período** — não o seu nível. 3.800 no Shanghai Composite e 5.700 no S&P 500 não são dois pontos
de uma mesma escala: desenhar níveis seria um quadro sobre onde cada índice começou a contar.

- **Um índice que chega tarde não está no quadro até chegar.** O S&P chega a 1950, o Dow apenas a
  2009, e o índice Hang Seng Tech começa em 2020. Ele está ausente, não estacionado em 0,00% — aí se
  colocaria acima de todo índice que já caiu e se leria como um mercado em que nada aconteceu.
- **Velas mensais, sem ajuste.** Um índice não paga dividendo, mas a razão é a outra: um ajuste
  rebaseia uma série, e duas séries rebaseadas lado a lado não são comparáveis. A página toma o mesmo
  caminho bruto na fonte que a página A+H.
- **A configuração de mercado não governa esta página**: ela lê três mercados ao mesmo tempo, e mudar
  o mercado não a muda. Pode-se escolher as seis do continente, as três de Hong Kong, as três de Nova
  York ou as doze.
- O período mais longo é limitado pelo teto mensal da fonte — 430 velas, cerca de trinta e cinco anos;
  menos de doze meses é recusado: isso é uma corrida curta, não uma de fundo.

## Classes de ativos

Uma linha por classe de ativos, e a linha é **o que a manutenção rendeu** — não a cotação. Todas as
oito são fundos listados em uma bolsa continental, comprados com o mesmo dinheiro, então podem ser
comparadas diretamente.

- **Os dividendos são reintegrados, e também os desdobramentos.** Um título e um fundo de mercado
  monetário pagam quase inteiramente em renda: o preço do ETF de mercado monetário foi de 100,161 a
  100,901 em treze anos, o que sem ajuste é +0,0% — e desenharia no fim do quadro a única linha daqui
  que nunca caiu. Um fundo que desdobrou cotas é ainda mais claro: o ETF Nasdaq dá +136% sem ajuste,
  enquanto o índice que ele segue subiu seis vezes na mesma década.
- **Deliberadamente o oposto da corrida de índices.** Um índice não paga dividendos, então aquela
  página fica como está; um fundo paga, então esta precisa ser ajustada. Os dois caminhos não se
  misturam.
- **As duas linhas estrangeiras carregam o câmbio.** Os ETFs de Nasdaq e Hang Seng são cotados em
  yuan, então a moeda já está dentro — que é o que um detentor continental realmente recebeu.
- **Os inícios diferem.** A linha mais antiga começa em 2012 e o fundo de commodities apenas em
  2019. Uma linha que ainda não entrou está ausente, não em 0,00%.
- **A configuração de mercado não rege esta página**: todas as oito são listadas no continente.
  Menos de doze meses é recusado.

## Quedas

Uma linha é **a distância entre um ativo e sua própria máxima** — não o que ele rendeu, mas o que
custou para render. Os mesmos oito ativos da corrida de classes de ativos, medidos contra si mesmos
em vez de entre si.

- **A curva é o ponto.** Em todo o resto deste aplicativo um valor é desenhado como um
  comprimento, e um comprimento só pode dizer quão profunda está a água naquele instante. Uma
  profundidade é uma forma no tempo: o fundo e a saída dele são dois lugares na curva, e a
  distância que os separa no quadro é o número de meses decorridos.
- **Os dois números não sobem juntos.** Nos últimos dez anos o fundo Nasdaq caiu 25,52% e voltou ao
  nível em seis meses; o fundo CSI 500 caiu 56,07% e levou oitenta e seis. Impresso como um único
  número, o segundo parece uma versão agravada do primeiro — e não é.
- **Uma única escala de profundidade para todo o quadro.** Escalar cada linha pelo seu próprio pior
  momento desenharia os 0,2% do fundo de mercado monetário como um abismo do tamanho dos 56% do CSI
  500, num quadro cujo sentido inteiro é dizer que os dois não são comparáveis. Por isso essa
  linha é uma linha reta colada à sua linha de máxima — e **essa retidão é o que ela diz**.
- **Ajustado, mensal e a partir do primeiro mês próprio de cada ativo**, pelas razões que a corrida
  de classes de ativos dá: as distribuições de um fundo nunca aparecem no seu preço, e um ativo que
  chega em 2019 não é medido contra uma máxima que não tinha.
- **As linhas continuam correndo.** São ordenadas por quão abaixo da própria máxima estão — a mais
  perto da própria máxima no topo — e trocam de lugar enquanto os meses passam.
- **Ouro e o fundo de commodities ainda estavam debaixo d'água quando isto foi medido** — o quadro
  reporta esse tipo de queda como aberta, porque o período terminou antes de ser reparada.

Não depende da configuração de mercado: todos os oito são cotados numa bolsa continental. Menos de
doze meses no período é recusado.

## Matriz de retorno

![A página inteira: pré-visualização à esquerda, barra de reprodução abaixo, ajustes à direita.](media/monthly-matrix.png)

Barras mensais dispostas em uma grade: o modo ano mostra a sazonalidade de um instrumento ao longo de uma década; o modo comparação coloca vários instrumentos lado a lado para mostrar a rotação.

- Modo ano: escolha um instrumento (busca ou um índice amplo predefinido); o intervalo é de 1 a 10 anos ou todos. Uma requisição devolve uma década de barras mensais.
- Modo comparação: de 2 a 14 instrumentos de uma lista (setores de nível 1 / temas / índices amplos / personalizada / ações) lado a lado, de 6 a 48 meses.
- A grade acende célula por célula em ordem temporal; ao final mostra o melhor e o pior mês do intervalo, entre outras estatísticas.
- Os dados mensais cobrem uma década de uma vez, então não há o limite diário de dias — mas muitos instrumentos saem do enquadramento.

## Calendário de altas e baixas

![A página inteira: pré-visualização à esquerda, barra de reprodução abaixo, ajustes à direita.](media/gain-calendar.png)

Qualquer ação ou índice da bolsa chinesa, seu alta ou baixa diária disposta em células de calendário por mês: vermelho na alta, verde na baixa.

- Busque por código, nome ou pinyin; as predefinições são índices amplos. Somente instrumentos do mercado selecionado.
- A lista de favoritos é compartilhada com a página de ações do app: um favorito adicionado em qualquer uma das duas aparece em ambas.
- O intervalo é de 1, 3, 6 ou 12 meses, ou personalizado; um instrumento sozinho ainda está sujeito ao limite de cerca de 640 dias de calendário.
- As estatísticas finais dão a contagem de pregões em alta e em baixa.

## Plano DCA

![A página inteira: pré-visualização à esquerda, barra de reprodução abaixo, ajustes à direita.](media/dca-plan.png)

Comprar um ativo com valor e frequência fixos — todo dia de pregão, toda semana ou todo mês — e ver em animação o que a disciplina virou.

- Os ativos de um toque seguem o mercado: ETFs amplos e de ouro nas ações A, os fundos índice de Hong Kong, SPY, QQQ e GLD nos Estados Unidos.
- Valor e frequência você define; o período é de três, cinco ou dez anos, ou até onde os dados alcançam (uns treze anos).
- O retorno é calculado sobre fechamentos ajustados retroativamente, sem taxas. O resultado descreve a série de preços, não uma conta que alguém poderia ter executado.
- Além de 3, 5 e 10 anos e do período mais longo, o intervalo pode ser **Personalizado**: informe a data inicial e a final e pressione o botão de buscar dados. Dá para voltar cerca de 35 anos — a fonte entrega cerca de 640 dias corridos por requisição e a varredura faz no máximo vinte.

## Retorno de posição

![A página inteira: pré-visualização à esquerda, barra de reprodução abaixo, ajustes à direita.](media/position.png)

Uma única compra, mantida por anos — um milhão em 中国平安 em 2015, por exemplo — animada como o que o valor e o retorno fizeram.

- Os nomes sugeridos seguem o mercado: na China, as ações que as pessoas de fato dizem ter mantido (Ping An, Moutai, CMB…); em Hong Kong, Tencent, HSBC e o Tracker Fund; nos Estados Unidos, Apple, Berkshire e SPY.
- O capital inicial e o período de posição são seus; o período pode ser de três, cinco ou dez anos, ou até onde os dados alcançam (cerca de treze anos).
- O retorno é calculado sobre fechamentos ajustados retroativamente — dividendos reinvestidos, sem taxas. O ajuste retroativo se ancora na abertura de capital e acumula os dividendos para frente, então os primeiros anos de um bom pagador nunca ficam negativos, como pode ocorrer no ajuste para frente.
- O mesmo intervalo **Personalizado** vale para a posição: informe duas datas e pressione buscar dados. Se o ativo passou a ser negociado depois da data informada, a posição começa no seu primeiro dia de negociação.

## Vídeo

O quadro é sempre 9:16. Todo o resto é você que decide.

- A duração muda o ritmo, não corta a animação: a abertura, o crescimento das barras e as estatísticas finais são redistribuídos ao longo do tamanho escolhido.
- As margens são anotadas contra um quadro de 1080×1920 e escalonadas para a resolução de exportação, então um layout ajustado uma vez vale em qualquer tamanho. A margem esquerda também decide onde caem os rótulos do eixo: pequena demais, e os números saem do quadro.
- As guias de área segura delimitam o que um aplicativo de celular cobre com a própria interface. São desenhadas na prévia e nunca em um arquivo.

## Para onde vão os vídeos

As exportações são gravadas em uma pasta que você escolhe por um seletor. Enquanto nenhuma tiver sido escolhida, a primeira exportação pergunta e depois lembra; as configurações permitem trocar ou esquecer.

## Imagem de fundo

A página de configurações pode colocar uma imagem atrás da janela, escurecida. Os cartões e painéis permanecem opacos e o painel de navegação deixa passar só um pouco — a imagem aparece principalmente ao redor deles. A prévia do vídeo tem seu próprio fundo sólido e não é afetada.

- Escolha uma imagem do computador ou use diretamente um dos planos de fundo e imagens da tela de bloqueio que acompanham o Windows.
- A imagem escolhida é copiada para a pasta do aplicativo; mover ou excluir o original não afeta o fundo.
- O controle de intensidade da máscara define o quanto a imagem é escurecida, de 30% a 95%.
- Nenhuma imagem é mostrada enquanto o alto contraste estiver ativado.
## Fundo da animação

Na página de configurações você pode mudar sobre o que a animação é desenhada: o gradiente padrão, duas cores suas ou uma imagem. Vale para a pré-visualização, o vídeo exportado e a imagem de capa: os três são desenhados pelo mesmo renderizador, então não existe "bonito na pré-visualização e diferente no arquivo".

- Ao escolher cores, você indica um tom superior e um inferior, e o quadro passa de um para o outro. Prefira escuros: todos os tons de texto são claros, e um fundo claro dificulta a leitura dos números.

- O controle de opacidade define quanto das duas cores é usado: em 100% o quadro é o par escolhido e abaixo disso o degradê escuro da própria página aparece por baixo. É isso que mantém um par claro legível.

- Escolher uma imagem funciona como no fundo da janela: uma do computador ou um papel de parede que já vem com o Windows. A escolhida é copiada para a pasta do aplicativo.

- A imagem preenche o quadro e o excesso é cortado, então as proporções nunca são esticadas.

- O controle de escurecimento define o quanto a imagem volta para o fundo próprio da página, de 20% a 95%.

## Os dados, e o que eles não vão dizer

As cotações vêm dos endpoints públicos da Tencent Finance, e o quadro sempre cita a fonte. Estes vídeos descrevem o que já foi negociado. Servem apenas para referência e não são recomendação de investimento.

- Os valores são convertidos para centenas de milhões de yuans, e o volume muda para uma unidade maior assim que os números pedem, para que o eixo continue legível.
- Os valores são convertidos em centenas de milhões — de yuans no continente e em Hong Kong, de dólares nos Estados Unidos. Cada mercado mantém sua própria moeda.
- Um período maior que cerca de 640 dias de calendário é recusado em vez de truncado em silêncio, porque isso é tudo o que uma requisição à fonte devolve.

## Atualização

Quando a Microsoft Store tem uma versão mais nova, aparece um botão **Atualizar** ao lado de Configurações no painel de navegação; um clique instala.

- Ele só aparece quando a Store realmente tem uma versão mais nova. Uma compilação de desenvolvimento ou instalada por fora nunca o vê, e isso é esperado.
- O aplicativo fecha durante a instalação e abre de novo na nova versão, e o botão some. Se uma exportação estiver rodando, ele pergunta antes.
- Se não conseguir instalar, ele diz o motivo — só por Wi-Fi, bateria fraca — e a atualização também pode ser instalada pela Microsoft Store.

## Algo errado?

Escreva para gaqo@outlook.com dizendo o que você estava fazendo e o que esperava em vez disso. O número da versão está na página de configurações.
