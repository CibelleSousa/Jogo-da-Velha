import sys
import socket
import threading
import theme
import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1" # REMOVER MENSAGEM PADRÃO DO PYGAME
import pygame


# CONFIGURAR A REDE
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client.connect(('10.0.0.10', 50000))
except:
    print('Não foi possível conectar ao servidor.')
    sys.exit()

pygame.init()

# CRIAR JANELA
tela = pygame.display.set_mode((theme.LARGURA, theme.ALTURA_TOTAL))
pygame.display.set_caption('Jogo da Velha')
clock = pygame.time.Clock()

# FONTES
fonte_simbolo = pygame.font.SysFont("arial", 100, bold=True)
fonte_ui = pygame.font.SysFont("arial", 24)
fonte_popup_titulo = pygame.font.SysFont("arial", 40, bold=True) 
fonte_popup_solicitacao = pygame.font.SysFont("arial", 20, bold=True) 
fonte_popup_nome = pygame.font.SysFont("arial", 35)

# ESTADO DO JOGO
tabuleiro = [[None]*3 for _ in range(3)]
meu_simbolo = None
jogador_atual = 'X'
game_over = False
vencedor_nome = None
running = True
disconnect_reason = None

# ESTADOS DE UX
popup_pedido_reinicio = False # Se True, mostra texto "Aguardando oponente..."
aguardando_resposta = False   # Se True, mostra texto "Aguardando oponente..."
popup_oponente_desconectou = False # Se True, mostra texto "Oponente desconectou"

# RETÂNGULOS DE UI
rect_botao_main = pygame.Rect(0, 0, 140, 40)
y_base_ui = theme.BARRA_SUPERIOR + theme.ALTURA
rect_botao_main.center = (theme.LARGURA // 2, y_base_ui + 150)

# POPUP VENCEDOR
rect_btn_jogar_novo = pygame.Rect(0, 0, 200, 50)

# POPUP PEDIDO REINICIO (SIM/NAO)
rect_btn_sim = pygame.Rect(0, 0, 100, 40)
rect_btn_nao = pygame.Rect(0, 0, 100, 40)

# COMUNICAR COM SERVIDOR
def receber_mensagem():
    global tabuleiro, jogador_atual, meu_simbolo, game_over, vencedor_nome, popup_pedido_reinicio, aguardando_resposta, running, disconnect_reason, popup_oponente_desconectou
    while True:
        try:
            msg = client.recv(4096).decode()
            if not msg:
                disconnect_reason = "Servidor fechou a conexão (lotado ou indisponível)."
                running = False
                break
            if "ID" in msg:
                partes = msg.split("ID ")
                if len(partes) > 1:
                    meu_simbolo = partes[1][0]
            if "ATT" in msg:
                inicio = msg.find("ATT ") + 4
                dados = msg[inicio : inicio+9]
                index = 0
                for linha in range(3):
                    for coluna in range(3):
                        char = dados[index]
                        tabuleiro[linha][coluna] = char if char != '-' else None
                        index += 1
            if "VEZ" in msg:
                inicio = msg.find("VEZ ") + 4
                jogador_atual = msg[inicio]
            if "WIN" in msg:
                inicio = msg.find("WIN ") + 4
                vencedor_codigo =  msg[inicio]
                game_over = True
                vencedor_nome = 'Empate' if vencedor_codigo == 'V' else f"Jogador {vencedor_codigo}"
            if "RESET" in  msg:
                if not popup_oponente_desconectou:
                    game_over = False
                    vencedor_nome = None
                    popup_pedido_reinicio = False
                    aguardando_resposta = False
            if "PEDIDO_REINICIO" in msg:
                popup_pedido_reinicio = True
            if "REINICIO_NEGADO" in msg:
                aguardando_resposta = False
                print("Oponente negou reinicio da partida.")
            if "OPONENTE_DESCONECTOU" in msg:
                game_over = True
                vencedor_nome = "Oponente desconectou"
                popup_pedido_reinicio = False
                aguardando_resposta = False
                popup_oponente_desconectou = True
                continue
        except Exception as e:
            print(f"Erro ao receber dados: {e}")
            running = False
            break

thread_rede = threading.Thread(target=receber_mensagem, daemon=True)
thread_rede.start()

# DESENHAR LINHAS
def desenhar_linhas():
    offset_y = theme.BARRA_SUPERIOR
    pygame.draw.line(tela, theme.PRETO, (theme.QUADRANTE, offset_y), (theme.QUADRANTE, offset_y + theme.ALTURA), theme.ESPESSURA_LINHA)
    pygame.draw.line(tela, theme.PRETO, (theme.QUADRANTE*2, offset_y), (theme.QUADRANTE*2, offset_y + theme.ALTURA), theme.ESPESSURA_LINHA)
    pygame.draw.line(tela, theme.PRETO, (0, offset_y + theme.QUADRANTE), (theme.LARGURA, offset_y + theme.QUADRANTE), theme.ESPESSURA_LINHA)
    pygame.draw.line(tela, theme.PRETO, (0, offset_y + theme.QUADRANTE*2), (theme.LARGURA, offset_y + theme.QUADRANTE*2), theme.ESPESSURA_LINHA)
    # pygame.draw.line(tela, theme.CINZA, (0, theme.ALTURA), (theme.LARGURA, theme.ALTURA), 5)

# DESENHAR SÍMBOLO
def desenhar_simbolo():
    offset_y = theme.BARRA_SUPERIOR
    for linha in range(3):
        for coluna in range(3):
            if tabuleiro[linha][coluna] is not None:
                cor = theme.AZUL if tabuleiro[linha][coluna] == 'X' else theme.VERMELHO
                texto = fonte_simbolo.render(tabuleiro[linha][coluna], True, cor)
                centro_x = coluna * theme.QUADRANTE + theme.QUADRANTE // 2
                centro_y = linha * theme.QUADRANTE + theme.QUADRANTE // 2 + offset_y
                rect_texto = texto.get_rect(center = (centro_x, centro_y))
                tela.blit(texto, rect_texto)

# DESENHAR UI
def desenhar_ui():
    y_base = theme.BARRA_SUPERIOR + theme.ALTURA
    nome_jogador = "Jogador 1" if jogador_atual == 'X' else "Jogador 2"
    texto_vez = fonte_ui.render(f"Vez do {nome_jogador}", True, theme.PRETO)
    tela.blit(texto_vez, (20, y_base + 20))

    if meu_simbolo:
        texto_sou = fonte_ui.render(f"Você joga com {meu_simbolo}", True, theme.AZUL if meu_simbolo == 'X' else theme.VERMELHO)
        rect_sou = texto_sou.get_rect(topright=(theme.LARGURA - 20, y_base + 20))
        tela.blit(texto_sou, rect_sou)
    
    txt_legenda = fonte_ui.render("Jogador 1 = X | Jogador 2 = O", True, theme.PRETO)
    tela.blit(txt_legenda, (20, y_base + 55))

    if not game_over and not popup_pedido_reinicio:
        if aguardando_resposta:
            # Mostra texto de espera no lugar do botão
            txt_wait = fonte_ui.render("Aguardando oponente...", True, theme.CINZA)
            r_wait = txt_wait.get_rect(center=rect_botao_main.center)
            tela.blit(txt_wait, r_wait)
        else:
            pygame.draw.rect(tela, theme.CINZA2, rect_botao_main, border_radius=10)
            pygame.draw.rect(tela, theme.PRETO, rect_botao_main, 2, border_radius=10)
            txt_btn = fonte_ui.render("Reiniciar", True, theme.PRETO)
            tela.blit(txt_btn, txt_btn.get_rect(center=rect_botao_main.center))

# DESENHAR POPUP's
def desenhar_popups():
    s = pygame.Surface((theme.LARGURA, theme.ALTURA_TOTAL))
    s.set_alpha(180)
    s.fill((255,255,255))
    tela.blit(s, (0,0))

    centro_x, centro_y = theme.LARGURA // 2, theme.ALTURA_TOTAL // 2

    if popup_oponente_desconectou:
        rect_box = pygame.Rect(0, 0, 400, 200)
        rect_box.center = (centro_x, centro_y)
        pygame.draw.rect(tela, theme.PRETO, rect_box, border_radius=20)
        pygame.draw.rect(tela, theme.BRANCO, rect_box.inflate(-10,-10), border_radius=20)

        t_tit = fonte_popup_titulo.render("Fim de Jogo!", True, theme.PRETO)
        tela.blit(t_tit, t_tit.get_rect(center=(centro_x, centro_y - 40)))

        t_nome = fonte_popup_nome.render("Oponente desconectou!", True, theme.VERMELHO)
        tela.blit(t_nome, t_nome.get_rect(center=(centro_x, centro_y)))

        rect_btn_jogar_novo.center = (centro_x, centro_y + 60)
        pygame.draw.rect(tela, theme.CINZA2, rect_btn_jogar_novo, border_radius=10)
        pygame.draw.rect(tela, theme.PRETO, rect_btn_jogar_novo, 2, border_radius=10)
        t_btn = fonte_ui.render("OK", True, theme.PRETO)
        tela.blit(t_btn, t_btn.get_rect(center=rect_btn_jogar_novo.center))
        return  # sai da função, não desenha outros popups
    
    if popup_pedido_reinicio:
        rect_box = pygame.Rect(0, 0, 315, 140)
        rect_box.center = (centro_x, centro_y)
        pygame.draw.rect(tela, theme.PRETO, rect_box, border_radius=15)
        pygame.draw.rect(tela, theme.BRANCO, rect_box.inflate(-6,-6), border_radius=15)

        txt_p = fonte_popup_solicitacao.render("Oponente quer reiniciar.", True, theme.PRETO)
        tela.blit(txt_p, txt_p.get_rect(center=(centro_x, centro_y - 40)))

        # Botões Sim / Não
        rect_btn_sim.center = (centro_x - 70, centro_y + 28)
        rect_btn_nao.center = (centro_x + 70, centro_y + 28)

        pygame.draw.rect(tela, theme.VERDE_CLARO, rect_btn_sim, border_radius=8)
        pygame.draw.rect(tela, theme.PRETO, rect_btn_sim, 2, border_radius=8)
        t_sim = fonte_ui.render("Aceitar", True, theme.PRETO)
        tela.blit(t_sim, t_sim.get_rect(center=rect_btn_sim.center))

        pygame.draw.rect(tela, theme.VERMELHO_CLARO, rect_btn_nao, border_radius=8)
        pygame.draw.rect(tela, theme.PRETO, rect_btn_nao, 2, border_radius=8)
        t_nao = fonte_ui.render("Recusar", True, theme.PRETO)
        tela.blit(t_nao, t_nao.get_rect(center=rect_btn_nao.center))

    elif game_over:
        rect_box = pygame.Rect(0, 0, 400, 250)
        rect_box.center = (centro_x, centro_y)
        pygame.draw.rect(tela, theme.PRETO, rect_box, border_radius=20)
        pygame.draw.rect(tela, theme.BRANCO, rect_box.inflate(-10, -10), border_radius=20)

        t_tit = fonte_popup_titulo.render("Fim de Jogo!", True, theme.PRETO)
        tela.blit(t_tit, t_tit.get_rect(center=(centro_x, centro_y - 60)))

        # Texto e botão baseado no vencedor
        if vencedor_nome == "Empate":
            texto_final = "Deu Velha!"
            cor_v = theme.PRETO
            texto_botao = "Jogar Novamente"
        else:
            texto_final = f"{vencedor_nome} venceu!"
            cor_v = theme.VERDE_ESCURO
            texto_botao = "Jogar Novamente"

        t_nome = fonte_popup_nome.render(texto_final, True, cor_v)
        tela.blit(t_nome, t_nome.get_rect(center=(centro_x, centro_y - 10)))

        rect_btn_jogar_novo.center = (centro_x, centro_y + 60)
        pygame.draw.rect(tela, theme.CINZA2, rect_btn_jogar_novo, border_radius=10)
        pygame.draw.rect(tela, theme.PRETO, rect_btn_jogar_novo, 2, border_radius=10)
        t_btn = fonte_ui.render(texto_botao, True, theme.PRETO)
        tela.blit(t_btn, t_btn.get_rect(center=rect_btn_jogar_novo.center))


# MAIN
while running:
    if meu_simbolo:
        pygame.display.set_caption(f"Jogo da Velha - Você joga com {meu_simbolo}")
    mouse_pos = pygame.mouse.get_pos()
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if evento.type == pygame.MOUSEBUTTONDOWN:
            if popup_pedido_reinicio:
                if rect_btn_sim.collidepoint(mouse_pos):
                    client.send("CONFIRMAR_REINICIO".encode())
                    popup_pedido_reinicio = False
                elif rect_btn_nao.collidepoint(mouse_pos):
                    client.send("NEGAR_REINICIO".encode())
                    popup_pedido_reinicio = False
            elif game_over:
                if vencedor_nome == "Oponente desconectou" and rect_btn_jogar_novo.collidepoint(mouse_pos):
                    popup_oponente_desconectou = False
                    game_over = False
                    vencedor_nome = None
                    popup_pedido_reinicio = False
                    aguardando_resposta = False
                elif rect_btn_jogar_novo.collidepoint(mouse_pos):
                    client.send("SOLICITAR_REINICIO".encode())
                    aguardando_resposta = True
            else:
                if rect_botao_main.collidepoint(mouse_pos):
                    client.send("SOLICITAR_REINICIO".encode())
                    aguardando_resposta = True
                elif not game_over:
                    x, y = mouse_pos
                    if theme.BARRA_SUPERIOR < y < (theme.BARRA_SUPERIOR + theme.ALTURA):
                        coluna = x // theme.QUADRANTE
                        linha = (y - theme.BARRA_SUPERIOR) // theme.QUADRANTE

                        if tabuleiro[linha][coluna] is None:
                            msg = f'JOGAR {linha} {coluna}'
                            client.send(msg.encode())
    tela.fill(theme.BRANCO)
    desenhar_linhas()
    desenhar_simbolo()
    desenhar_ui()
    if game_over or popup_pedido_reinicio:
        desenhar_popups()
    pygame.display.update()
    clock.tick(theme.FPS)

try:
    client.close()
except:
    pass

# opcional: mostrar mensagem final no terminal ou num popup simples antes de sair
if disconnect_reason:
    print(disconnect_reason)

pygame.quit()
sys.exit()
