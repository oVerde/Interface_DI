import time


class Lobby:
    def __init__(self):
        self.state = "INACTIVE"
        self.start_time = None
        self.countdown_duration = 3
        self.map_index = None
        self.loading_time = time.time()
    
    def enter_lobby(self, map_index):
        self.state = "ACTIVE"
        self.start_time = time.time()
        self.map_index = map_index
    
    def update(self):
        if self.state == "INACTIVE":
            return "INACTIVE", None
        
        elapsed = time.time() - self.start_time
        remaining = self.countdown_duration - elapsed
        
        if remaining <= 0:
            self.state = "STARTING"
            return "STARTING", 0
        
        return "ACTIVE", remaining
    
    def exit_lobby(self):
        self.state = "INACTIVE"
        self.start_time = None
        self.map_index = None
    
    def should_start_game(self):
        return self.state == "STARTING"
    
    def get_loading_dots(self):
        elapsed = (time.time() - self.loading_time) * 3
        dots = (int(elapsed) % 4)
        return "." * dots
