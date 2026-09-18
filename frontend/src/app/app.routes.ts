import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'notas' },
  {
    path: 'notas',
    loadComponent: () => import('./features/notas/lista-notas').then((m) => m.ListaNotas),
    title: 'Notas · Minhas Compras',
  },
  {
    path: 'notas/:chave/revisao',
    loadComponent: () => import('./features/notas/revisao-nota').then((m) => m.RevisaoNota),
    title: 'Revisar nota · Minhas Compras',
  },
  {
    path: 'ler',
    loadComponent: () => import('./features/leituras/leitura-qrcode').then((m) => m.LeituraQrcode),
    title: 'Ler nota · Minhas Compras',
  },
  {
    path: 'cadastros',
    loadComponent: () =>
      import('./features/cadastros/cadastros/cadastros').then((m) => m.Cadastros),
    title: 'Cadastros · Minhas Compras',
  },
  {
    path: 'cadastros/categorias',
    loadComponent: () =>
      import('./features/cadastros/catalogo-nomes/catalogo-nomes').then((m) => m.CatalogoNomes),
    data: { tipo: 'categorias' },
    title: 'Categorias · Minhas Compras',
  },
  {
    path: 'cadastros/categorias/new',
    loadComponent: () =>
      import('./features/cadastros/catalogo-nome-formulario/catalogo-nome-formulario').then(
        (m) => m.CatalogoNomeFormulario,
      ),
    data: { tipo: 'categorias' },
    title: 'Nova categoria · Minhas Compras',
  },
  {
    path: 'cadastros/categorias/:id',
    loadComponent: () =>
      import('./features/cadastros/catalogo-nome-formulario/catalogo-nome-formulario').then(
        (m) => m.CatalogoNomeFormulario,
      ),
    data: { tipo: 'categorias' },
    title: 'Editar categoria · Minhas Compras',
  },
  {
    path: 'cadastros/marcas',
    loadComponent: () =>
      import('./features/cadastros/catalogo-nomes/catalogo-nomes').then((m) => m.CatalogoNomes),
    data: { tipo: 'marcas' },
    title: 'Marcas · Minhas Compras',
  },
  {
    path: 'cadastros/marcas/new',
    loadComponent: () =>
      import('./features/cadastros/catalogo-nome-formulario/catalogo-nome-formulario').then(
        (m) => m.CatalogoNomeFormulario,
      ),
    data: { tipo: 'marcas' },
    title: 'Nova marca · Minhas Compras',
  },
  {
    path: 'cadastros/marcas/:id',
    loadComponent: () =>
      import('./features/cadastros/catalogo-nome-formulario/catalogo-nome-formulario').then(
        (m) => m.CatalogoNomeFormulario,
      ),
    data: { tipo: 'marcas' },
    title: 'Editar marca · Minhas Compras',
  },
  {
    path: 'cadastros/produtos',
    loadComponent: () =>
      import('./features/cadastros/produtos-lista/produtos-lista').then((m) => m.ProdutosLista),
    title: 'Produtos · Minhas Compras',
  },
  {
    path: 'cadastros/produtos/new',
    loadComponent: () =>
      import('./features/cadastros/produto-formulario/produto-formulario').then(
        (m) => m.ProdutoFormulario,
      ),
    title: 'Novo produto · Minhas Compras',
  },
  {
    path: 'cadastros/produtos/:id',
    loadComponent: () =>
      import('./features/cadastros/produto-formulario/produto-formulario').then(
        (m) => m.ProdutoFormulario,
      ),
    title: 'Editar produto · Minhas Compras',
  },
  {
    path: 'cadastros/estabelecimentos',
    loadComponent: () =>
      import('./features/cadastros/estabelecimentos/estabelecimentos').then(
        (m) => m.Estabelecimentos,
      ),
    title: 'Estabelecimentos · Minhas Compras',
  },
  {
    path: 'cadastros/estabelecimentos/:id',
    loadComponent: () =>
      import('./features/cadastros/estabelecimento-formulario/estabelecimento-formulario').then(
        (m) => m.EstabelecimentoFormulario,
      ),
    title: 'Editar estabelecimento · Minhas Compras',
  },
  {
    path: '**',
    loadComponent: () =>
      import('./features/nao-encontrado/nao-encontrado').then((m) => m.NaoEncontrado),
    title: 'Página não encontrada · Minhas Compras',
  },
];
