# Market Motion Studio

Este aplicativo transforma indicadores do mercado de ações A em vídeos verticais para o celular. Você escolhe um período, olha a prévia até que ela se leia bem e exporta um MP4. Nada mais precisa ser instalado.

## Escolher um mercado

Em Configurações escolhe-se de qual mercado o app obtém suas cotações; ações A por padrão. A mudança vale após reiniciar o app.

- **Ações A**: as sete páginas estão disponíveis.
- **Hong Kong**: a matriz de retorno e o calendário funcionam; a corrida de setores usa os quatro subíndices Hang Seng; **não há número para o mercado inteiro, então essa página fica oculta**.
- **Estados Unidos**: a matriz de retorno e o calendário funcionam; a corrida de setores usa dez ETFs setoriais SPDR; a página de volume mantém só o modo diário, porque o endpoint de minutos não serve dados americanos; **os valores estão em dólares e a página de volume do mercado fica oculta**.

## Volume financeiro do mercado

O volume financeiro de cada dia em todo o mercado: os valores dos índices compostos de Xangai e Shenzhen somados, uma barra por pregão.

- Só ficam os dias em que todos os mercados incluídos negociaram, para que o feriado de um deles não faça o total parecer ter desabado.
- Um pregão ainda em andamento é deixado de fora. Um dia inacabado contém apenas seu leilão de abertura e seria desenhado como uma barra colada ao eixo.
- Ou olhar só um segmento: cada bolsa, cada quadro principal, STAR, ChiNext. Os quadros principais são derivados do total da bolsa menos o seu quadro de crescimento; o BSE 50 continua sendo uma medida de componentes.
- Só o mercado de ações A dá um total do mercado inteiro. Com Hong Kong ou Estados Unidos a página é removida da navegação.

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

## Retorno de posição

![A página inteira: pré-visualização à esquerda, barra de reprodução abaixo, ajustes à direita.](media/position.png)

Uma única compra, mantida por anos — um milhão em 中国平安 em 2015, por exemplo — animada como o que o valor e o retorno fizeram.

- Os nomes sugeridos seguem o mercado: na China, as ações que as pessoas de fato dizem ter mantido (Ping An, Moutai, CMB…); em Hong Kong, Tencent, HSBC e o Tracker Fund; nos Estados Unidos, Apple, Berkshire e SPY.
- O capital inicial e o período de posição são seus; o período pode ser de três, cinco ou dez anos, ou até onde os dados alcançam (cerca de treze anos).
- O retorno é calculado sobre fechamentos ajustados retroativamente — dividendos reinvestidos, sem taxas. O ajuste retroativo se ancora na abertura de capital e acumula os dividendos para frente, então os primeiros anos de um bom pagador nunca ficam negativos, como pode ocorrer no ajuste para frente.

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
