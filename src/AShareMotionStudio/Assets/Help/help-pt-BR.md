# AShare Motion Studio

Este aplicativo transforma indicadores do mercado de ações A em vídeos verticais para o celular. Você escolhe um período, olha a prévia até que ela se leia bem e exporta um MP4. Nada mais precisa ser instalado.

## Volume financeiro do mercado

O volume financeiro de cada dia em todo o mercado: os valores dos índices compostos de Xangai e Shenzhen somados, uma barra por pregão.

- Só ficam os dias em que todos os mercados incluídos negociaram, para que o feriado de um deles não faça o total parecer ter desabado.
- Um pregão ainda em andamento é deixado de fora. Um dia inacabado contém apenas seu leilão de abertura e seria desenhado como uma barra colada ao eixo.
- Ou olhar só um segmento: cada bolsa, cada quadro principal, STAR, ChiNext. Os quadros principais são derivados do total da bolsa menos o seu quadro de crescimento; o BSE 50 continua sendo uma medida de componentes.

## Volume de uma ação

O volume de uma ação diante da sua taxa de giro, em dois painéis sobrepostos.

- De um pregão para outro, volume e taxa de giro são proporcionais, então os dois painéis têm quase a mesma forma. Dentro de um dia, o volume por minuto e o giro acumulado ficam realmente diferentes, e essa é a imagem mais interessante.
- A fonte intradiária guarda apenas os últimos pregões, então esse modo oferece esses e não uma data qualquer.

## Corrida de setores

Um conjunto de setores ou ações desenhado como barras horizontais que se ultrapassam, e a ordem muda até o último quadro.

- Duas medidas: a variação do período em % e seu volume em centenas de milhões de yuans. Trocar a medida só recoloriu os mesmos dados; não busca de novo.
- Quatro listas: setores Shenwan de nível 1, temas em alta, personalizada (marcar caixas) e ações individuais (adicionar pela busca). A lista personalizada começa preenchida com os setores Shenwan de nível 1.
- O intervalo pode ser de 1, 3, 6 ou 12 meses, ou datas de início e fim personalizadas.
- Uma lista tem um mínimo e um máximo de itens — poucas barras não é uma corrida, muitas se amontoam.

## Matriz mensal

Barras mensais dispostas em uma grade: o modo ano mostra a sazonalidade de um instrumento ao longo de uma década; o modo comparação coloca vários instrumentos lado a lado para mostrar a rotação.

- Modo ano: escolha um instrumento (busca ou um índice amplo predefinido); o intervalo é de 1 a 10 anos ou todos. Uma requisição devolve uma década de barras mensais.
- Modo comparação: de 2 a 14 instrumentos de uma lista (setores de nível 1 / temas / índices amplos / personalizada / ações) lado a lado, de 6 a 48 meses.
- A grade acende célula por célula em ordem temporal; ao final mostra o melhor e o pior mês do intervalo, entre outras estatísticas.
- Os dados mensais cobrem uma década de uma vez, então não há o limite diário de dias — mas muitos instrumentos saem do enquadramento.

## Calendário de altas e baixas

Qualquer ação ou índice da bolsa chinesa, seu alta ou baixa diária disposta em células de calendário por mês: vermelho na alta, verde na baixa.

- Busque por código, nome ou pinyin; as predefinições são índices amplos. Somente ações e índices da bolsa chinesa.
- A lista de favoritos é compartilhada com a página de ações do app: um favorito adicionado em qualquer uma das duas aparece em ambas.
- O intervalo é de 1, 3, 6 ou 12 meses, ou personalizado; um instrumento sozinho ainda está sujeito ao limite de cerca de 640 dias de calendário.
- As estatísticas finais dão a contagem de pregões em alta e em baixa.

## Vídeo

O quadro é sempre 9:16. Todo o resto é você que decide.

- A duração muda o ritmo, não corta a animação: a abertura, o crescimento das barras e as estatísticas finais são redistribuídos ao longo do tamanho escolhido.
- As margens são anotadas contra um quadro de 1080×1920 e escalonadas para a resolução de exportação, então um layout ajustado uma vez vale em qualquer tamanho. A margem esquerda também decide onde caem os rótulos do eixo: pequena demais, e os números saem do quadro.
- As guias de área segura delimitam o que um aplicativo de celular cobre com a própria interface. São desenhadas na prévia e nunca em um arquivo.

## Para onde vão os vídeos

As exportações são gravadas em uma pasta que você escolhe por um seletor. Enquanto nenhuma tiver sido escolhida, a primeira exportação pergunta e depois lembra; as configurações permitem trocar ou esquecer.

## Os dados, e o que eles não vão dizer

As cotações vêm dos endpoints públicos da Tencent Finance, e o quadro sempre cita a fonte. Estes vídeos descrevem o que já foi negociado. Servem apenas para referência e não são recomendação de investimento.

- Os valores são convertidos para centenas de milhões de yuans, e o volume muda para uma unidade maior assim que os números pedem, para que o eixo continue legível.
- Um período maior que cerca de 640 dias de calendário é recusado em vez de truncado em silêncio, porque isso é tudo o que uma requisição à fonte devolve.

## Algo errado?

Escreva para gaqo@outlook.com dizendo o que você estava fazendo e o que esperava em vez disso. O número da versão está na página de configurações.
