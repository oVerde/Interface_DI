import cv2
import sys
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

def main():
    _check_python_version()
    cap = cv2.VideoCapture(0)
    cap.set(3, 1280)
    cap.set(4, 720)

    bg_loader = BackgroundLoader((1280, 720))
    engine = GestureEngine()
    interface = InterfaceManager()
    renderer = Renderer()
    renderer.set_backgrounds(bg_loader, interface.maps)
    game = None
    window_created = False
    
    cv2.namedWindow('Interactive Project Python', cv2.WINDOW_NORMAL)
    cv2.setWindowProperty('Interactive Project Python', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    print("Sistema iniciado. Comandos: Braço direito (NEXT), Braço esquerdo (PREV), Ambos (SELECT)")

    while cap.isOpened():
        if not cap.grab():
            break
        success, frame = cap.retrieve()
        if not success:
            continue

        frame = cv2.flip(frame, 1)
        results = engine.process_frame(frame)
        event = engine.detect_gesture(results)
        display_frame = bg_loader.get_background(interface.current_index)

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
        if not window_created:
            window_created = True

        key = cv2.waitKey(5) & 0xFF
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