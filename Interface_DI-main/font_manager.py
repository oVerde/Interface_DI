"""
Font Manager for OpenCV
Handles loading and using .ttf fonts with OpenCV using PIL
Optimized: Uses PIL for rendering, converts back to OpenCV efficiently
"""

import cv2
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import os


class FontManager:
    """Manages .ttf fonts for OpenCV rendering using PIL - OPTIMIZED"""
    
    _fonts_cache = {}
    _default_font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'Roboto-VariableFont_wdth,wght.ttf')
    
    @staticmethod
    def load_font(font_path=None, font_size=30):
        """
        Load a .ttf font
        
        Args:
            font_path: Path to .ttf file (default: Roboto from fonts/)
            font_size: Font size in pixels
            
        Returns:
            PIL.ImageFont object
        """
        if font_path is None:
            font_path = FontManager._default_font_path
        
        cache_key = f"{font_path}_{font_size}"
        
        if cache_key not in FontManager._fonts_cache:
            try:
                font = ImageFont.truetype(font_path, font_size)
                FontManager._fonts_cache[cache_key] = font
                print(f"[OK] Font loaded: {font_path} (size: {font_size})")
            except Exception as e:
                print(f"[ERROR] Error loading font {font_path}: {e}")
                print(f"  Falling back to default OpenCV font")
                return None
        
        return FontManager._fonts_cache[cache_key]
    
    @staticmethod
    def put_text(img, text, position, font_size=24, color=(255, 255, 255), font_path=None, thickness=1):
        """
        Draw text on image using .ttf font (PIL) or fallback to OpenCV
        
        Args:
            img: OpenCV image (BGR) - MODIFIED IN-PLACE
            text: Text to display
            position: (x, y) tuple
            font_size: Size of font in pixels
            color: BGR color tuple
            font_path: Path to .ttf font (default: Roboto)
            thickness: Ignored (kept for API compatibility)
        """
        if font_path is None:
            font_path = FontManager._default_font_path
        
        font = FontManager.load_font(font_path, font_size)
        if font is None:
            # Fallback to OpenCV font
            cv2.putText(img, text, position, cv2.FONT_HERSHEY_DUPLEX, 
                       max(0.5, font_size / 25), color, thickness)
            return img
        
        # Convert BGR to RGB for PIL
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        draw = ImageDraw.Draw(pil_img)
        
        # Convert BGR to RGB for PIL
        color_rgb = (color[2], color[1], color[0])
        
        draw.text(position, text, font=font, fill=color_rgb)
        
        # Convert back to BGR
        img_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        
        # Copy back to original image
        img[:] = img_bgr
        return img
    
    @staticmethod
    def get_text_size(text, font):
        """
        Get size of text rendered with .ttf font
        
        Args:
            text: Text to measure
            font: PIL ImageFont object
            
        Returns:
            (width, height) tuple
        """
        if font is None:
            return (0, 0)
        
        bbox = font.getbbox(text)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        return (width, height)


class UIFont:
    """Manages fonts for UI rendering"""
    
    def __init__(self, font_path=None, base_size=30):
        """
        Initialize UI font
        
        Args:
            font_path: Path to .ttf font file (defaults to Roboto in fonts/)
            base_size: Base font size for calculations
        """
        if font_path is None:
            # Default to Roboto in fonts folder
            font_path = Path(__file__).parent / 'fonts' / 'Roboto-VariableFont_wdth,wght.ttf'
        
        self.font_path = str(font_path)
        self.base_size = base_size
        
        # Font size presets (relative to base_size)
        self.size_presets = {
            'title': int(base_size * 3.5),      # Large titles
            'large': int(base_size * 2.0),      # Large text
            'medium': int(base_size * 1.2),     # Normal text
            'small': int(base_size * 0.8),      # Small text
            'tiny': int(base_size * 0.6),       # Very small text
        }
        
        # Load fonts for each preset
        self.fonts = {}
        for preset_name, preset_size in self.size_presets.items():
            self.fonts[preset_name] = FontManager.load_font(self.font_path, preset_size)
    
    def get_font(self, size_name):
        """Get font object from preset name"""
        return self.fonts.get(size_name)
    
    def get_size(self, size_name):
        """Get font size from preset name"""
        return self.size_presets.get(size_name, self.base_size)
    
    def put_text(self, img, text, position, size_name='medium', color=(255, 255, 255),
                thickness=1, outline=False, outline_color=(0, 0, 0)):
        """
        Draw text on image with preset sizes
        
        Args:
            img: Image to draw on
            text: Text to display
            position: (x, y) tuple
            size_name: 'title', 'large', 'medium', 'small', 'tiny'
            color: BGR color tuple
            thickness: Text thickness (ignored for PIL but kept for API compatibility)
            outline: If True, draw outline first
            outline_color: Color for outline
        """
        font = self.get_font(size_name)
        
        # Draw outline first if requested
        if outline:
            x, y = position
            # Draw outline in 8 directions
            for dx in [-2, -1, 0, 1, 2]:
                for dy in [-2, -1, 0, 1, 2]:
                    if dx != 0 or dy != 0:
                        FontManager.put_text(img, text, (x + dx, y + dy), font, outline_color)
        
        # Draw main text
        FontManager.put_text(img, text, position, font, color)
        
        return img
    
    def put_text_centered(self, img, text, y_pos, size_name='medium',
                         color=(255, 255, 255), thickness=1, outline=False):
        """Draw text centered horizontally"""
        h, w = img.shape[:2]
        font = self.get_font(size_name)
        text_size = FontManager.get_text_size(text, font)
        x = (w - text_size[0]) // 2
        
        return self.put_text(img, text, (x, y_pos), size_name, color, 
                           thickness, outline)
    
    def put_text_left(self, img, text, y_pos, size_name='medium',
                     color=(255, 255, 255), thickness=1, outline=False, x_offset=40):
        """Draw text aligned to left"""
        return self.put_text(img, text, (x_offset, y_pos), size_name, color,
                           thickness, outline)
    
    def put_text_right(self, img, text, y_pos, size_name='medium',
                      color=(255, 255, 255), thickness=1, outline=False):
        """Draw text aligned to right"""
        h, w = img.shape[:2]
        font = self.get_font(size_name)
        text_size = FontManager.get_text_size(text, font)
        x = w - text_size[0] - 40
        
        return self.put_text(img, text, (x, y_pos), size_name, color,
                           thickness, outline)
