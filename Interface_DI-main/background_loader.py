import cv2
import numpy as np
from pathlib import Path

class BackgroundLoader:
    def __init__(self, resolution=(1280, 720)):
        self.resolution = resolution
        self.backgrounds = {}
        self.base_path = Path("img")
        self._load_backgrounds()
    
    def _load_backgrounds(self):
        for i in range(3):
            path = self.base_path / f"map{i+1}" / "background.png"
            if path.exists():
                img = cv2.imread(str(path))
                self.backgrounds[i] = cv2.resize(img, self.resolution) if img is not None else self._placeholder(i+1)
            else:
                self.backgrounds[i] = self._placeholder(i+1)
    
    def _placeholder(self, map_num):
        img = np.ones((self.resolution[1], self.resolution[0], 3), dtype=np.uint8) * 30
        text = f"Add background.png to img/map{map_num}/"
        size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)[0]
        x, y = (self.resolution[0] - size[0]) // 2, (self.resolution[1] - size[1]) // 2
        cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (100, 200, 255), 2)
        return img
    
    def get_background(self, map_index):
        return self.backgrounds.get(map_index, self._placeholder(map_index + 1)).copy()
