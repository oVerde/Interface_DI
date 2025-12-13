# Interface DI - Sistema Integrado de Seleção, Lobby e Jogo

Sistema completo de interface interativa com controle por gestos, integrando seletor de mapas (OpenCV), lobby multiplayer (Arcade) e cenário de jogo (Arcade).

## 🎯 Visão Geral

O projeto está dividido em três componentes principais que funcionam em sequência:

1. **Seletor de Mapas** (OpenCV + MediaPipe): Interface gestual para escolha de cenários
2. **Lobby Multiplayer** (Arcade): Detecção de até 5 jogadores com visualização de esqueletos
3. **Cenário de Jogo** (Arcade): Jogo em perspectiva com controle por gestos corporais

## 🚀 Instalação Rápida

### Requisitos
- Python 3.12+ (recomendado)
- Webcam conectada
- Windows (testado) / Linux / macOS

### Setup Automático
```bash
# Execute o script de instalação (Windows)
.\setup.ps1
```

O script irá:
- Detectar instalação do Python
- Instalar todas as dependências
- Configurar o ambiente automaticamente

### Setup Manual
```bash
# Instalar dependências
pip install -r requirements.txt

# Executar programa
python main.py
```

## 📁 Estrutura do Projeto

```
Interface_DI-main/
├── main.py                    # Ponto de entrada - Seletor → Lobby
├── gesture_engine.py          # Detecção de gestos MediaPipe (otimizado)
├── renderer.py                # Renderização do seletor
├── background_loader.py       # Carregamento de fundos
├── font_manager.py            # Fontes TTF (Roboto)
├── game_logic.py              # Lógica placeholder dos jogos
├── lobby.py                   # (não usado - legacy)
├── setup.ps1                  # Script de instalação Windows
├── requirements.txt           # Dependências Python
├── fonts/                     # Fontes TrueType
│   └── Roboto-VariableFont_wdth,wght.ttf
├── img/                       # Imagens dos cenários
│   ├── map1/background.png    # Paris
│   ├── map2/background.png    # Berlim
│   └── map3/background.png    # Amesterdão
└── Projeto-DI-main/          # Sistema Arcade (Lobby + Jogo)
    └── poseCenario/
        ├── lobby_test.py      # Lobby multiplayer (5 jogadores)
        ├── colega.py          # Cenário de jogo em perspectiva
        └── ...
```

## 🎮 Como Usar

### Fluxo Completo
```
1. SELETOR (OpenCV)
   └─> Gestos: Braço direito (próximo), esquerdo (anterior), ambos (selecionar)
   
2. LOBBY (Arcade)
   └─> Detecta até 5 jogadores, visualiza esqueletos em slots
   └─> Gesto: Manter mão levantada ou swipe para iniciar
   
3. CENÁRIO (Arcade)
   └─> Jogo em perspectiva com elementos dinâmicos
   └─> Controle por movimentos corporais
```

### Controles - Seletor
- **Braço Direito Levantado**: Próximo mapa
- **Braço Esquerdo Levantado**: Mapa anterior
- **Ambos os Braços**: Selecionar (se desbloqueado)
- **ESC**: Sair

### Controles - Lobby
- **Mão Levantada (2s)**: Iniciar jogo
- **Swipe**: Iniciar jogo imediatamente
- **ESC**: Sair

### Controles - Cenário
- **Movimentos Corporais**: Controlar personagem
- **ESC**: Sair

## ⚙️ Otimizações de Performance

### Processamento de Gestos
- **Modelo MediaPipe**: `model_complexity=0` (mais rápido)
- **Skip frames**: Processa gestos a cada 2 frames
- **Confiança**: 0.6 (balanceado entre precisão e velocidade)
- **GPU**: Suporte automático CUDA/DirectML se disponível

### Câmera
- **Resolução**: 640x480 (otimizado para performance)
- **FPS**: 30 (padrão)
- **Buffer**: 1 frame (reduz latência)
- **Backends**: DirectShow (preferencial) → Media Foundation → Auto

### Renderização
- **Operações NumPy diretas**: Evita cópias desnecessárias
- **Fontes**: Renderização apenas da região de texto
- **Arcade**: Fullscreen para melhor desempenho

## 🔧 Configuração Técnica

### Seletor (OpenCV)
- Resolução fullscreen: 1280x720
- Flip horizontal automático (modo espelho)
- Transição suave entre mapas
- Detecção de gestos com cooldown 0.8s

### Lobby (Arcade)
- Fullscreen nativo
- Detecção de até 5 pessoas simultâneas
- Slots: 5 posições com escalonamento em profundidade
- Smoothing: 5 frames para suavizar movimentos
- Tempo de hold: 2 segundos para iniciar

### Cenário (Arcade)
- Fullscreen
- Background em perspectiva
- Elementos dinâmicos (árvores, pássaros, carros)
- Spawning baseado em milestones

## 📦 Dependências

```txt
opencv-python>=4.12.0.88    # Processamento de vídeo e gestos
mediapipe>=0.10.14          # Detecção de pose/landmarks
numpy>=2.2.0                # Operações matemáticas
Pillow>=11.3.0              # Renderização de fontes TTF
arcade>=2.6.0               # Engine de jogo para lobby/cenário
```

**Nota**: Pillow 12.0.0 tem incompatibilidade com Arcade. Use 11.3.0.

## 🐛 Troubleshooting

### Câmera não funciona
```bash
# Testar câmera manualmente
python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'ERRO')"
```
- Verificar permissões da câmera no Windows
- Testar índices diferentes: 0, 1, 2
- Verificar se outra aplicação está usando a câmera

### Erro "No module named..."
```bash
# Reinstalar dependências
pip install -r requirements.txt
```

### Performance lenta
- Verificar se está usando GPU: Mensagem "✓ GPU CUDA detectada" no início
- Fechar outras aplicações que usam câmera
- Reduzir resolução em `gesture_engine.py` se necessário

### Fontes não aparecem
- Verificar se pasta `fonts/` existe
- Roboto-VariableFont_wdth,wght.ttf deve estar presente
- Fallback para fontes OpenCV padrão se ausente

### Lobby não detecta jogadores
- Melhorar iluminação
- Afastar-se para ficar no enquadramento completo
- Verificar se câmera tem boa qualidade

## 🎨 Customização

### Adicionar Novo Mapa
1. Criar pasta `img/map4/`
2. Adicionar `background.png` (1920x1080 recomendado)
3. Editar `main.py`:
   ```python
   self.maps = ["Paris", "Berlim", "Amesterdão", "NovoMapa"]
   self.locked_maps = [1, 2, 3]  # Índices bloqueados
   ```

### Ajustar Sensibilidade de Gestos
Em `gesture_engine.py`:
```python
# Linha ~30
min_detection_confidence=0.6,  # Aumentar para mais precisão
min_tracking_confidence=0.6,   # Aumentar para menos falsos positivos
```

### Modificar Tempo de Hold no Lobby
Em `lobby_test.py`:
```python
# Linha ~52
self.gesture_hold_duration = 2.0  # Segundos
```

## 📊 Fluxo de Dados

```
[Câmera] → [MediaPipe] → [GestureEngine] → [InterfaceManager]
                                                    ↓
                                            [Subprocess]
                                                    ↓
                                            [lobby_test.py]
                                                    ↓
                                            [Subprocess]
                                                    ↓
                                            [colega.py]
```

### Comunicação entre Componentes
- **Seletor → Lobby**: Subprocess (`python lobby_test.py`)
- **Lobby → Cenário**: Subprocess (`python colega.py <num_jogadores>`)
- **Dados compartilhados**: Número de jogadores via argumento de linha de comando

## 🔍 Arquitetura de Código

## 🔍 Arquitetura de Código

### main.py - InterfaceManager
**Responsabilidades**:
- Gerenciar estado do seletor de mapas
- Processar gestos do usuário
- Renderizar interface OpenCV
- Lançar subprocess para lobby

**Principais métodos**:
- `open_camera()`: Multi-backend camera detection
- `run()`: Loop principal com detecção de gestos
- `launch_lobby()`: Subprocess para Arcade lobby

### gesture_engine.py - GestureEngine
**Responsabilidades**:
- Inicializar MediaPipe Holistic
- Processar frames da câmera
- Detectar gestos (braços levantados)
- Cooldown para evitar múltiplos triggers

**Otimizações**:
- `model_complexity=0`: Modelo leve
- `min_detection_confidence=0.6`
- `enable_segmentation=False`
- GPU automático se disponível

### renderer.py - Renderer
**Responsabilidades**:
- Renderizar UI do seletor
- Desenhar títulos de mapas
- Indicadores de bloqueio
- Instruções de controle
- Setas de navegação animadas

**Componentes**:
- FontManager para TTF rendering
- Operações NumPy diretas (performance)
- Alpha blending para overlay

### background_loader.py - BackgroundLoader
**Responsabilidades**:
- Carregar imagens de fundo dos mapas
- Redimensionar para resolução target
- Gerar placeholders se imagem ausente

### font_manager.py - FontManager
**Responsabilidades**:
- Carregar fontes TrueType (Roboto)
- Cache de fontes por tamanho
- Renderizar texto com PIL
- Converter para formato OpenCV
- Calcular bounding boxes

**Otimização**:
- Renderiza apenas região de texto
- Cache previne recarregamentos

### lobby_test.py - LobbyWindow (Arcade)
**Responsabilidades**:
- Detectar até 5 jogadores
- Visualizar esqueletos em slots
- Processar gestos de início
- Lançar subprocess para cenário

**Componentes**:
- PoseTracker para multi-person detection
- 5 slots com escalonamento em profundidade
- Smoothing de poses
- Detecção de swipe

### colega.py - PerspectivaWindow (Arcade)
**Responsabilidades**:
- Renderizar cenário em perspectiva
- Gerenciar elementos dinâmicos
- Controle por movimentos corporais
- Sistema de pontuação

**Elementos**:
- Background em perspectiva
- Árvores laterais
- Pássaros
- Carros
- Elemento fixo central

## 🎯 Mapas Disponíveis

| Mapa | Status | Descrição |
|------|--------|-----------|
| Paris | 🔓 Desbloqueado | Cenário urbano francês |
| Berlim | 🔒 Bloqueado | Cenário urbano alemão |
| Amesterdão | 🔒 Bloqueado | Cenário urbano holandês |

## 📈 Performance

### Benchmarks (em hardware típico)
- **Seletor**: ~30 FPS (640x480, gestos a cada 2 frames)
- **Lobby**: ~60 FPS (fullscreen, 5 jogadores)
- **Cenário**: ~60 FPS (fullscreen, elementos dinâmicos)

### Requisitos de Hardware
**Mínimo**:
- CPU: Dual-core 2.0 GHz
- RAM: 4 GB
- Webcam: 480p @ 30fps

**Recomendado**:
- CPU: Quad-core 2.5 GHz+
- RAM: 8 GB
- GPU: NVIDIA/AMD com suporte DirectML ou CUDA
- Webcam: 720p @ 30fps

## 🔐 Segurança e Privacidade

- **Câmera**: Processamento local, sem upload
- **Dados**: Nenhum dado pessoal coletado ou armazenado
- **Rede**: Não requer conexão (offline)

## 📝 Changelog

### Versão Atual
- ✅ Integração completa Seletor → Lobby → Cenário
- ✅ Otimização de performance (3-4x mais rápido)
- ✅ Multi-backend camera detection
- ✅ Suporte GPU (CUDA/DirectML)
- ✅ Fullscreen em todas as janelas
- ✅ Sistema de subprocess para transições
- ✅ Detecção multi-pessoa (até 5)
- ✅ Smoothing de movimentos
- ✅ Setup script automatizado

## 🤝 Contribuição

Para modificar ou estender o projeto:

1. **Adicionar gestos**: Editar `gesture_engine.py` → método `detect_gesture()`
2. **Novos mapas**: Adicionar em `img/mapX/background.png` + atualizar `main.py`
3. **Lobby customizado**: Modificar `lobby_test.py` → classe `LobbyWindow`
4. **Cenário**: Editar `colega.py` → classe `PerspectivaWindow`

## 📄 Licença

Projeto educacional para Interface Digital Interativa.

---

**Desenvolvido com** ❤️ **usando Python, OpenCV, MediaPipe e Arcade**
