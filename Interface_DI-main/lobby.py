import time
import sys
import os

# Importar PoseTracker do projeto desenvolvido
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Projeto-DI-main', 'poseCenario'))

try:
    from colega import PoseTracker
    MULTI_PERSON_AVAILABLE = True
except ImportError:
    MULTI_PERSON_AVAILABLE = False
    print("Aviso: PoseTracker não disponível. Usando modo simples.")


class Lobby:
    """
    Sistema de lobby integrado com detecção multi-pessoa do Projeto-DI-main.
    Mantém compatibilidade com a interface existente.
    """
    def __init__(self):
        self.state = "INACTIVE"
        self.start_time = None
        self.countdown_duration = 3
        self.map_index = None
        self.loading_time = time.time()
        
        # Sistema multi-pessoa do projeto
        self.max_people = 5
        self.detected_people = 0
        self.required_people = 5
        self.pose_tracker = None
        
        if MULTI_PERSON_AVAILABLE:
            try:
                self.pose_tracker = PoseTracker(max_people=self.max_people)
                self.pose_tracker.start()
                print("✓ Sistema multi-pessoa ativado (Projeto-DI-main)")
            except Exception as e:
                print(f"Aviso: Não foi possível iniciar PoseTracker: {e}")
                self.pose_tracker = None
    
    def enter_lobby(self, map_index):
        """Entra no lobby e inicia detecção de jogadores"""
        self.state = "WAITING_PLAYERS"
        self.start_time = time.time()
        self.map_index = map_index
        self.detected_people = 0
    
    def update(self, frame=None):
        """
        Atualiza estado do lobby
        Returns: (state, countdown/info)
        """
        if self.state == "INACTIVE":
            return "INACTIVE", None
        
        # Detectar jogadores se o tracker estiver disponível
        if self.pose_tracker and frame is not None:
            try:
                poses = self.pose_tracker.get_smoothed_poses()
                self.detected_people = len([p for p in poses if p])
            except:
                pass
        
        # Estado: Aguardando jogadores
        if self.state == "WAITING_PLAYERS":
            if self.detected_people >= self.required_people:
                self.state = "COUNTDOWN"
                self.start_time = time.time()
            return "WAITING_PLAYERS", self.detected_people
        
        # Estado: Contagem regressiva
        if self.state == "COUNTDOWN":
            elapsed = time.time() - self.start_time
            remaining = self.countdown_duration - elapsed
            
            # Se perdeu jogadores, volta para espera
            if self.detected_people < self.required_people:
                self.state = "WAITING_PLAYERS"
                return "WAITING_PLAYERS", self.detected_people
            
            if remaining <= 0:
                self.state = "STARTING"
                return "STARTING", 0
            
            return "COUNTDOWN", remaining
        
        return self.state, None
    
    def exit_lobby(self):
        """Sai do lobby"""
        self.state = "INACTIVE"
        self.start_time = None
        self.map_index = None
        self.detected_people = 0
    
    def should_start_game(self):
        """Verifica se deve iniciar o jogo"""
        return self.state == "STARTING"
    
    def get_loading_dots(self):
        """Animação de pontos de carregamento"""
        elapsed = (time.time() - self.loading_time) * 3
        dots = (int(elapsed) % 4)
        return "." * dots
    
    def get_player_count(self):
        """Retorna número de jogadores detectados"""
        return self.detected_people
    
    def cleanup(self):
        """Limpa recursos do lobby"""
        if self.pose_tracker:
            try:
                self.pose_tracker.stop()
            except:
                pass

