# Interface_DI – Guia de Execução (Windows)

Este README explica exatamente o que é preciso para instalar, configurar e executar o ficheiro `main.py` deste projeto no Windows.

## Requisitos
- Python 3.12.8 (recomendado 64-bit)
- Webcam integrada ou USB
- Permissões para aceder à câmara no Windows

## Dependências Python
Instale os seguintes pacotes:
- opencv-python
- mediapipe
- numpy
- pillow

Opcional (já incluído no projeto):
- Fonte `fonts/Roboto-VariableFont_wdth,wght.ttf` para melhor renderização de texto. Caso não exista, o programa usa a fonte padrão do OpenCV.

## Estrutura esperada
- `img/map1/background.png`
- `img/map2/background.png`
- `img/map3/background.png`
Se estes ficheiros não existirem, serão mostrados placeholders.

## Passo a passo (recomendado)
1) Setup automático com Python 3.12
```powershell
.# cria venv com Python 3.12 (via py launcher)
 .\setup.ps1 -PySpec 3.12
 # ativar venv se necessário
 .\.venv\Scripts\Activate.ps1
 # executar
 python .\main.py
```

2) Alternativa manual (com Python 3.12 ativo)
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
py -3.12 -m pip install --upgrade pip
pip install -r requirements.txt
python .\main.py
```

## Como funciona
- O programa abre uma janela fullscreen chamada "Interactive Project Python" e usa a webcam.
- Reconhece gestos com o corpo via MediaPipe:
  - Braço esquerdo levantado: PREV (voltar)
  - Braço direito levantado: NEXT (avançar)
  - Ambos os braços levantados: SELECT (selecionar)
- Estados da interface:
  - `SELECTOR`: Carrossel de mapas (Paris, Berlim, Amesterdão). Alguns mapas podem estar bloqueados.
  - `MULTIPLAYER_LOBBY`: Simula confirmação de jogadores até 5; inicia contagem quando todos estão prontos.
  - `LOBBY`: Contagem de 3 segundos antes de entrar no modo `VIEWER`.
  - `VIEWER`: Atualização do jogo selecionado (placeholders em `game_logic.py`).

## Controles no teclado
- `Esc`: sair do programa.
- `Backspace`: voltar para `SELECTOR` quando estiver em `VIEWER`, `MULTIPLAYER_LOBBY` ou `LOBBY`.
- `Enter`: marcar um jogador como pronto na `MULTIPLAYER_LOBBY`.

## Resolução e câmara
- O programa define a câmara para 1280x720 (`cap.set(3, 1280)` e `cap.set(4, 720)`). Nem todas as webcams suportam exatamente esta resolução; se não suportar, o driver ajusta automaticamente.

## Problemas comuns e soluções
- Janela abre mas não há vídeo:
  - Verifique permissões da câmara no Windows: Definições > Privacidade e segurança > Câmara.
  - Feche outras apps que usem a câmara (Teams/Zoom/OBS).
- `mediapipe` falha ao instalar:
  - Garanta Python 64-bit e `pip` atualizado.
  - Tente `pip install --upgrade setuptools wheel` antes das dependências.
- Texto com fonte estranha:
  - Confirme que existe o ficheiro `fonts/Roboto-VariableFont_wdth,wght.ttf`. Caso contrário, o programa usa a fonte padrão.
- Backgrounds não aparecem:
  - Crie os diretórios `img/map1`, `img/map2`, `img/map3` e adicione `background.png` em cada um (qualquer imagem PNG). Caso contrário, verá um placeholder.

## Ficheiros principais
- `main.py`: ponto de entrada, loop principal, gestão de estados e eventos.
- `gesture_engine.py`: processamento de frames e deteção de gestos com MediaPipe.
- `renderer.py`: renderização da interface, transições e lobbies; usa `font_manager.py`.
- `background_loader.py`: carrega os backgrounds por mapa, com placeholders.
- `game_logic.py`: lógica dos jogos (atualmente placeholders `Map1Game`, `Map2Game`, `Map3Game`).
- `lobby.py`: utilitário para estados/contagem (algumas funções usadas via `renderer`).

## Dicas
- Iluminação uniforme ajuda o MediaPipe a detetar bem os braços.
- Mantenha o corpo visível na frame da câmara.
- Evite movimentos demasiado rápidos — há um cooldown de ~0.8s para evitar gestos repetidos.

## Comandos rápidos
```powershell
# Setup automático (3.12)
.\setup.ps1 -PySpec 3.12
# Ativar venv
.\.venv\Scripts\Activate.ps1
# Executar
python .\main.py
```

---
Se quiser, posso gerar um `requirements.txt` e automatizar a criação do ambiente.