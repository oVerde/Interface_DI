import cv2
import sys
import os

# Configurar para usar GPU se disponível
os.environ['OPENCV_VIDEOIO_PRIORITY_MSMF'] = '0'  # Prioridade para DirectShow
try:
    # Tentar habilitar CUDA se disponível
    if cv2.cuda.getCudaEnabledDeviceCount() > 0:
        print(f"✓ GPU CUDA detectada: {cv2.cuda.getCudaEnabledDeviceCount()} dispositivo(s)")
        os.environ['OPENCV_DNN_BACKEND'] = 'CUDA'
        os.environ['OPENCV_DNN_TARGET'] = 'CUDA'
except:
    pass

# Tentar usar DirectML (GPU AMD/Intel no Windows)
try:
    import mediapipe as mp
    # MediaPipe vai usar GPU automaticamente se TensorFlow Lite GPU estiver disponível
except:
    pass

from gesture_engine import GestureEngine
from renderer import Renderer
from game_logic import Map1Game, Map2Game, Map3Game
from background_loader import BackgroundLoader
from lobby import Lobby


class InterfaceManager:
    def __init__(self):
        self.maps = ["Paris", "Berlim", "Amesterdão"]
        self.locked_maps = [1, 2]
        self.current_index = 0
        self.state = "SELECTOR"
    
    def update(self, event):
        if not event or self.state != "SELECTOR":
            return
        if event == 'NEXT':
            self.current_index = (self.current_index + 1) % len(self.maps)
        elif event == 'PREV':
            self.current_index = (self.current_index - 1 + len(self.maps)) % len(self.maps)
        elif event == 'SELECT' and self.current_index not in self.locked_maps:
            self.state = "MULTIPLAYER_LOBBY"
    
    def get_state_data(self):
        return {'state': self.state, 'maps': self.maps, 'current_index': self.current_index,
                'locked_maps': self.locked_maps, 'is_locked': self.current_index in self.locked_maps}


def _check_python_version():
    ver = sys.version_info
    if ver.major != 3 or ver.minor != 12:
        print(f"[Aviso] Python recomendado: 3.12.x. Está a usar {ver.major}.{ver.minor}.{ver.micro}.")
        print("         Siga o README para usar 'py -3.12' ou o setup.ps1.")

def _open_camera():
    """Tenta abrir a câmera usando diferentes backends e índices"""
    backends = [
        (cv2.CAP_DSHOW, "DirectShow"),
        (cv2.CAP_MSMF, "Media Foundation"),
        (cv2.CAP_ANY, "Auto")
    ]
    camera_indices = [0, 1, 2]
    
    for idx in camera_indices:
        for backend, backend_name in backends:
            try:
                print(f"Tentando câmera {idx} com {backend_name}...")
                cap = cv2.VideoCapture(idx, backend)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        print(f"✓ Câmera {idx} OK ({backend_name})")
                        # Otimizações de performance
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                        cap.set(cv2.CAP_PROP_FPS, 30)
                        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                        return cap
                    cap.release()
            except:
                continue
    return None

def main():
    print("Iniciando programa...")
    _check_python_version()
    cap = _open_camera()
    if cap is None:
        print("ERRO: Nenhuma câmera encontrada!")
        return
    print("Carregando componentes...")
    bg_loader = BackgroundLoader((1280, 720))
    engine = GestureEngine()
    interface = InterfaceManager()
    renderer = Renderer()
    renderer.set_backgrounds(bg_loader, interface.maps)
    game = None
    frame_count = 0
    print("Componentes carregados!")
    
    cv2.namedWindow('Interactive Project Python', cv2.WINDOW_NORMAL)
    cv2.setWindowProperty('Interactive Project Python', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    print("Sistema iniciado. Comandos: Braço direito (NEXT), Braço esquerdo (PREV), Ambos (SELECT)")

    # Cache do background atual
    current_bg = bg_loader.get_background(interface.current_index)
    last_index = interface.current_index
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            continue

        frame = cv2.flip(frame, 1)
        
        # Processar gestos apenas a cada 2 frames para performance
        event = None
        if frame_count % 2 == 0:
            results = engine.process_frame(frame)
            event = engine.detect_gesture(results)
        frame_count += 1
        
        # Atualizar background apenas se mudou
        if interface.current_index != last_index:
            current_bg = bg_loader.get_background(interface.current_index)
            last_index = interface.current_index
        display_frame = current_bg

        prev_state = interface.state
        interface.update(event)
        
        if prev_state == "SELECTOR" and interface.state == "MULTIPLAYER_LOBBY":
            renderer.init_multiplayer_lobby()
        
        if interface.state == "MULTIPLAYER_LOBBY":
            renderer.update_multiplayer_lobby(event)
            if renderer.multiplayer_lobby_finished():
                game = [Map1Game(), Map2Game(), Map3Game()][interface.current_index]
                interface.state = "LOBBY"
                renderer.init_lobby(interface.current_index)
        
        if interface.state == "LOBBY":
            renderer.update_lobby()
            if renderer.lobby_finished():
                interface.state = "VIEWER"
        
        if game and interface.state == "VIEWER":
            game.update(event, results)

        state_data = interface.get_state_data()
        mp_data = {'confirmed_players': renderer.multiplayer_players_ready, 'total_players': 5}
        final_frame = renderer.render(display_frame, interface.state, state_data['maps'], 
                                      state_data['current_index'], is_locked=state_data['is_locked'], 
                                      mp_lobby_data=mp_data)

        cv2.imshow('Interactive Project Python', final_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            break
        elif key == 8:
            if interface.state == "VIEWER":
                game = None
                interface.state = "SELECTOR"
            elif interface.state == "MULTIPLAYER_LOBBY":
                interface.state = "SELECTOR"
            elif interface.state == "LOBBY":
                interface.state = "SELECTOR"
        elif key == 13 and interface.state == "MULTIPLAYER_LOBBY":
            renderer.set_player_ready()

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()