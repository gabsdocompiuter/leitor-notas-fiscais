const { readFileSync } = require('node:fs');
const { resolve } = require('node:path');
const { runInNewContext } = require('node:vm');
const { test } = require('node:test');
const assert = require('node:assert/strict');

const script = readFileSync(resolve(__dirname, '../public/tema-inicial.js'), 'utf8');

function executar(salva, sistemaEscuro, bloqueado = false, semMatchMedia = false) {
  const atributos = {};
  const documento = {
    documentElement: { setAttribute: (nome, valor) => { atributos[nome] = valor; } },
    querySelector: () => ({ setAttribute: (_, valor) => { atributos.cor = valor; } }),
  };
  runInNewContext(script, {
    document: documento,
    localStorage: { getItem: () => {
      if (bloqueado) throw new Error('bloqueado');
      return salva;
    } },
    window: semMatchMedia ? {} : { matchMedia: () => ({ matches: sistemaEscuro }) },
  });
  return atributos;
}

for (const [salva, sistemaEscuro, esperado] of [
  [null, false, 'light'], [null, true, 'dark'],
  ['claro', true, 'light'], ['escuro', false, 'dark'],
  ['sistema', true, 'dark'], ['invalido', true, 'dark'],
]) {
  test(`tema antes do Angular: ${salva}, sistema escuro ${sistemaEscuro}`, () => {
    const resultado = executar(salva, sistemaEscuro);
    assert.equal(resultado['data-bs-theme'], esperado);
    assert.equal(resultado.cor, esperado === 'dark' ? '#212529' : '#ffffff');
  });
}

test('armazenamento bloqueado mantém a preferência do sistema', () => {
  assert.equal(executar(null, true, true)['data-bs-theme'], 'dark');
});

test('sem matchMedia usa claro por padrão', () => {
  assert.equal(executar(null, false, false, true)['data-bs-theme'], 'light');
});
