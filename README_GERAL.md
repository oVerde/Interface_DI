# Interface DI - Sistema de Controle Gestual

Um sistema interativo de seleção de cenários e gestão de lobby multiplayer controlado por gestos, desenvolvido em Python com OpenCV e MediaPipe.

## 🎯 Funcionalidades

### Estados da Aplicação
- **SELECTOR**: Menu de seleção de cenários com carrossel animado
- **MULTIPLAYER_LOBBY**: Sala de espera para 5 jogadores com animação de carregamento
- **LOBBY**: Contagem regressiva de 3 segundos antes do jogo
- **VIEWER**: Tela do jogo (placeholder para lógica do jogo)

### Controles por Gesto
- **Braço Direito Levantado**: Avançar no carrossel de cenários
- **Braço Esquerdo Levantado**: Recuar no carrossel de cenários
- **Ambos os Braços Levantados**: Selecionar cenário (se desbloqueado)
- **BACKSPACE**: Voltar ao menu anterior
- **ENTER (no multiplayer lobby)**: Marcar jogador pronto

### Recursos Visuais
- Carrossel de cenários com transição suave (fade 0.5s)
- Indicadores de mapas bloqueados/desbloqueados
- 5 círculos para representar jogadores no lobby multiplayer
- Animação de carregamento com "..." (1, 2, 3 pontos ciclicamente)
- Interface em fullscreen com instruções visuais
- Fontes TTF (Roboto) para melhor qualidade de texto

## 📁 Estrutura do Projeto

```
Interface_DI/
├── main.py                    # Ponto de entrada, gerencia estados e loop principal
├── renderer.py                # Sistema de renderização de todos os estados
├── gesture_engine.py          # Detecção de gestos com MediaPipe
├── game_logic.py              # Classes stub para lógica do jogo
├── background_loader.py       # Carregamento de imagens de fundo
├── font_manager.py            # Gerenciamento de fontes TTF
├── lobby.py                   # Gerenciamento do countdown do lobby
├── fonts/                     # Fontes TTF
├── img/                       # Imagens dos cenários
│   ├── map1/background.png
│   ├── map2/background.png
│   └── map3/background.png
└── __pycache__/              # Cache de Python
```

## 🚀 Como Executar

### Requisitos
- Python 3.8+
- OpenCV: `pip install opencv-python`
- MediaPipe: `pip install mediapipe`
- Pillow: `pip install pillow`
- Webcam conectada

### Instalação
```bash
pip install -r requirements.txt
```

### Execução
```bash
python main.py
```

## 🔧 Configuração

### Câmera
- Resolução: 1280x720
- Flip automático para espelho (melhor UX)

### Detecção de Gesto
- Limiar de visibilidade: 0.3 (confidence)
- Cooldown entre gestos: 0.8 segundos
- Detecção: Posição do pulso acima do ombro

### Animações
- Transição de cenário: 500ms (easing cubic)
- Countdown do lobby: 3 segundos
- Loading dots: Ciclo de 0.4s por ponto (2.5x speed)

## 📊 Estados da Máquina

```
SELECTOR
    ↓ (SELECT + map não bloqueado)
MULTIPLAYER_LOBBY (espera 5 jogadores)
    ↓ (5 prontos ou countdown termina)
LOBBY (countdown 3s)
    ↓ (countdown termina)
VIEWER (jogo)
    ↓ (BACKSPACE)
SELECTOR
```

## 🎮 Cenários Disponíveis
1. **Paris** (desbloqueado)
2. **Berlim** (bloqueado)
3. **Amesterdão** (bloqueado)

## 📝 Notas Técnicas

### Renderização
- Todos os estados renderizados no `Renderer` class
- Suporte para animações via `time.time()`
- Textos com outline para melhor legibilidade
- Overlay semi-transparentes para UI elementos

### Detecção de Gestos
- Usa MediaPipe Pose para detecção de 33 landmarks
- Verifica visibilidade e posição dos landmarks
- Sistema de cooldown para evitar triggers múltiplos

### Fontes
- Usa PIL para renderizar fontes TTF no OpenCV
- Caching automático de fontes por tamanho
- Fallback para fontes padrão do OpenCV se necessário

## 🐛 Troubleshooting

**"ModuleNotFoundError: No module named 'cv2'"**
- Instale: `pip install opencv-python`

**Câmera não detectada**
- Verifique permissões da câmera
- Altere `cv2.VideoCapture(0)` para outro índice se necessário

**Texto muito pequeno/grande**
- Ajuste tamanho nas chamadas `_put_text_ttf()`

**Gestos não detectados**
- Aumentar iluminação
- Ajustar `visibility > 0.3` em `gesture_engine.py`

## 📦 Dependências

```
opencv-python>=4.8.0
mediapipe>=0.10.0
pillow>=10.0.0
numpy>=1.20.0
```

## 🎨 Customização

### Mudar Cenários
1. Adicione PNG em `img/map4/background.png`
2. Adicione nome em `InterfaceManager.maps`
3. Atualize lock status em `InterfaceManager.locked_maps`

### Ajustar Cores
- Busque valores BGR em `renderer.py` (OpenCV usa BGR, não RGB)
- Amarelo: `(255, 255, 0)`
- Vermelho: `(0, 0, 255)`
- Verde: `(0, 255, 0)`

### Modificar Timings
- Transition: `self.transition_duration`
- Countdown: `lobby_countdown_start` + 3 segundos
- Gesto cooldown: `self.last_gesture_time` em `gesture_engine.py`

## 👥 Arquitetura

### InterfaceManager (main.py)
- Gerencia estado da aplicação
- Processa eventos de gesto
- Coordena transições entre estados

### Renderer (renderer.py)
- Renderiza cada estado visualmente
- Gerencia animações e transições
- Coordena lobby multiplayer e countdown

### GestureEngine (gesture_engine.py)
- Processa frames da câmera
- Detecta landmarks com MediaPipe
- Reconhece padrões de gesto

### BackgroundLoader (background_loader.py)
- Carrega imagens dos cenários
- Gera placeholders se imagens faltarem
- Suporta PNG com alpha

## 📄 Licença

Projeto de interface para sistema DI.
