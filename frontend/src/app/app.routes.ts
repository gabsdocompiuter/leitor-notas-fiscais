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
    path: '**',
    loadComponent: () =>
      import('./features/nao-encontrado/nao-encontrado').then((m) => m.NaoEncontrado),
    title: 'Página não encontrada · Minhas Compras',
  },
];
