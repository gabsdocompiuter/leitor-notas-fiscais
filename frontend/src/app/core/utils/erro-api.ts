import { HttpErrorResponse } from '@angular/common/http';

import { ErroApi } from '../models/api.models';

export function mensagemErro(erro: unknown): string {
  if (erro instanceof HttpErrorResponse) {
    const resposta = erro.error as Partial<ErroApi> | null;
    if (resposta?.mensagem) {
      return resposta.mensagem;
    }
    if (erro.status === 0) {
      return 'Não foi possível acessar o backend. Verifique se a API está em execução.';
    }
  }
  return 'Ocorreu um erro inesperado. Tente novamente.';
}
