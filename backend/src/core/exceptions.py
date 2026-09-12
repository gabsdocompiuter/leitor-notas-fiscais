"""Exceções compartilhadas pela consulta e extração."""


class ErroLeitura(ValueError):
    """A resposta não contém uma nota completa e consistente."""


class ErroConsulta(RuntimeError):
    """A consulta HTTP não pôde ser concluída."""


class ErroQrCode(ErroConsulta):
    """A URL recebida não representa um QR Code suportado."""


class ErroPersistencia(RuntimeError):
    """Não foi possível gravar ou recuperar os dados no banco."""


class NaoEncontrado(LookupError):
    """O recurso solicitado não existe no banco."""


class DadosInvalidos(ValueError):
    """Os dados recebidos não atendem às regras da aplicação."""


class Conflito(RuntimeError):
    """O estado atual do recurso impede a operação."""
