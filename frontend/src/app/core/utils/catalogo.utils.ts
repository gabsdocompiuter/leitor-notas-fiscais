function normalizar(valor: string): string {
  return valor
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLocaleLowerCase('pt-BR')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim();
}

export function capitalizarIniciais(valor: string): string {
  return valor
    .toLocaleLowerCase('pt-BR')
    .replace(/(^|[\s-])(\p{L})/gu, (_trecho, separador: string, letra: string) => {
      return `${separador}${letra.toLocaleUpperCase('pt-BR')}`;
    });
}

function pontuarBusca(termos: string[], texto: string): number {
  if (termos.length === 0) return 1;
  const palavras = normalizar(texto).split(' ').filter(Boolean);
  return termos.reduce(
    (total, termo) =>
      total +
      (palavras.some((palavra) => palavra.includes(termo) || termo.includes(palavra)) ? 1 : 0),
    0,
  );
}

export function filtrarCatalogo<T>(
  itens: T[],
  busca: string,
  obterTexto: (item: T) => string,
  limite = 30,
): T[] {
  const termos = normalizar(busca).split(' ').filter(Boolean);
  return itens
    .map((item) => ({ item, pontos: pontuarBusca(termos, obterTexto(item)) }))
    .filter(({ pontos }) => termos.length === 0 || pontos > 0)
    .sort((a, b) => b.pontos - a.pontos || obterTexto(a.item).localeCompare(obterTexto(b.item)))
    .slice(0, limite)
    .map(({ item }) => item);
}
