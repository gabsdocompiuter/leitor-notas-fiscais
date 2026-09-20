import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'notas' },
  {
    path: 'notas',
    loadComponent: () =>
      import('./features/notas/listagem-notas/listagem-notas').then((m) => m.ListagemNotas),
    title: 'Notas · Minhas Compras',
  },
  {
    path: 'notas/:chave/revisao',
    loadComponent: () =>
      import('./features/notas/revisao-notas/revisao-notas').then((m) => m.RevisaoNotas),
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
      import('./features/cadastros/categorias/categorias').then((m) => m.Categorias),
    title: 'Categorias · Minhas Compras',
  },
  {
    path: 'cadastros/categorias/new',
    loadComponent: () =>
      import('./features/cadastros/categorias/cadastro-categoria/cadastro-categoria').then(
        (m) => m.CadastroCategoria,
      ),
    title: 'Nova categoria · Minhas Compras',
  },
  {
    path: 'cadastros/categorias/:id',
    loadComponent: () =>
      import('./features/cadastros/categorias/cadastro-categoria/cadastro-categoria').then(
        (m) => m.CadastroCategoria,
      ),
    title: 'Editar categoria · Minhas Compras',
  },
  {
    path: 'cadastros/marcas',
    loadComponent: () => import('./features/cadastros/marcas/marcas').then((m) => m.Marcas),
    title: 'Marcas · Minhas Compras',
  },
  {
    path: 'cadastros/marcas/new',
    loadComponent: () =>
      import('./features/cadastros/marcas/cadastro-marca/cadastro-marca').then(
        (m) => m.CadastroMarca,
      ),
    title: 'Nova marca · Minhas Compras',
  },
  {
    path: 'cadastros/marcas/:id',
    loadComponent: () =>
      import('./features/cadastros/marcas/cadastro-marca/cadastro-marca').then(
        (m) => m.CadastroMarca,
      ),
    title: 'Editar marca · Minhas Compras',
  },
  {
    path: 'cadastros/produtos',
    loadComponent: () => import('./features/cadastros/produtos/produtos').then((m) => m.Produtos),
    title: 'Produtos · Minhas Compras',
  },
  {
    path: 'cadastros/produtos/new',
    loadComponent: () =>
      import('./features/cadastros/produtos/cadastro-produto/cadastro-produto').then(
        (m) => m.CadastroProduto,
      ),
    title: 'Novo produto · Minhas Compras',
  },
  {
    path: 'cadastros/produtos/:id',
    loadComponent: () =>
      import('./features/cadastros/produtos/cadastro-produto/cadastro-produto').then(
        (m) => m.CadastroProduto,
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
      import('./features/cadastros/estabelecimentos/cadastro-estabelecimento/cadastro-estabelecimento').then(
        (m) => m.CadastroEstabelecimento,
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
