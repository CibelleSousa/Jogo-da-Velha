# Jogo da Velha Distribuído (Socket TCP)

## 1. Visão Geral e Propósito
Este software consiste em uma implementação multiplayer do clássico "Jogo da Velha", operando sobre uma arquitetura de sistema distribuído **Cliente-Servidor**.

O objetivo do projeto é demonstrar a sincronização de estado em tempo real entre duas máquinas distintas, garantindo consistência visual e lógica para ambos os jogadores através de sockets de rede. O sistema conta com uma interface gráfica (GUI) desenvolvida em **Pygame** e um servidor multithread capaz de gerenciar a lógica da partida e o roteamento de mensagens.

## 2. Requisitos e Dependências
Para executar este software, é necessário:
* **Linguagem:** Python 3.x (Testado na versão 3.12)
* **Bibliotecas:** `pygame` e `socket` (nativa).

Para instalar a dependência gráfica:
```bash
pip install pygame
```

## 3. Arquitetura e Arquivos
O projeto está modularizado em três arquivos principais:

* `server.py`: O "cérebro" da aplicação. Gerencia a matriz do tabuleiro, valida jogadas, detecta vitórias e retransmite estados para os clientes. Possui um Console de Administração local.
* `client.py`: A interface do usuário. Responsável apenas por renderizar o estado recebido do servidor e capturar os cliques do mouse. Não processa regras do jogo localmente.
* `theme.py`: Arquivo de configuração contendo constantes de cores, dimensões e taxas de atualização (FPS), facilitando a manutenção visual.

## 4. Instruções de Execução

### Passo 1: Iniciar o Servidor
Em uma máquina (ou terminal), execute:
```bash
python server.py
```
* O servidor escutará na porta 50000 em todos os interfaces de rede (0.0.0.0).
* **Comandos de Admin**: No terminal do servidor, digite `r` + Enter para reiniciar a partida forçadamente ou `q` + Enter para desligar o servidor.

### Passo 2: Configurar e Iniciar os Clientes
1. Abra o arquivo `client.py` em um editor de texto.
2. Localize a linha: `client.connect(('SEU_IP_AQUI', 50000))`.
    * Se for rodar tudo no mesmo PC, use `'127.0.0.1'`.
    * Se for rodar em PCs diferentes na mesma rede Wi-Fi, coloque o IPv4 da máquina onde o `server.py` está rodando (ex: `'192.168.0.15'`).
3. Execute o cliente em dois terminais diferentes:
```bash
python client.py
```
## 5. Motivação da Escolha do Protocolo de Transporte (TCP)
Foi selecionado o protocolo TCP (Transmission Control Protocol) para a camada de transporte.

**Justificativa**: O Jogo da Velha é uma aplicação sensível ao estado (State-Sensitive).
1. **Confiabilidade**: Diferente de um streaming de vídeo (UDP), não podemos tolerar a perda de pacotes. Se uma jogada for enviada e perdida na rede, o tabuleiro ficará dessincronizado, quebrando a integridade da partida.
2. **Ordenação**: É crucial que as jogadas cheguem na ordem exata. O TCP garante que se o Jogador A jogar antes do Jogador B, o servidor processará nessa ordem.

## 6. Documentação do Protocolo da Camada de Aplicação
O protocolo de aplicação é baseado em mensagens de texto (strings codificadas em UTF-8), facilitando o debug e a implementação.

### Estrutura das Mensagens
As mensagens seguem o padrão: `COMANDO <ARGUMENTOS>`

### A. Mensagens Servidor -> Cliente (Estados e Eventos)
Mensagem  | Descrição  | Exemplo
--------- | --------- | ---------
`ID <S>` | Define o símbolo do jogador ao conectar. `<S>` pode ser X, O. | `ID X` (Você é o X)
`ATT <T>` | Atualiza a matriz do tabuleiro. `<T>` é uma string de 9 caracteres representando as células. | `ATT X--O--X--`
`VEZ <S>` | Informa de quem é o turno atual. O cliente bloqueia cliques se não for sua vez. | `VEZ O`
`WIN <S>` | Informa o fim de jogo. `<S>` pode ser X, O ou V (Velha). | `WIN X`
`RESET` | Comando para limpar o tabuleiro e remover pop-ups de vitória. | `RESET`
`PEDIDO_REINICIO` | Informa que o oponente solicitou reiniciar a partida. Abre um pop-up de confirmação. | `PEDIDO_REINICIO `
`REINICIO_NEGADO` | Informa que o oponente recusou o pedido de reinício. | `REINICIO_NEGADO`

### B. Mensagens Cliente -> Servidor (Ações)
Mensagem  | Descrição  | Exemplo
--------- | --------- | ---------
`JOGAR <L> <C>` | Envia coordenada de clique (Linha, Coluna). O servidor valida se é legal. | `JOGAR 1 2`
`SOLICITAR_REINICIO` | Enviado quando o usuário clica em "Reiniciar". | `SOLICITAR_REINICIO`
`CONFIRMAR_REINICIO` | Enviado quando o usuário clica em "Aceitar" no pop-up de pedido. | `CONFIRMAR_REINICIO`
`NEGAR_REINICIO` | Enviado quando o usuário clica em "Recusar" no pop-up de pedido. | `NEGAR_REINICIO`

## 6. Autoria
Desenvolvido como requisito para a disciplina de Redes de Computadores por:

* Cibelle Sousa Rodrigues
* David Junio Mariano
* Laisa Pereira França