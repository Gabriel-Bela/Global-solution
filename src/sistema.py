# -*- coding: utf-8 -*-
"""
                Global Solution 2026 (CitizenTech)

Sistema textual para registrar, consultar e acompanhar ocorrencias
de melhoria em bairros. Todos os dados sao simulados e sem informacao pessoal.

Executar a partir da raiz do repositorio:  python src/sistema.py
"""

import os
from collections import deque

# ------------------------------------------------------------------
# 1. CONSTANTES PADRONIZADAS
# ------------------------------------------------------------------
CATEGORIAS = ["iluminacao", "acessibilidade", "limpeza", "conservacao"]

# aberta     = registrada, ainda nao examinada pela equipe
# em_analise = a equipe esta avaliando ou executando o servico
# concluida  = problema resolvido (exige dia de conclusao)
SITUACOES = ["aberta", "em_analise", "concluida"]

try:
    PASTA_BASE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    PASTA_BASE = os.path.join(os.getcwd(), "src")

ARQ_DADOS = os.path.join(PASTA_BASE, "..", "data", "dados.csv")
ARQ_HISTORICO = os.path.join(PASTA_BASE, "..", "data", "historico.csv")

# ------------------------------------------------------------------
# 2. ESTRUTURAS DE DADOS (variaveis globais do sistema)
# ------------------------------------------------------------------
ocorrencias = []        # LISTA: todas as ocorrencias validas (percorrer / listar)
indice = {}             # DICIONARIO: id -> ocorrencia (acesso direto pelo codigo)
fila_analise = deque()  # FILA: ids ainda nao examinados, por ordem de registro
pilha_eventos = []      # PILHA: eventos de status (topo = ultimo)
hierarquia = {}         # HIERARQUIA: bairro -> categoria -> [ids]
rejeitados = []         # registros do arquivo que falharam na validacao


# ------------------------------------------------------------------
# 3. VALIDACAO
# ------------------------------------------------------------------
def validar_registro(reg):
    """Retorna (True, "") se o registro e valido, ou (False, motivo)."""
    if reg["categoria"] == "":
        return False, "categoria ausente"
    elif reg["categoria"] not in CATEGORIAS:
        return False, "categoria desconhecida: " + reg["categoria"]
    elif reg["descricao"] == "" or reg["local"] == "" or reg["bairro"] == "":
        return False, "descricao, bairro ou local ausente"
    elif reg["status"] not in SITUACOES:
        return False, "situacao desconhecida: " + reg["status"]
    elif not reg["dia_abertura"].isdigit():
        return False, "dia de abertura invalido"

    conclusao_ok = reg["dia_conclusao"].isdigit()

    # Expressao booleana (documentada no README):
    # concluida sem dia valido OU dia de conclusao anterior a abertura
    if reg["status"] == "concluida" and (
        not conclusao_ok or int(reg["dia_conclusao"]) < int(reg["dia_abertura"])
    ):
        return False, "concluida sem dia de conclusao valido"
    elif reg["status"] != "concluida" and reg["dia_conclusao"] != "":
        return False, "dia de conclusao preenchido em ocorrencia nao concluida"
    return True, ""


def transicao_valida(atual, novo):
    """Regras de mudanca de situacao (usa AND, OR e NOT)."""
    if atual == novo:
        return False
    permitida = (atual == "aberta" and novo == "em_analise") or (
        atual == "em_analise" and (novo == "concluida" or novo == "aberta")
    )
    return permitida and not (atual == "concluida")


# ------------------------------------------------------------------
# 4. CARGA DE DADOS
# ------------------------------------------------------------------
def ler_csv(caminho):
    """Le um CSV simples (sem virgulas dentro dos campos). Retorna lista de dicts."""
    linhas = []
    try:
        arquivo = open(caminho, "r", encoding="utf-8-sig")
    except OSError:
        print("ERRO: nao foi possivel abrir o arquivo " + caminho)
        return linhas
    cabecalho = []
    numero = 0
    for linha in arquivo:
        linha = linha.strip()
        if linha == "":
            continue
        campos = [c.strip() for c in linha.split(",")]
        if numero == 0:
            cabecalho = campos
        else:
            while len(campos) < len(cabecalho):
                campos.append("")
            registro = {}
            for i in range(len(cabecalho)):
                registro[cabecalho[i]] = campos[i]
            linhas.append(registro)
        numero += 1
    arquivo.close()
    return linhas


def adicionar_na_hierarquia(oc):
    bairro = oc["bairro"]
    categoria = oc["categoria"]
    if bairro not in hierarquia:
        hierarquia[bairro] = {}
    if categoria not in hierarquia[bairro]:
        hierarquia[bairro][categoria] = []
    hierarquia[bairro][categoria].append(oc["id"])


def carregar_sistema():
    for reg in ler_csv(ARQ_DADOS):
        ok, motivo = validar_registro(reg)
        if ok:
            ocorrencias.append(reg)
            indice[reg["id"]] = reg
            adicionar_na_hierarquia(reg)
        else:
            rejeitados.append((reg["id"], motivo))

    # Fila: ocorrencias abertas, em ordem de dia de abertura e depois de id
    abertas = []
    for oc in ocorrencias:
        if oc["status"] == "aberta":
            abertas.append(oc)
    abertas.sort(key=lambda o: (int(o["dia_abertura"]), o["id"]))
    for oc in abertas:
        fila_analise.append(oc["id"])

    # Pilha: eventos na ordem em que ocorreram (o ultimo fica no topo)
    for ev in ler_csv(ARQ_HISTORICO):
        if ev["id"] in indice:
            pilha_eventos.append(ev)


# ------------------------------------------------------------------
# 5. ENTRADA E SAIDA
# ------------------------------------------------------------------
def pedir_texto(msg):
    return input(msg).strip().lower()


def pedir_dia(msg, minimo=0):
    """Pede um numero inteiro (dia simulado) maior ou igual a 'minimo'."""
    while True:
        texto = input(msg).strip()
        if texto.isdigit() and int(texto) >= minimo:
            return int(texto)
        print("Valor invalido. Digite um numero inteiro >= " + str(minimo) + ".")


def mostrar_linha(oc):
    print(oc["id"].ljust(5) + oc["categoria"].ljust(16) + oc["bairro"].ljust(18)
          + oc["local"].ljust(20) + oc["status"])


def listar(lista):
    if len(lista) == 0:
        print("Nenhuma ocorrencia encontrada.")
        return
    print("COD".ljust(5) + "CATEGORIA".ljust(16) + "BAIRRO".ljust(18)
          + "LOCAL".ljust(20) + "STATUS")
    print("-" * 70)
    for oc in lista:
        mostrar_linha(oc)
    print("Total exibido: " + str(len(lista)))


# ------------------------------------------------------------------
# 6. FUNCIONALIDADES
# ------------------------------------------------------------------
def cadastrar():
    print("\n--- Cadastrar ocorrencia ---")
    print("Categorias: " + ", ".join(CATEGORIAS))
    categoria = pedir_texto("Categoria: ")
    descricao = input("Descricao breve (sem virgulas): ").strip().replace(",", " ")
    bairro = input("Bairro: ").strip().replace(",", " ")
    local = input("Local generico (ex.: Praca Central): ").strip().replace(",", " ")
    dia = pedir_dia("Dia simulado de abertura: ")

    # Gera um codigo unico: maior codigo existente + 1 (considera rejeitados)
    maior = 0
    for codigo in list(indice.keys()) + [r[0] for r in rejeitados]:
        if codigo.isdigit() and int(codigo) > maior:
            maior = int(codigo)
    novo_id = str(maior + 1).zfill(3)

    reg = {"id": novo_id, "categoria": categoria, "descricao": descricao,
           "bairro": bairro, "local": local, "dia_abertura": str(dia),
           "status": "aberta", "dia_conclusao": ""}
    ok, motivo = validar_registro(reg)
    if not ok:
        print("Cadastro recusado: " + motivo + ".")
        return

    ocorrencias.append(reg)
    indice[novo_id] = reg
    adicionar_na_hierarquia(reg)
    fila_analise.append(novo_id)
    print("Ocorrencia " + novo_id + " cadastrada com situacao 'aberta'.")


def buscar():
    print("\n--- Buscar por codigo ---")
    codigo = input("Codigo (ex.: 003): ").strip().zfill(3)
    if codigo in indice:
        oc = indice[codigo]
        print("Codigo:      " + oc["id"])
        print("Categoria:   " + oc["categoria"])
        print("Descricao:   " + oc["descricao"])
        print("Bairro:      " + oc["bairro"])
        print("Local:       " + oc["local"])
        print("Aberta no dia " + oc["dia_abertura"])
        print("Situacao:    " + oc["status"])
        if oc["dia_conclusao"] != "":
            print("Concluida no dia " + oc["dia_conclusao"])
        print("Historico desta ocorrencia:")
        achou = False
        for ev in pilha_eventos:
            if ev["id"] == codigo:
                print("  dia " + ev["dia"] + ": " + ev["de"] + " -> " + ev["para"])
                achou = True
        if not achou:
            print("  (sem mudancas de situacao)")
    else:
        print("Ocorrencia " + codigo + " nao encontrada.")


def filtrar():
    print("\n--- Filtrar ocorrencias ---")
    print("Deixe em branco para nao filtrar por aquele campo.")
    categoria = pedir_texto("Categoria (" + ", ".join(CATEGORIAS) + "): ")
    status = pedir_texto("Situacao (" + ", ".join(SITUACOES) + "): ")
    if categoria != "" and categoria not in CATEGORIAS:
        print("Categoria desconhecida.")
        return
    if status != "" and status not in SITUACOES:
        print("Situacao desconhecida.")
        return
    resultado = []
    for oc in ocorrencias:
        # (sem filtro de categoria OU igual) E (sem filtro de status OU igual)
        if (categoria == "" or oc["categoria"] == categoria) and (
            status == "" or oc["status"] == status
        ):
            resultado.append(oc)
    listar(resultado)


def atualizar():
    print("\n--- Atualizar situacao ---")
    codigo = input("Codigo da ocorrencia: ").strip().zfill(3)
    if codigo not in indice:
        print("Ocorrencia " + codigo + " nao encontrada.")
        return
    oc = indice[codigo]
    print("Situacao atual: " + oc["status"])
    novo = pedir_texto("Nova situacao (" + ", ".join(SITUACOES) + "): ")
    if novo not in SITUACOES:
        print("Situacao desconhecida. Nada foi alterado.")
        return
    if not transicao_valida(oc["status"], novo):
        print("Mudanca nao permitida: " + oc["status"] + " -> " + novo + ".")
        print("Permitido: aberta->em_analise, em_analise->concluida, em_analise->aberta.")
        return
    dia = pedir_dia("Dia simulado da alteracao: ", int(oc["dia_abertura"]))

    anterior = oc["status"]
    oc["status"] = novo
    if novo == "concluida":
        oc["dia_conclusao"] = str(dia)
    if anterior == "aberta" and codigo in fila_analise:
        fila_analise.remove(codigo)       # saiu da fila: ja foi examinada
    if novo == "aberta":
        fila_analise.append(codigo)       # voltou para a fila
    pilha_eventos.append({"id": codigo, "dia": str(dia), "de": anterior, "para": novo})
    print("Ocorrencia " + codigo + " atualizada: " + anterior + " -> " + novo + ".")


def mostrar_fila():
    print("\n--- Fila de demandas ainda nao examinadas (ordem de registro) ---")
    if len(fila_analise) == 0:
        print("Fila vazia.")
        return
    posicao = 1
    for codigo in fila_analise:
        oc = indice[codigo]
        print(str(posicao) + ". " + codigo + " - " + oc["categoria"]
              + " - " + oc["local"] + " (dia " + oc["dia_abertura"] + ")")
        posicao += 1


def mostrar_ultimos_eventos(quantidade=5):
    print("\n--- Ultimos eventos (do mais recente para o mais antigo) ---")
    copia = pilha_eventos[:]    # copia para nao esvaziar a pilha real
    mostrados = 0
    while len(copia) > 0 and mostrados < quantidade:
        ev = copia.pop()        # desempilha o topo
        print("dia " + ev["dia"] + " | ocorrencia " + ev["id"]
              + " | " + ev["de"] + " -> " + ev["para"])
        mostrados += 1
    if mostrados == 0:
        print("Nenhum evento registrado.")


def mostrar_hierarquia():
    print("\n--- Hierarquia: bairro -> categoria -> ocorrencias ---")
    for bairro in sorted(hierarquia):
        print(bairro)
        for categoria in sorted(hierarquia[bairro]):
            print("  " + categoria + ": " + ", ".join(hierarquia[bairro][categoria]))


def mostrar_rejeitados():
    print("\n--- Registros rejeitados na validacao ---")
    if len(rejeitados) == 0:
        print("Nenhum registro foi rejeitado.")
        return
    print("COD".ljust(8) + "MOTIVO")
    print("-" * 60)
    for codigo, motivo in rejeitados:
        if codigo == "":
            codigo = "(vazio)"
        print(codigo.ljust(8) + motivo)
    print("Total rejeitado: " + str(len(rejeitados)))
    print("Esses registros nao entram nos indicadores.")


# ------------------------------------------------------------------
# 7. INDICADORES
# ------------------------------------------------------------------
def construir_matriz():
    """Matriz (lista de listas): linhas = categorias, colunas = situacoes."""
    matriz = []
    for _ in CATEGORIAS:
        matriz.append([0] * len(SITUACOES))
    for oc in ocorrencias:
        i = CATEGORIAS.index(oc["categoria"])
        j = SITUACOES.index(oc["status"])
        matriz[i][j] += 1
    return matriz


def indicadores():
    total = len(ocorrencias)
    print("\n=== INDICADORES ===")
    if total == 0:
        print("Sem ocorrencias cadastradas.")
        return

    matriz = construir_matriz()

    print("\n[1] Ocorrencias por categoria")
    print("Regra: percentual = (qtd da categoria / total) * 100")
    for i in range(len(CATEGORIAS)):
        qtd = sum(matriz[i])
        print("  " + CATEGORIAS[i].ljust(16) + str(qtd).rjust(3)
              + "  (" + format(qtd / total * 100, ".1f") + "%)")

    print("\n[2] Ocorrencias por situacao")
    print("Regra: percentual = (qtd da situacao / total) * 100")
    for j in range(len(SITUACOES)):
        qtd = 0
        for i in range(len(CATEGORIAS)):
            qtd += matriz[i][j]
        print("  " + SITUACOES[j].ljust(16) + str(qtd).rjust(3)
              + "  (" + format(qtd / total * 100, ".1f") + "%)")

    print("\n[3] Matriz categoria x situacao")
    print("".ljust(16) + "".join(s.rjust(12) for s in SITUACOES))
    for i in range(len(CATEGORIAS)):
        print(CATEGORIAS[i].ljust(16) + "".join(str(v).rjust(12) for v in matriz[i]))

    print("\n[4] Tempo medio simulado de atendimento")
    print("Regra: media de (dia_conclusao - dia_abertura) das concluidas")
    soma = 0
    concluidas = 0
    for oc in ocorrencias:
        if oc["status"] == "concluida":
            duracao = int(oc["dia_conclusao"]) - int(oc["dia_abertura"])
            print("  ocorrencia " + oc["id"] + ": " + oc["dia_conclusao"] + " - "
                  + oc["dia_abertura"] + " = " + str(duracao) + " dias")
            soma += duracao
            concluidas += 1
    if concluidas > 0:
        print("  Media = " + str(soma) + " / " + str(concluidas) + " = "
              + format(soma / concluidas, ".1f") + " dias")
    else:
        print("  Nenhuma ocorrencia concluida ainda.")

    pendentes = total - concluidas
    print("\n[5] Pendencias")
    print("Regra: pendencias = total - concluidas = " + str(total) + " - "
          + str(concluidas) + " = " + str(pendentes))

    # Categoria com mais pendencias (conclusao breve)
    maior_qtd = -1
    maior_cat = ""
    for i in range(len(CATEGORIAS)):
        pend = matriz[i][0] + matriz[i][1]
        if pend > maior_qtd:
            maior_qtd = pend
            maior_cat = CATEGORIAS[i]
    print("\nConclusao: " + str(pendentes) + " de " + str(total)
          + " demandas seguem pendentes; a categoria com mais pendencias e '"
          + maior_cat + "' (" + str(maior_qtd) + ").")

    if len(rejeitados) > 0:
        print("\nAtencao: " + str(len(rejeitados))
              + " registro(s) do arquivo foram rejeitados e nao entram nos calculos.")


# ------------------------------------------------------------------
# 8. MENU PRINCIPAL
# ------------------------------------------------------------------
def mostrar_menu():
    print("\n===== PAINEL DE CONTROLE =====")
    print("1  - Listar ocorrencias")
    print("2  - Cadastrar ocorrencia")
    print("3  - Buscar por codigo")
    print("4  - Filtrar por categoria e/ou situacao")
    print("5  - Atualizar situacao")
    print("6  - Ver fila de demandas nao examinadas")
    print("7  - Ver ultimos eventos")
    print("8  - Ver hierarquia bairro > categoria")
    print("9  - Ver indicadores")
    print("10 - Ver registros rejeitados")
    print("0  - Sair")


def main():
    carregar_sistema()
    print("Dados carregados: " + str(len(ocorrencias)) + " ocorrencias validas, "
          + str(len(pilha_eventos)) + " eventos no historico.")
    for codigo, motivo in rejeitados:
        print("Registro " + (codigo if codigo != "" else "(sem codigo)")
              + " rejeitado na validacao: " + motivo + ".")

    while True:
        mostrar_menu()
        opcao = input("Escolha uma opcao: ").strip()
        if opcao == "1":
            listar(ocorrencias)
        elif opcao == "2":
            cadastrar()
        elif opcao == "3":
            buscar()
        elif opcao == "4":
            filtrar()
        elif opcao == "5":
            atualizar()
        elif opcao == "6":
            mostrar_fila()
        elif opcao == "7":
            mostrar_ultimos_eventos()
        elif opcao == "8":
            mostrar_hierarquia()
        elif opcao == "9":
            indicadores()
        elif opcao == "10":
            mostrar_rejeitados()
        elif opcao == "0":
            print("Encerrando. Ate logo!")
            break
        else:
            print("Opcao invalida. Digite um numero de 0 a 10.")


main()