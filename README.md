# Emdec ⇒ GTFS
Esta aplicação extrai informações de rotas de onibus do [site da emdec](http://www.emdec.com.br/ABusInf/consultarlinha.asp), e as apresenta em 2 formatos: GTFS e JSON

* O formato JSON não segue nenhum padrão existente, mas representa de forma quase direta as informações extraídas da EMDEC.
* O Formato GTFS segue uma [especifícação](https://developers.google.com/transit/gtfs/reference?hl=en) desenvolvida pelo Google e outros colaboradores. Em particular, este formato pode ser utilizado diretamente pelo [Google Maps](https://maps.google.com), [Nokia Maps](https://www.here.com), [Bing Maps](https://www.bing.com/maps), [Moovit](http://www.moovitapp.com/) e outros para cálculo de rotas.

![Visualização das rotas](http://i.imgur.com/CS6NjkU.jpg "Visualização das rotas, gerada pela Mobilibus")


## Observações / Limitações

* A maioria das rotas são apresentadas como 2 percursos distintos, um de ida e um de volta (e.g., [253](http://www.emdec.com.br/ABusInf/detalhelinha.asp?TpDiaID=0&CdPjOID=3000)). Essas estão perfeitas.

  Infelizmente diversas outras rotas são apresentadas como um único percursos, mas possuem letreiros e horários distintos para a ida e a volta (e.g., [332](http://www.emdec.com.br/ABusInf/detalhelinha.asp?TpDiaID=0&CdPjOID=3125)). Nesses casos, eu infelizmente não possuo informação suficiente para determinar onde começa a "volta". Seria importante descobrir essa informação para informar o horário desta parada e atualizar o letreiro.

* É fácil obter o trajeto e a lista de paradas a partir do site da emdec, mas não há informação sobre a ordem das paradas.

  O programa determina a sequência associando cada parada ao ponto mais próximo no trajeto. Quando há ambiguidade (Ida-e-volta pela mesma rua, rota com ciclos, etc - E.g., [332](http://www.portalinterbuss.com.br/campinas/linhas/332)), a ambiguidade é resolvida de forma que a parada fique "à direita" do onibus.

  Por inspeção visual o resultado parece bastante satisfatório, mas existem alguns erros nas situações de ambiguidade.

* Optei por gerar o arquivo GTFS usando o modo de "frequências", no qual o usuário poderá ver "A cada X minutos".

  Isso é especialmente importante porque não temos informação precisa de horários, exceto na primeira parada.

* Os nomes das paradas de onibus são obtidos por [Geocodificação reversa](https://developers.google.com/maps/documentation/geocoding/?hl=en#ReverseGeocoding), e não são tão amigáveis quanto seria desejável.

  Por exemplo, "Terminal Barão Geraldo" é mostrado como "Avenida Albino José Barbosa de Oliveira, 893"

* Atualmente não uso o suporte para "terminais" do formato GTFS

## Uso

* [`/route/list`](http://emdec.paulo.costa.nom.br/route/list): JSON com número e nome de todas as linhas da EMDEC
* `/route/<codigo>/json`: Arquivo JSON contendo informação sobre as linhas identificada pelo código. E.g.:
 * [`/route/332.json`](http://emdec.paulo.costa.nom.br/route/332.json): Informações sobre a linha `332`
 * [`/route/116,224,332.json`](http://emdec.paulo.costa.nom.br/route/116,224,332.json): Informações sobre a linhas `116`, `224` e `332`
 * [`/route/all.json`](http://emdec.paulo.costa.nom.br/route/all.json): Informações sobre todas as linhas
* `/route/<codigo>/gtfs`: Arquivo GTFS contendo informação sobre as linhas identificada pelo código. E.g.:
 * [`/route/332.gtfs`](http://emdec.paulo.costa.nom.br/route/332.gtfs): Informações sobre a linha `332`
 * [`/route/116,224,332.gtfs`](http://emdec.paulo.costa.nom.br/route/116,224,332.gtfs): Informações sobre a linhas `116`, `224` e `332`
 * [`/route/all.gtfs`](http://emdec.paulo.costa.nom.br/route/all.gtfs): Informações sobre todas as linhas

Exemplo de uso da API JSON: http://jsfiddle.net/v2w1vjLf/

## Licença

Faça o que quiser, com o código ou com os dados.
