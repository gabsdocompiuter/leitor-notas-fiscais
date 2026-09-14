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
  { path: 'cadastros', loadComponent: () => import('./features/cadastros/cadastros').then((m) => m.Cadastros), title: 'Cadastros · Minhas Compras' },
  { path: 'cadastros/categorias', loadComponent: () => import('./features/cadastros/catalogo-nomes').then((m) => m.CatalogoNomes), data: { tipo: 'categorias' }, title: 'Categorias · Minhas Compras' },
  { path: 'cadastros/marcas', loadComponent: () => import('./features/cadastros/catalogo-nomes').then((m) => m.CatalogoNomes), data: { tipo: 'marcas' }, title: 'Marcas · Minhas Compras' },
  { path: 'cadastros/produtos', loadComponent: () => import('./features/cadastros/produtos').then((m) => m.Produtos), title: 'Produtos · Minhas Compras' },
  { path: 'cadastros/estabelecimentos', loadComponent: () => import('./features/cadastros/estabelecimentos').then((m) => m.Estabelecimentos), title: 'Estabelecimentos · Minhas Compras' },
  {
    path: '**',
    loadComponent: () =>
      import('./features/nao-encontrado/nao-encontrado').then((m) => m.NaoEncontrado),
    title: 'Página não encontrada · Minhas Compras',
  },
];
