from collections import deque
from typing import Iterable

class CycleError(Exception):
    pass

class RedeDisciplinas:
    """
    Grafo dirigido onde vértices são disciplinas (str) e arestas representam
    pré-requisitos: (A -> B) significa A é pré-requisito direto de B.
    Para cada disciplina guardamos o conjunto de seus pré-requisitos diretos.
    """

    def __init__(self, disciplinas: Optional[Iterable[str]] = None):
        self._pre_reqs: Dict[str, Set[str]] = {}
        if disciplinas:
            for d in disciplinas:
                self.adicionar_disciplina(d)

    # --- CRUD de disciplinas ---
    def adicionar_disciplina(self, disciplina: str) -> None:
        """Adiciona uma disciplina (não faz nada se já existe)."""
        if disciplina not in self._pre_reqs:
            self._pre_reqs[disciplina] = set()

    def remover_disciplina(self, disciplina: str) -> None:
        """
        Remove uma disciplina e todas as arestas incidentes (tanto como dependente
        quanto como pré-requisito).
        """
        if disciplina not in self._pre_reqs:
            return
        del self._pre_reqs[disciplina]
        for deps in self._pre_reqs.values():
            deps.discard(disciplina)

    # --- Arestas (pré-requisitos) ---
    def adicionar_pre_requisito(self, pre: str, disciplina: str) -> None:
        """
        Adiciona aresta pre -> disciplina.
        Cria nós automaticamente se necessário.
        """
        self.adicionar_disciplina(pre)
        self.adicionar_disciplina(disciplina)
        self._pre_reqs[disciplina].add(pre)

    def remover_pre_requisito(self, pre: str, disciplina: str) -> None:
        """Remove a aresta pre -> disciplina, se existir."""
        if disciplina in self._pre_reqs:
            self._pre_reqs[disciplina].discard(pre)

    # --- Consultas ---
    def disciplinas(self) -> List[str]:
        """Lista todas as disciplinas."""
        return list(self._pre_reqs.keys())

    def prerequisitos_diretos(self, disciplina: str) -> List[str]:
        """Retorna a lista de pré-requisitos diretos de 'disciplina'."""
        if disciplina not in self._pre_reqs:
            raise KeyError(f"Disciplina desconhecida: {disciplina}")
        return list(self._pre_reqs[disciplina])

    def todos_prerequisitos(self, disciplina: str) -> List[str]:
        """Retorna todos os pré-requisitos (ancestros) de 'disciplina' em ordem qualquer."""
        if disciplina not in self._pre_reqs:
            raise KeyError(f"Disciplina desconhecida: {disciplina}")
        vistos: Set[str] = set()
        pilha = list(self._pre_reqs[disciplina])
        while pilha:
            cur = pilha.pop()
            if cur in vistos:
                continue
            vistos.add(cur)
            pilha.extend(self._pre_reqs.get(cur, set()))
        return list(vistos)

    def existe_dependencia(self, a: str, b: str) -> bool:
        """
        Verifica se existe dependência de 'a' para 'b', isto é, se 'a' é
        pré-requisito (direto ou indireto) de 'b'.
        """
        if b not in self._pre_reqs or a not in self._pre_reqs:
            return False
        # DFS até encontrar 'a'
        pilha = list(self._pre_reqs[b])
        visitados: Set[str] = set()
        while pilha:
            cur = pilha.pop()
            if cur == a:
                return True
            if cur in visitados:
                continue
            visitados.add(cur)
            pilha.extend(self._pre_reqs.get(cur, set()))
        return False

    # --- Ciclos e ordenação ---
    def tem_ciclo(self) -> bool:
        """Retorna True se o grafo contiver um ciclo (pré-requisito circular)."""
        try:
            self.ordenacao_topologica()
            return False
        except CycleError:
            return True

    def ordenacao_topologica(self) -> List[str]:
        """
        Retorna uma ordenação topológica de todas as disciplinas.
        Lança CycleError se houver ciclo.
        Método: algoritmo de Kahn (conta pré-requisitos, começa em nós com grau 0).
        """
        in_degree: Dict[str, int] = {node: len(prs) for node, prs in self._pre_reqs.items()}
        fila = deque([n for n, d in in_degree.items() if d == 0])
        ordem: List[str] = []

        # adjacência reversa para saber quais disciplinas dependem de uma dada disciplina
        reverse_adj: Dict[str, Set[str]] = {node: set() for node in self._pre_reqs}
        for node, prs in self._pre_reqs.items():
            for p in prs:
                reverse_adj[p].add(node)

        while fila:
            n = fila.popleft()
            ordem.append(n)
            for m in reverse_adj.get(n, ()):
                in_degree[m] -= 1
                if in_degree[m] == 0:
                    fila.append(m)

        if len(ordem) != len(self._pre_reqs):
            raise CycleError("Ciclo detectado na grade de disciplinas.")
        return ordem

    # --- Plano de estudo e progressão por níveis ---
    def plano_de_estudo_para(self, alvo: str) -> List[str]:
        """
        Retorna uma ordem válida mínima de disciplinas necessárias para cursar 'alvo',
        terminando em 'alvo'. Lança KeyError se alvo desconhecido; CycleError se houver ciclo.
        """
        if alvo not in self._pre_reqs:
            raise KeyError(f"Disciplina desconhecida: {alvo}")
        necessario: Set[str] = set(self.todos_prerequisitos(alvo))
        necessario.add(alvo)

        sub_prs: Dict[str, Set[str]] = {}
        for node in necessario:
            sub_prs[node] = {p for p in self._pre_reqs.get(node, set()) if p in necessario}

        in_degree: Dict[str, int] = {n: len(prs) for n, prs in sub_prs.items()}
        fila = deque([n for n, d in in_degree.items() if d == 0])
        ordem: List[str] = []

        reverse_adj: Dict[str, Set[str]] = {n: set() for n in sub_prs}
        for node, prs in sub_prs.items():
            for p in prs:
                reverse_adj[p].add(node)

        while fila:
            n = fila.popleft()
            ordem.append(n)
            for m in reverse_adj.get(n, ()):
                in_degree[m] -= 1
                if in_degree[m] == 0:
                    fila.append(m)

        if len(ordem) != len(sub_prs):
            raise CycleError("Ciclo detectado na sub-rede necessária para a disciplina alvo.")
        return ordem

    def progressao_por_niveis_para(self, alvo: str) -> List[Set[str]]:
        """
        Retorna a progressão em níveis (conjuntos de disciplinas que podem ser cursadas
        em paralelo) até o 'alvo'. O último nível conterá o 'alvo'.
        """
        ordem = self.plano_de_estudo_para(alvo)
        necessario: Set[str] = set(ordem)
        sub_prs = {n: {p for p in self._pre_reqs.get(n, set()) if p in necessario} for n in necessario}
        in_degree = {n: len(ps) for n, ps in sub_prs.items()}

        niveis: List[Set[str]] = []
        disponiveis = {n for n, d in in_degree.items() if d == 0}
        processados: Set[str] = set()
        while disponiveis:
            niveis.append(set(disponiveis))
            proximos: Set[str] = set()
            for n in disponiveis:
                processados.add(n)
                for m in necessario:
                    if n in sub_prs.get(m, set()):
                        in_degree[m] -= 1
                        if in_degree[m] == 0:
                            proximos.add(m)
            disponiveis = proximos - processados
        return niveis

    def __repr__(self) -> str:
        return f"RedeDisciplinas({len(self._pre_reqs)} disciplinas)"
