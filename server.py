import socket
import threading
import time
import os

# CONFIGURAÇÕES DE REDE
HOST = '0.0.0.0'
PORT = 50000

# ESTADO DO JOGO
tabuleiro = [[None]*3 for _ in range(3)]
jogador_atual = 'X'
clientes = []
simbolos_disponiveis = ['X', 'O']


# VERIFICAR O VENCEDOR
def verificar_vencedor():
    for i in range(3):
        if tabuleiro[i][0] == tabuleiro[i][1] == tabuleiro[i][2] and tabuleiro[i][0]:
            return tabuleiro[i][0]
        if tabuleiro[0][i] == tabuleiro[1][i] == tabuleiro[2][i] and tabuleiro[0][i]:
            return tabuleiro[0][i]
    if tabuleiro[0][0] == tabuleiro[1][1] == tabuleiro[2][2] and tabuleiro[0][0]:
        return tabuleiro[0][0]
    if tabuleiro[0][2] == tabuleiro[1][1] == tabuleiro[2][0] and tabuleiro[0][2]:
        return tabuleiro[0][2]
    if all(all(celula is not None for celula in linha) for linha in tabuleiro):
        return "V"
    return None

# CONVERTER MATRIZ EM STRING ÚNICA
def tabuleiro_para_string():
    string = ''
    for linha in range(3):
        for coluna in range(3):
            valor = tabuleiro[linha][coluna]
            string += valor if valor else '-'
    return string

# ENVIAR MENSAGEM PARA TODOS OS CLIENTES
def broadcast(mensagem: str):
    for cliente in clientes:
        try:
            cliente.send(mensagem.encode())
        except:
            pass

# ENVIAR PEDIDO PARA O OPONENTE
def enviar_para_oponente(remetente, msg: str):
    for cliente in clientes:
        if cliente != remetente:
            try: 
                cliente.send(msg.encode())
            except: 
                pass

# REINICIAR O JOGO
def reiniciar_jogo():
    global tabuleiro, jogador_atual
    tabuleiro = [[None]*3 for _ in range(3)]
    jogador_atual = 'X'
    broadcast(f"RESET")
    broadcast(f"ATT {tabuleiro_para_string()}")
    broadcast(f"VEZ X")

# ADMINISTRAR O SERVIDOR VIA TERMINAL
def console_admin():
    print("-" * 30)
    print(" COMANDOS DE ADMINISTRAÇÃO:")
    print(" [r] + Enter -> Reiniciar Jogo")
    print(" [q] + Enter -> Desligar Servidor")
    print("-" * 30)

    while True:
        try:
            cmd = input() # Fica esperando você digitar no terminal do servidor
            if cmd.strip().lower() == 'q':
                print("[ADMIN] Desligando servidor...")
                # Fecha conexões antes de sair
                for cliente in clientes:
                    try: 
                        cliente.close()
                    except: 
                        pass
                os._exit(0) # Mata o processo imediatamente
            elif cmd.strip().lower() == 'r':
                print("[ADMIN] Reiniciando partida forçadamente...")
                reiniciar_jogo()
        except:
            pass

# LIDAR COM CLIENTE
def handle_client(conn, addr, simbolo: str):
    global jogador_atual
    print(f"Novo jogador conectado: {simbolo} em {addr}")

    conn.send(f"ID {simbolo}".encode()) # envia qual símbolo cada jogador é
    time.sleep(0.1)
    conn.send(f"ATT {tabuleiro_para_string()}".encode()) # estado atual do tabuleiro
    time.sleep(0.1)
    conn.send(f"VEZ {jogador_atual}".encode()) # envia de quem é a vez

    while True:
        try:
            msg: str = conn.recv(1024).decode()
            if not msg:
                break

            if msg.startswith("JOGAR"):
                _, linha, coluna = msg.split()
                linha, coluna = int(linha), int(coluna)

                if jogador_atual == simbolo and tabuleiro[linha][coluna] is None:
                    tabuleiro[linha][coluna] = simbolo
                    vencedor = verificar_vencedor()
                    broadcast(f"ATT {tabuleiro_para_string()}")

                    if vencedor:
                        broadcast(f"WIN {vencedor}")
                    else:
                        jogador_atual = 'O' if simbolo == 'X' else 'X'
                        broadcast(f"VEZ {jogador_atual}")
            elif msg == 'SOLICITAR_REINICIO':
                if len(clientes) < 2:
                    # Menos de 2 jogadores, não há oponente para reinício
                    conn.send("REINICIO_NEGADO".encode())
                else:
                    enviar_para_oponente(conn, "PEDIDO_REINICIO")
            elif msg == 'CONFIRMAR_REINICIO':
                reiniciar_jogo()
            elif msg == 'NEGAR_REINICIO':
                enviar_para_oponente(conn, "REINICIO_NEGADO")
        except Exception as e:
            print(f'Erro na conexão com {simbolo}')
            break
    
    # REMOVE DA LISTA
    if conn in clientes:
        clientes.remove(conn)
    
    # DEVOLVE SIMBOLO PARA A FILA
    simbolos_disponiveis.append(simbolo)

    # AVISAR O OPONENTE
    enviar_para_oponente(conn, "OPONENTE_DESCONECTOU")
    conn.close()
    reiniciar_jogo()


# OBTER IP DA REDE

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # ipv4 e udp
        # não precisa existir — só serve para descobrir a rota padrão
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1" # localhost

# INICIALIZAR O SERVIDOR
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # ipv4 e tcp
server.bind((HOST, PORT))
server.listen(2) # no máximo dois clientes
print(f'Servidor rodando em {get_local_ip()}:{PORT}')
# INICIAR A THREAD DE ADMINISTRAÇÃO
threading.Thread(target=console_admin, daemon=True).start()


while True:
    
    conn, addr = server.accept()

    if not simbolos_disponiveis:
        # Servidor lotado, então rejeita a conexão
        conn.close()
        print(f"Conexão recusada de {addr}")
        continue
    
    simbolo = simbolos_disponiveis.pop(0)
    clientes.append(conn)

    thread = threading.Thread(target=handle_client, args=(conn, addr, simbolo)) # cria um processo paralelo para cada cliente
    thread.start()
