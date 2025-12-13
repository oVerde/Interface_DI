# ReadmeToce - Guia de Integração Backend e Mecânicas

Instruções completas para integrar backend, lógica de jogo e mecânicas necessárias ao sistema de interface.

## 📋 Visão Geral da Integração

Este documento fornece um roadmap detalhado para expandir a interface atual com:
1. **Backend de Servidor** (API REST/WebSocket)
2. **Lógica de Jogo** (Game Logic)
3. **Sistema de Multiplayer** (Sincronização entre jogadores)
4. **Persistência de Dados** (Database)
5. **Mecânicas do Jogo** (Gameplay específico)

---

## 🔧 Fase 1: Setup Backend

### 1.1 Escolher Framework Web

**Opção A: Flask (Recomendado para inicio)**
```bash
pip install flask flask-cors
```

**Opção B: FastAPI (Mais moderno)**
```bash
pip install fastapi uvicorn
```

**Opção C: Django (Enterprise)**
```bash
pip install django djangorestframework
```

### 1.2 Estrutura de Pasta Backend

```
Interface_DI/
├── backend/
│   ├── app.py                    # Aplicação Flask/FastAPI principal
│   ├── config.py                 # Configurações de ambiente
│   ├── requirements.txt           # Dependências Python
│   ├── models/
│   │   ├── player.py            # Modelo de jogador
│   │   ├── game_session.py       # Sessão de jogo
│   │   └── score.py             # Sistema de pontuação
│   ├── routes/
│   │   ├── auth.py              # Autenticação
│   │   ├── lobby.py             # Endpoints de lobby
│   │   ├── game.py              # Endpoints de jogo
│   │   └── scores.py            # Ranking/scores
│   ├── services/
│   │   ├── player_service.py
│   │   ├── game_service.py
│   │   └── matchmaking.py       # Encontro de jogadores
│   └── utils/
│       ├── decorators.py
│       └── validators.py
├── frontend/                      # Código atual (renamed)
│   ├── main.py
│   ├── renderer.py
│   └── ...
└── docker-compose.yml             # Orquestração
```

### 1.3 Exemplo: Servidor Flask Básico

**backend/app.py**
```python
from flask import Flask, jsonify, request
from flask_cors import CORS
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Simulação de players conectados
active_players = {}
lobbies = {}

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'online', 'timestamp': datetime.now().isoformat()})

@app.route('/api/lobby/create', methods=['POST'])
def create_lobby():
    data = request.json
    lobby_id = f"lobby_{len(lobbies) + 1}"
    lobbies[lobby_id] = {
        'id': lobby_id,
        'map': data.get('map', 'Paris'),
        'players': [],
        'created_at': datetime.now().isoformat(),
        'status': 'WAITING'
    }
    return jsonify(lobbies[lobby_id]), 201

@app.route('/api/lobby/<lobby_id>/join', methods=['POST'])
def join_lobby(lobby_id):
    data = request.json
    if lobby_id not in lobbies:
        return jsonify({'error': 'Lobby not found'}), 404
    
    player = {
        'id': data.get('player_id'),
        'name': data.get('name'),
        'ready': False,
        'joined_at': datetime.now().isoformat()
    }
    lobbies[lobby_id]['players'].append(player)
    
    if len(lobbies[lobby_id]['players']) == 5:
        lobbies[lobby_id]['status'] = 'FULL'
    
    return jsonify(lobbies[lobby_id]), 200

@app.route('/api/lobby/<lobby_id>/status', methods=['GET'])
def get_lobby_status(lobby_id):
    if lobby_id not in lobbies:
        return jsonify({'error': 'Lobby not found'}), 404
    return jsonify(lobbies[lobby_id]), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

---

## 🎮 Fase 2: Lógica de Jogo

### 2.1 Expandir Game Logic

**game_logic.py** (modificado)
```python
import random
from typing import List, Dict
from enum import Enum

class GameState(Enum):
    LOADING = "LOADING"
    PLAYING = "PLAYING"
    PAUSED = "PAUSED"
    FINISHED = "FINISHED"

class Player:
    def __init__(self, player_id: str, name: str):
        self.id = player_id
        self.name = name
        self.position = (640, 360)  # Centro da tela
        self.score = 0
        self.health = 100
        self.is_alive = True

class GameMap:
    def __init__(self, map_name: str, map_id: int):
        self.name = map_name
        self.id = map_id
        self.width = 1280
        self.height = 720
        self.obstacles = self._generate_obstacles()
        self.collectibles = self._generate_collectibles()
    
    def _generate_obstacles(self) -> List[Dict]:
        obstacles = []
        for i in range(5):
            obstacles.append({
                'x': random.randint(100, 1180),
                'y': random.randint(100, 620),
                'width': 60,
                'height': 60
            })
        return obstacles
    
    def _generate_collectibles(self) -> List[Dict]:
        items = []
        for i in range(10):
            items.append({
                'x': random.randint(100, 1180),
                'y': random.randint(100, 620),
                'type': random.choice(['coin', 'powerup', 'bonus']),
                'collected': False
            })
        return items

class GameLogic:
    def __init__(self, map_id: int, players: List[Player]):
        self.map = GameMap(['Paris', 'Berlim', 'Amesterdão'][map_id], map_id)
        self.players = players
        self.state = GameState.LOADING
        self.frame_count = 0
        self.start_time = None
    
    def update(self, player_inputs: Dict):
        """
        player_inputs: {
            'player_1': {'gesture': 'UP', 'x': 100, 'y': 200},
            ...
        }
        """
        if self.state != GameState.PLAYING:
            return
        
        self.frame_count += 1
        
        # Atualizar posição de cada jogador
        for player_id, input_data in player_inputs.items():
            player = next((p for p in self.players if p.id == player_id), None)
            if player and player.is_alive:
                self._update_player_position(player, input_data)
                self._check_collectible_collision(player)
                self._check_obstacle_collision(player)
        
        # Atualizar score
        self._update_scores()
    
    def _update_player_position(self, player: Player, input_data: Dict):
        gesture = input_data.get('gesture')
        speed = 5
        
        if gesture == 'UP':
            player.position = (player.position[0], max(0, player.position[1] - speed))
        elif gesture == 'DOWN':
            player.position = (player.position[0], min(720, player.position[1] + speed))
        elif gesture == 'LEFT':
            player.position = (player.position[0] - speed, player.position[1])
        elif gesture == 'RIGHT':
            player.position = (player.position[0] + speed, player.position[1])
    
    def _check_collectible_collision(self, player: Player):
        for item in self.map.collectibles:
            if item['collected']:
                continue
            
            dist = ((player.position[0] - item['x'])**2 + 
                   (player.position[1] - item['y'])**2)**0.5
            
            if dist < 30:
                item['collected'] = True
                self._apply_item_effect(player, item['type'])
    
    def _apply_item_effect(self, player: Player, item_type: str):
        if item_type == 'coin':
            player.score += 10
        elif item_type == 'powerup':
            player.health = min(100, player.health + 25)
        elif item_type == 'bonus':
            player.score += 50
    
    def _check_obstacle_collision(self, player: Player):
        for obstacle in self.map.obstacles:
            if (abs(player.position[0] - obstacle['x']) < 40 and
                abs(player.position[1] - obstacle['y']) < 40):
                player.health -= 5
                if player.health <= 0:
                    player.is_alive = False
    
    def _update_scores(self):
        pass  # Implementar lógica de score customizada
    
    def get_game_state(self) -> Dict:
        return {
            'map': self.map.name,
            'state': self.state.value,
            'players': [
                {
                    'id': p.id,
                    'name': p.name,
                    'position': p.position,
                    'score': p.score,
                    'health': p.health,
                    'alive': p.is_alive
                }
                for p in self.players
            ],
            'obstacles': self.map.obstacles,
            'collectibles': [
                {
                    'x': c['x'],
                    'y': c['y'],
                    'type': c['type'],
                    'collected': c['collected']
                }
                for c in self.map.collectibles
            ]
        }
```

### 2.2 Integrar com Main.py

**main.py** (modificações)
```python
from game_logic import GameLogic, Player

class InterfaceManager:
    # ... código existente ...
    
    def __init__(self):
        # ... código existente ...
        self.game_logic = None
        self.game_players = []

def main():
    # ... código existente ...
    
    if game and interface.state == "VIEWER":
        # Construir input do jogador baseado em gesto
        player_inputs = {}
        if event:
            player_inputs['player_1'] = {
                'gesture': event,
                'x': interface.current_index,
                'y': 0
            }
        
        game.update(player_inputs)
        game_state = game.get_game_state()
        
        # Renderizar estado do jogo
        final_frame = renderer.render_game(display_frame, game_state)
```

---

## 🌐 Fase 3: Sistema Multiplayer

### 3.1 WebSocket para Sincronização

**backend/websocket_server.py**
```python
import asyncio
import websockets
import json
from datetime import datetime

class GameRoom:
    def __init__(self, room_id: str, map_id: int):
        self.room_id = room_id
        self.map_id = map_id
        self.players = {}
        self.game_state = None
        self.created_at = datetime.now()
    
    async def add_player(self, player_id: str, websocket):
        self.players[player_id] = {
            'websocket': websocket,
            'joined_at': datetime.now(),
            'ready': False
        }
    
    async def remove_player(self, player_id: str):
        if player_id in self.players:
            del self.players[player_id]
    
    async def broadcast_state(self):
        if len(self.players) > 0:
            message = json.dumps(self.game_state)
            disconnected = []
            
            for player_id, player in self.players.items():
                try:
                    await player['websocket'].send(message)
                except websockets.exceptions.ConnectionClosed:
                    disconnected.append(player_id)
            
            for player_id in disconnected:
                await self.remove_player(player_id)

rooms = {}

async def game_handler(websocket, path):
    player_id = None
    room_id = None
    
    try:
        async for message in websocket:
            data = json.loads(message)
            action = data.get('action')
            
            if action == 'join':
                room_id = data.get('room_id')
                player_id = data.get('player_id')
                
                if room_id not in rooms:
                    rooms[room_id] = GameRoom(room_id, data.get('map_id', 0))
                
                await rooms[room_id].add_player(player_id, websocket)
                
                await websocket.send(json.dumps({
                    'status': 'joined',
                    'room_id': room_id,
                    'player_id': player_id,
                    'player_count': len(rooms[room_id].players)
                }))
            
            elif action == 'game_state':
                if room_id and room_id in rooms:
                    rooms[room_id].game_state = data.get('state')
                    await rooms[room_id].broadcast_state()
            
            elif action == 'leave':
                if room_id and room_id in rooms:
                    await rooms[room_id].remove_player(player_id)
    
    except websockets.exceptions.ConnectionClosed:
        if room_id and player_id and room_id in rooms:
            await rooms[room_id].remove_player(player_id)

if __name__ == '__main__':
    start_server = websockets.serve(game_handler, "0.0.0.0", 8765)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
```

### 3.2 Cliente WebSocket no Frontend

**websocket_client.py**
```python
import asyncio
import websockets
import json
from threading import Thread

class MultiplayerClient:
    def __init__(self, server_url: str = "ws://localhost:8765"):
        self.server_url = server_url
        self.websocket = None
        self.player_id = None
        self.room_id = None
        self.game_state = None
        self.connected = False
    
    async def connect(self, player_id: str, room_id: str, map_id: int):
        try:
            self.websocket = await websockets.connect(self.server_url)
            self.player_id = player_id
            self.room_id = room_id
            self.connected = True
            
            await self.websocket.send(json.dumps({
                'action': 'join',
                'player_id': player_id,
                'room_id': room_id,
                'map_id': map_id
            }))
            
            # Listen para mensagens
            await self._listen()
        
        except Exception as e:
            print(f"Erro de conexão: {e}")
            self.connected = False
    
    async def _listen(self):
        try:
            async for message in self.websocket:
                data = json.loads(message)
                self.game_state = data.get('state')
        except websockets.exceptions.ConnectionClosed:
            self.connected = False
    
    def connect_threaded(self, player_id: str, room_id: str, map_id: int):
        """Conexão em thread separada"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        thread = Thread(
            target=lambda: loop.run_until_complete(
                self.connect(player_id, room_id, map_id)
            )
        )
        thread.daemon = True
        thread.start()
    
    async def send_game_state(self, state: dict):
        if self.connected and self.websocket:
            await self.websocket.send(json.dumps({
                'action': 'game_state',
                'state': state
            }))
    
    async def disconnect(self):
        if self.websocket:
            await self.websocket.send(json.dumps({'action': 'leave'}))
            await self.websocket.close()
            self.connected = False
```

---

## 💾 Fase 4: Persistência de Dados

### 4.1 Database Schema

**SQLite (Desenvolvimento)**
```sql
-- Tabela de Jogadores
CREATE TABLE players (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Tabela de Sessões de Jogo
CREATE TABLE game_sessions (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    map_id INTEGER,
    status TEXT,
    winner_id TEXT FOREIGN KEY REFERENCES players(id)
);

-- Tabela de Participação
CREATE TABLE session_players (
    session_id TEXT FOREIGN KEY REFERENCES game_sessions(id),
    player_id TEXT FOREIGN KEY REFERENCES players(id),
    final_score INTEGER,
    alive BOOLEAN,
    PRIMARY KEY (session_id, player_id)
);

-- Tabela de Scores/Rankings
CREATE TABLE scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id TEXT FOREIGN KEY REFERENCES players(id),
    game_session_id TEXT FOREIGN KEY REFERENCES game_sessions(id),
    score INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4.2 ORM (SQLAlchemy)

**backend/models/__init__.py**
```python
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Player(db.Model):
    __tablename__ = 'players'
    
    id = db.Column(db.String(50), primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    scores = db.relationship('Score', backref='player', lazy=True)
    sessions = db.relationship('SessionPlayer', backref='player', lazy=True)

class GameSession(db.Model):
    __tablename__ = 'game_sessions'
    
    id = db.Column(db.String(50), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    map_id = db.Column(db.Integer)
    status = db.Column(db.String(20))
    winner_id = db.Column(db.String(50), db.ForeignKey('players.id'))
    
    players = db.relationship('SessionPlayer', backref='session', lazy=True)
    scores = db.relationship('Score', backref='session', lazy=True)

class Score(db.Model):
    __tablename__ = 'scores'
    
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.String(50), db.ForeignKey('players.id'), nullable=False)
    session_id = db.Column(db.String(50), db.ForeignKey('game_sessions.id'))
    score = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
```

---

## 🎨 Fase 5: Renderização de Jogo Avançada

### 5.1 Expandir Renderer para Game View

**renderer.py** (adicionar método)
```python
def render_game(self, image, game_state: Dict):
    """Renderiza o estado do jogo com todos os elementos"""
    h, w = image.shape[:2]
    
    # Renderizar obstáculos
    for obstacle in game_state.get('obstacles', []):
        x, y = int(obstacle['x']), int(obstacle['y'])
        cv2.rectangle(image, (x, y), (x+60, y+60), (100, 100, 100), -1)
        cv2.rectangle(image, (x, y), (x+60, y+60), (200, 0, 0), 2)
    
    # Renderizar coletáveis
    for item in game_state.get('collectibles', []):
        if item['collected']:
            continue
        
        x, y = int(item['x']), int(item['y'])
        
        if item['type'] == 'coin':
            cv2.circle(image, (x, y), 8, (0, 215, 255), -1)
        elif item['type'] == 'powerup':
            cv2.circle(image, (x, y), 10, (0, 255, 0), -1)
        elif item['type'] == 'bonus':
            cv2.circle(image, (x, y), 12, (0, 255, 255), -1)
    
    # Renderizar jogadores
    colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (255, 255, 0), (255, 0, 255)]
    for i, player in enumerate(game_state.get('players', [])):
        if not player['alive']:
            continue
        
        x, y = int(player['position'][0]), int(player['position'][1])
        color = colors[i % len(colors)]
        
        cv2.circle(image, (x, y), 15, color, -1)
        
        # Health bar
        health_width = int((player['health'] / 100) * 30)
        cv2.rectangle(image, (x-15, y-25), (x+15, y-20), (0, 0, 255), -1)
        cv2.rectangle(image, (x-15, y-25), (x-15+health_width, y-20), (0, 255, 0), -1)
        
        # Score
        self._put_text_ttf(image, f"{player['name']}: {player['score']}", 
                          (x-20, y+30), 16, (255, 255, 255))
    
    # HUD
    self._put_text_ttf(image, "GAME", (20, 30), 24, (255, 255, 255))
    
    return image
```

---

## 🧪 Fase 6: Testes e Validação

### 6.1 Testes Unitários

**tests/test_game_logic.py**
```python
import unittest
from game_logic import GameLogic, Player, GameMap

class TestGameLogic(unittest.TestCase):
    def setUp(self):
        self.players = [
            Player(f"player_{i}", f"Jogador {i}")
            for i in range(5)
        ]
        self.game = GameLogic(0, self.players)
    
    def test_player_initialization(self):
        player = self.players[0]
        self.assertEqual(player.score, 0)
        self.assertEqual(player.health, 100)
        self.assertTrue(player.is_alive)
    
    def test_collectible_collision(self):
        player = self.players[0]
        initial_score = player.score
        
        # Simular colisão
        item = self.game.map.collectibles[0]
        player.position = (item['x'], item['y'])
        self.game._check_collectible_collision(player)
        
        self.assertTrue(item['collected'])
        self.assertGreater(player.score, initial_score)
    
    def test_game_state_export(self):
        state = self.game.get_game_state()
        self.assertIn('map', state)
        self.assertIn('players', state)
        self.assertIn('obstacles', state)
        self.assertEqual(len(state['players']), 5)

if __name__ == '__main__':
    unittest.main()
```

---

## 🚀 Checklist de Implementação

### Backend
- [ ] Escolher framework (Flask/FastAPI/Django)
- [ ] Implementar endpoints de lobby
- [ ] Implementar endpoints de autenticação
- [ ] Configurar CORS
- [ ] Implementar WebSocket para multiplayer
- [ ] Configurar database (SQLite/PostgreSQL)
- [ ] Implementar ORM models

### Frontend
- [ ] Integrar cliente HTTP (requests/aiohttp)
- [ ] Integrar WebSocket client
- [ ] Expandir game_logic.py com mecânicas
- [ ] Atualizar renderer.py para game view
- [ ] Implementar multiplayer sync
- [ ] Testes de integração

### Infraestrutura
- [ ] Criar docker-compose.yml
- [ ] Setup CI/CD (GitHub Actions)
- [ ] Configurar logging
- [ ] Implementar error handling
- [ ] Setup monitoring (opcional)

---

## 📚 Recursos Adicionais

### Documentação
- [Flask Documentation](https://flask.palletsprojects.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [WebSockets Protocol](https://datatracker.ietf.org/doc/html/rfc6455)
- [OpenCV Documentation](https://docs.opencv.org/)

### Bibliotecas Úteis
```bash
# HTTP Client
pip install requests aiohttp

# Database
pip install sqlalchemy alembic psycopg2-binary

# WebSocket
pip install websockets websocket-client

# Testing
pip install pytest pytest-asyncio

# Utilities
pip install python-dotenv pydantic pyyaml
```

---

## 🤝 Próximos Passos

1. **Semana 1-2**: Setup backend básico + endpoints de lobby
2. **Semana 3-4**: Integração WebSocket + sincronização multiplayer
3. **Semana 5-6**: Expandir game_logic com mecânicas específicas
4. **Semana 7-8**: Sistema de persistência + ranking
5. **Semana 9-10**: Testes, otimização e documentação
6. **Semana 11-12**: Deploy e monitoramento

---

## 📞 Suporte

Para dúvidas ou problemas com a implementação, consulte:
- Issues do repositório
- Documentação oficial das bibliotecas
- Comunidades online (Stack Overflow, Discord)

---

**Última atualização**: Dezembro 2025
**Versão**: 1.0
