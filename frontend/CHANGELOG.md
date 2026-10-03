# Changelog

## Não lançado

- Menu Banco de dados com exportação, importação condicionada à API e confirmação antes de substituir os dados.

- Diferencia tags selecionadas com primary e mantém as sugestões abertas ao escolher uma tag, ocultando apenas as selecionadas.

- Exibe tags como badges arredondadas e busca no backend as cinco mais usadas, com filtro a partir de três caracteres.

- Move as tags para o último campo do item e padroniza o espaçamento da revisão com contêineres flex e gap.

- Alinha o link Relatórios ao padrão das opções do menu superior.
- Corrige o envio manual do link da NFC-e para consultar a API sem recarregar a página.

- Área de relatórios mensais com resumo, categorias, tags e consulta dos itens de cada grupo.
- Seleção e criação de múltiplas tags nos itens, com aplicação em lote pelo cabeçalho.
- Opção de considerar a nota no mês seguinte, disponível também após a importação.

- Adiciona tipos de produto por unidade, a granel e com variações de peso ou volume.
- Ajusta a revisão para confirmar quantidade inteira ou decimal e selecionar variações em modal.
- Converte automaticamente KG/G e L/ML na sugestão de quantidade a granel.
- Adiciona o menu Cadastros com telas de categorias, marcas, produtos, variações e estabelecimentos, sem exclusão.
- Permite criar uma variação diretamente no modal de pesquisa durante a revisão.

- Substitui os selects de produto e marca por modais com busca instantânea e criação.
- Inicia a busca de produto com a descrição original do item da nota.
- Centraliza os modais no espaço visível do celular durante o uso do teclado.
- Formata a busca inicial do produto e adiciona busca e criação de categorias em modal.
- Abre a busca de marca vazia, mantendo a descrição fiscal apenas no título.
- Adiciona ao produto a opção de não solicitar marca e exige a marca nos demais casos.
- Remove da revisão a confirmação de marca e os campos de conteúdo da embalagem.
- Remove o campo e o envio de marca quando o produto estiver configurado para não solicitá-la.
- Mantém o resumo da importação no fim da lista, sem sobrepor os itens durante a revisão.
- Remove a camada de composição residual da barra de importação no Chrome para Android.
- Exibe notas lidas como "Aguardando revisão" e inclui o link para a NFC-e original.
- Bloqueia itens revisados até a edição pelo lápis, inclusive em notas importadas.
- Permite editar o apelido do estabelecimento diretamente na revisão da nota.
- Remove a descrição livre das variações, que passam a usar quantidade e unidade.

## 0.1.0 - 2026-09-12

- Cria a aplicação Angular 21 com Bootstrap e layout responsivo.
- Implementa leitura de QR Code pela câmera e envio ao FastAPI.
- Lista notas por situação e permite retomar uma revisão.
- Implementa revisão, cadastros rápidos e conclusão da importação.
- Adiciona proxy de desenvolvimento e container próprio para o build Angular.
- Integra o frontend ao gateway Nginx separado na raiz do monorepo.
