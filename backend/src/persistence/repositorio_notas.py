import json
import sqlite3
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from ..core.exceptions import ErroPersistencia
from ..models.apresentacao_produto import ApresentacaoProduto
from ..models.categoria import Categoria
from ..models.estabelecimento import Estabelecimento
from ..models.item import Item
from ..models.leitura_nota import LeituraNota
from ..models.marca import Marca
from ..models.nota import Nota
from ..models.produto import Produto
from ..models.situacao_nota import SituacaoNota
from ..models.unidade_medida import UnidadeMedida
from .banco_sqlite import BancoSQLite


class RepositorioNotas:
    def __init__(self, banco: BancoSQLite):
        self.banco = banco
        self.banco.inicializar()

    def registrar_leitura(self, url: str, chave: str) -> LeituraNota:
        """Guarda o QR Code antes da consulta e reutiliza a captura da mesma chave."""
        with self.banco.conectar() as conexao:
            conexao.execute("BEGIN IMMEDIATE")
            existente = conexao.execute("SELECT * FROM leituras WHERE chave = ?", (chave,)).fetchone()
            if existente is not None:
                return self._ler_captura(conexao, existente)
            nota = conexao.execute("SELECT id FROM notas WHERE chave = ?", (chave,)).fetchone()
            leitura = LeituraNota(url=url)
            conexao.execute(
                "INSERT INTO leituras (id, chave, url, nota_id, erro_consulta, criada_em) VALUES (?, ?, ?, ?, ?, ?)",
                (str(leitura.id), chave, url, nota["id"] if nota else None, None, leitura.criada_em.isoformat()),
            )
            if nota is not None:
                leitura.nota = self._ler_nota(conexao, nota["id"])
            return leitura

    def registrar_erro(self, leitura_id: UUID, mensagem: str) -> None:
        with self.banco.conectar() as conexao:
            conexao.execute(
                "UPDATE leituras SET erro_consulta = ? WHERE id = ? AND nota_id IS NULL",
                (mensagem, str(leitura_id)),
            )

    def obter_leitura_por_chave(self, chave: str) -> LeituraNota | None:
        with self.banco.conectar() as conexao:
            linha = conexao.execute("SELECT * FROM leituras WHERE chave = ?", (chave,)).fetchone()
            return self._ler_captura(conexao, linha) if linha is not None else None

    def obter_por_chave(self, chave: str) -> Nota | None:
        with self.banco.conectar() as conexao:
            linha = conexao.execute("SELECT id FROM notas WHERE chave = ?", (chave,)).fetchone()
            return self._ler_nota(conexao, linha["id"]) if linha is not None else None

    def salvar(self, nota: Nota, leitura_id: UUID | None = None) -> Nota:
        """Insere atomicamente; uma chave existente retorna os dados já salvos."""
        with self.banco.conectar() as conexao:
            conexao.execute("BEGIN IMMEDIATE")
            existente = conexao.execute("SELECT id FROM notas WHERE chave = ?", (nota.chave,)).fetchone()
            if existente is None:
                self._inserir_nota(conexao, nota)
                nota_id = str(nota.id)
            else:
                # Reconsultar não apaga apelidos, revisões ou uma importação confirmada.
                nota_id = existente["id"]
            if leitura_id is not None:
                atualizacao = conexao.execute(
                    "UPDATE leituras SET nota_id = ?, erro_consulta = NULL WHERE id = ? AND chave = ?",
                    (nota_id, str(leitura_id), nota.chave),
                )
                if atualizacao.rowcount != 1:
                    raise ErroPersistencia("A leitura não corresponde à chave da nota.")
            return self._ler_nota(conexao, nota_id)

    def _inserir_nota(self, conexao: sqlite3.Connection, nota: Nota) -> None:
        if (
            not nota.itens or len(nota.itens) != nota.quantidade_itens
            or sum((item.valor_total for item in nota.itens), Decimal(0)) != nota.valor_total
            or nota.valor_total - nota.desconto != nota.valor_a_pagar
        ):
            raise ErroPersistencia("A nota está incompleta ou seus totais são inconsistentes.")
        loja = nota.estabelecimento
        conexao.execute(
            "INSERT INTO estabelecimentos (id, cnpj, razao_social, apelido) VALUES (?, ?, ?, ?) ON CONFLICT(cnpj) DO NOTHING",
            (str(loja.id), loja.cnpj, loja.razao_social, loja.apelido),
        )
        loja_id = conexao.execute("SELECT id FROM estabelecimentos WHERE cnpj = ?", (loja.cnpj,)).fetchone()["id"]
        conexao.execute(
            """INSERT INTO notas (id, chave, numero, serie, estabelecimento_id, emissao,
                quantidade_itens, valor_total, desconto, valor_a_pagar, url_origem, situacao)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (str(nota.id), nota.chave, nota.numero, nota.serie, loja_id, nota.emissao.isoformat(),
             nota.quantidade_itens, str(nota.valor_total), str(nota.desconto), str(nota.valor_a_pagar),
             nota.url_origem, nota.situacao.value),
        )
        for item in nota.itens:
            if item.apresentacao is not None:
                self._salvar_apresentacao(conexao, item.apresentacao)
            conexao.execute(
                """INSERT INTO itens (id, nota_id, numero, codigo, descricao_original, quantidade,
                    unidade_original, valor_unitario, valor_total, alertas, apresentacao_id,
                    unidade_corrigida, quantidade_normalizada, revisado)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (str(item.id), str(nota.id), item.numero, item.codigo, item.descricao_original,
                 str(item.quantidade), item.unidade_original, str(item.valor_unitario), str(item.valor_total),
                 json.dumps(item.alertas, ensure_ascii=False), str(item.apresentacao.id) if item.apresentacao else None,
                 item.unidade_corrigida.value if item.unidade_corrigida else None,
                 str(item.quantidade_normalizada) if item.quantidade_normalizada is not None else None,
                 int(item.revisado)),
            )

    def _salvar_apresentacao(self, conexao: sqlite3.Connection, apresentacao: ApresentacaoProduto) -> None:
        produto = apresentacao.produto
        categoria = produto.categoria
        conexao.execute("INSERT INTO categorias (id, nome) VALUES (?, ?) ON CONFLICT(id) DO NOTHING", (str(categoria.id), categoria.nome))
        conexao.execute(
            "INSERT INTO produtos (id, nome, categoria_id, unidade_base) VALUES (?, ?, ?, ?) ON CONFLICT(id) DO NOTHING",
            (str(produto.id), produto.nome, str(categoria.id), produto.unidade_base.value),
        )
        if apresentacao.marca is not None:
            marca = apresentacao.marca
            conexao.execute("INSERT INTO marcas (id, nome) VALUES (?, ?) ON CONFLICT(id) DO NOTHING", (str(marca.id), marca.nome))
        conexao.execute(
            """INSERT INTO apresentacoes_produto
                (id, produto_id, marca_id, conteudo_embalagem, unidade_embalagem, marca_confirmada)
                VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO NOTHING""",
            (str(apresentacao.id), str(produto.id), str(apresentacao.marca.id) if apresentacao.marca else None,
             str(apresentacao.conteudo_embalagem) if apresentacao.conteudo_embalagem is not None else None,
             apresentacao.unidade_embalagem.value if apresentacao.unidade_embalagem else None,
             int(apresentacao.marca_confirmada)),
        )

    def _ler_captura(self, conexao: sqlite3.Connection, linha: sqlite3.Row) -> LeituraNota:
        return LeituraNota(
            id=UUID(linha["id"]), url=linha["url"], criada_em=datetime.fromisoformat(linha["criada_em"]),
            erro_consulta=linha["erro_consulta"],
            nota=self._ler_nota(conexao, linha["nota_id"]) if linha["nota_id"] else None,
        )

    def _ler_nota(self, conexao: sqlite3.Connection, nota_id: str) -> Nota:
        linha = conexao.execute("SELECT * FROM notas WHERE id = ?", (nota_id,)).fetchone()
        loja = conexao.execute("SELECT * FROM estabelecimentos WHERE id = ?", (linha["estabelecimento_id"],)).fetchone()
        itens = []
        for item in conexao.execute("SELECT * FROM itens WHERE nota_id = ? ORDER BY numero", (nota_id,)).fetchall():
            itens.append(Item(
                id=UUID(item["id"]), numero=item["numero"], codigo=item["codigo"],
                descricao_original=item["descricao_original"], quantidade=Decimal(item["quantidade"]),
                unidade_original=item["unidade_original"], valor_unitario=Decimal(item["valor_unitario"]),
                valor_total=Decimal(item["valor_total"]), alertas=json.loads(item["alertas"]),
                apresentacao=self._ler_apresentacao(conexao, item["apresentacao_id"]) if item["apresentacao_id"] else None,
                unidade_corrigida=UnidadeMedida(item["unidade_corrigida"]) if item["unidade_corrigida"] else None,
                quantidade_normalizada=Decimal(item["quantidade_normalizada"]) if item["quantidade_normalizada"] is not None else None,
                revisado=bool(item["revisado"]),
            ))
        return Nota(
            id=UUID(linha["id"]), chave=linha["chave"], numero=linha["numero"], serie=linha["serie"],
            estabelecimento=Estabelecimento(id=UUID(loja["id"]), cnpj=loja["cnpj"], razao_social=loja["razao_social"], apelido=loja["apelido"]),
            emissao=datetime.fromisoformat(linha["emissao"]), quantidade_itens=linha["quantidade_itens"],
            valor_total=Decimal(linha["valor_total"]), desconto=Decimal(linha["desconto"]),
            valor_a_pagar=Decimal(linha["valor_a_pagar"]), itens=itens, url_origem=linha["url_origem"],
            situacao=SituacaoNota(linha["situacao"]),
        )

    def _ler_apresentacao(self, conexao: sqlite3.Connection, apresentacao_id: str) -> ApresentacaoProduto:
        linha = conexao.execute("SELECT * FROM apresentacoes_produto WHERE id = ?", (apresentacao_id,)).fetchone()
        produto = conexao.execute("SELECT * FROM produtos WHERE id = ?", (linha["produto_id"],)).fetchone()
        categoria = conexao.execute("SELECT * FROM categorias WHERE id = ?", (produto["categoria_id"],)).fetchone()
        marca = conexao.execute("SELECT * FROM marcas WHERE id = ?", (linha["marca_id"],)).fetchone() if linha["marca_id"] else None
        return ApresentacaoProduto(
            id=UUID(linha["id"]),
            produto=Produto(
                id=UUID(produto["id"]), nome=produto["nome"], unidade_base=UnidadeMedida(produto["unidade_base"]),
                categoria=Categoria(id=UUID(categoria["id"]), nome=categoria["nome"]),
            ),
            marca=Marca(id=UUID(marca["id"]), nome=marca["nome"]) if marca else None,
            conteudo_embalagem=Decimal(linha["conteudo_embalagem"]) if linha["conteudo_embalagem"] is not None else None,
            unidade_embalagem=UnidadeMedida(linha["unidade_embalagem"]) if linha["unidade_embalagem"] else None,
            marca_confirmada=bool(linha["marca_confirmada"]),
        )
