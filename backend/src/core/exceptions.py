"""Exceções compartilhadas pela consulta e extração."""


class ErroLeitura(ValueError):
    """A resposta não contém uma nota completa e consistente."""


class ErroConsulta(RuntimeError):
    """A consulta HTTP não pôde ser concluída."""


class ErroPersistencia(RuntimeError):
    """Não foi possível gravar ou recuperar os dados no banco."""
