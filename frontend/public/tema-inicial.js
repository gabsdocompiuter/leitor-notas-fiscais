// Executa antes dos estilos e do Angular para evitar exibir o tema errado ao carregar.
(() => {
  let preferencia = 'sistema';
  try {
    const salva = localStorage.getItem('lnf-tema');
    if (['sistema', 'claro', 'escuro'].includes(salva)) preferencia = salva;
  } catch {
    // Navegadores com armazenamento bloqueado usam a preferência do sistema.
  }
  const escuro =
    preferencia === 'escuro' ||
    (preferencia === 'sistema' &&
      window.matchMedia?.('(prefers-color-scheme: dark)').matches === true);
  document.documentElement.setAttribute('data-bs-theme', escuro ? 'dark' : 'light');
  document
    .querySelector('meta[name="theme-color"]')
    ?.setAttribute('content', escuro ? '#212529' : '#ffffff');
})();
