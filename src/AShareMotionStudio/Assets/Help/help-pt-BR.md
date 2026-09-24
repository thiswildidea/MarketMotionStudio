# AShare Motion Studio

Este aplicativo transforma indicadores do mercado de ações A em vídeos verticais para o celular. Você escolhe um período, olha a prévia até que ela se leia bem e exporta um MP4. Nada mais precisa ser instalado.

## Volume financeiro do mercado

O volume financeiro de cada dia em todo o mercado: os valores dos índices compostos de Xangai e Shenzhen somados, uma barra por pregão.

- Só ficam os dias em que todos os mercados incluídos negociaram, para que o feriado de um deles não faça o total parecer ter desabado.
- Um pregão ainda em andamento é deixado de fora. Um dia inacabado contém apenas seu leilão de abertura e seria desenhado como uma barra colada ao eixo.
- A opção de Pequim acrescenta o índice BSE 50, que cobre apenas suas componentes e não a bolsa inteira. É outra medida, e menor.

## Volume de uma ação

O volume de uma ação diante da sua taxa de giro, em dois painéis sobrepostos.

- De um pregão para outro, volume e taxa de giro são proporcionais, então os dois painéis têm quase a mesma forma. Dentro de um dia, o volume por minuto e o giro acumulado ficam realmente diferentes, e essa é a imagem mais interessante.
- A fonte intradiária guarda apenas os últimos pregões, então esse modo oferece esses e não uma data qualquer.

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
