# Changelog

## Não lançado

- Substitui os selects de produto e marca por modais com busca instantânea e criação.
- Inicia a busca de produto com a descrição original do item da nota.
- Centraliza os modais no espaço visível do celular durante o uso do teclado.
- Formata a busca inicial do produto e adiciona busca e criação de categorias em modal.
- Abre a busca de marca vazia, mantendo a descrição fiscal apenas no título.
- Adiciona ao produto a opção de não solicitar marca e exige a marca nos demais casos.
- Remove da revisão a confirmação de marca e os campos de conteúdo da embalagem.
- Remove o campo e o envio de marca quando o produto estiver configurado para não solicitá-la.

## 0.1.0 - 2026-09-12

- Cria a aplicação Angular 21 com Bootstrap e layout responsivo.
- Implementa leitura de QR Code pela câmera e envio ao FastAPI.
- Lista notas por situação e permite retomar uma revisão.
- Implementa revisão, cadastros rápidos e conclusão da importação.
- Adiciona proxy de desenvolvimento e container próprio para o build Angular.
- Integra o frontend ao gateway Nginx separado na raiz do monorepo.
