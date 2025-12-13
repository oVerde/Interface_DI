import os
import random
import arcade
from points import get_speed, get_size, get_left, get_right

ACCURACY = 0.04
WIDTH, HEIGHT = 1280, 720
FPS = 60

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(SCRIPT_DIR, "img")

def load_texture_safe(path):
    if os.path.exists(path):
        try:
            return arcade.load_texture(path)
        except Exception as e:
            print(f"Erro ao carregar {path}: {e}")
    return arcade.make_soft_square_texture(64, (255, 0, 255), 255)
bg_original = load_texture_safe(os.path.join(IMG_DIR, 'Fundo.jpg'))

imagens_basic = [
    load_texture_safe(os.path.join(IMG_DIR, 'BasicElements', 'PUB.png')),
    load_texture_safe(os.path.join(IMG_DIR, 'BasicElements', 'Three1.png')),
    load_texture_safe(os.path.join(IMG_DIR, 'BasicElements', 'Three2.png')),
]

imagens_direita = [
    load_texture_safe(os.path.join(IMG_DIR, 'ElementosDir', f'Element_{i}.png'))
    for i in range(1, 3)
]

imagens_esquerda = [
    load_texture_safe(os.path.join(IMG_DIR, 'ElementosEsq', f'Elemento_{i}.png'))
    for i in range(1, 4)
]

imagem_trunfo = load_texture_safe(os.path.join(IMG_DIR, 'ElementsUniqueEsq', 'Trunfo.png'))
imagem_torre = load_texture_safe(os.path.join(IMG_DIR, 'ElementoFixo', 'Torre.png'))


def get_basic_texture():
    if random.random() < 0.07:
        return imagens_basic[0]
    else:
        return random.choice(imagens_basic[1:])


class AnimatedElement:
    def __init__(self, texture, window: arcade.Window):
        self.window = window
        self.texture = texture
        self.sprite = arcade.Sprite()
        self.sprite.texture = texture
        self.t = 0.0
        self.t_raw = 0.0
        self.active = True
        self.size = 0.0
        self.speed_t = 0.001 * get_speed(ACCURACY)
    
    def ease_out(self, t):
        SLOW_PHASE = 0.15
        SLOW_PROGRESS = 0.035
        
        if t < SLOW_PHASE:
            return (t / SLOW_PHASE) * SLOW_PROGRESS
        else:
            remaining = (t - SLOW_PHASE) / (1.0 - SLOW_PHASE)
            return SLOW_PROGRESS + remaining * (1.0 - SLOW_PROGRESS)

    @property
    def width(self):
        return self.sprite.texture.width * max(self.size, 0.0001)

    @property
    def height(self):
        return self.sprite.texture.height * max(self.size, 0.0001)

    def update(self, delta_time: float):
        raise NotImplementedError

    def draw(self):
        if not self.active or self.size <= 0.001:
            return
        self.sprite.center_x = self.x
        self.sprite.center_y = self.y
        self.sprite.scale = self.size
        
        alpha = int(min(self.t / 0.0015, 1.0) * 255)
        self.sprite.alpha = alpha
        
        arcade.draw_sprite(self.sprite)


class ElementoFixo(AnimatedElement):
    def __init__(self, window: arcade.Window):
        super().__init__(imagem_torre, window)
        self.max_size_reached = False
        self.pos_inicial_x = 0.5
        self.pos_inicial_y = 0.425
        self.pos_final_x = 0.5
        self.pos_final_y = 0.525
        self.scale_inicial = 0.05
        self.scale_final = 0.25
        self.size = self.scale_inicial
        self.speed_t = 0.00025 * get_speed(ACCURACY)

    def update(self, delta_time: float):
        if self.max_size_reached:
            return

        self.t += self.speed_t * 1000 * delta_time

        start_x = self.window.width * self.pos_inicial_x
        start_y = self.window.height * self.pos_inicial_y
        end_x = self.window.width * self.pos_final_x
        end_y = self.window.height * self.pos_final_y

        self.x = start_x + (end_x - start_x) * self.t
        self.y = start_y + (end_y - start_y) * self.t
        self.size = self.scale_inicial + (self.scale_final - self.scale_inicial) * self.t

        if self.size >= self.scale_final:
            self.size = self.scale_final
            self.max_size_reached = True


class BasicElement(AnimatedElement):
    def __init__(self, is_left_side: bool, window: arcade.Window):
        texture = get_basic_texture()
        super().__init__(texture, window)
        self.is_left = is_left_side
        
        if is_left_side:
            self.pos_inicial_x = 0.495
            self.pos_inicial_y = 0.40
            self.pos_final_x = -3
            self.pos_final_y = 0.475 * -1.5
        else:
            self.pos_inicial_x = 0.505
            self.pos_inicial_y = 0.40
            self.pos_final_x = 4
            self.pos_final_y = 0.475 * -1.5
        
        self.scale_inicial = 0.01
        self.scale_final = 6.750
        self.size = self.scale_inicial
        self.x_spread = 0
        
        self.x = window.width * self.pos_inicial_x
        self.y = window.height * self.pos_inicial_y

    def update(self, delta_time: float):
        if not self.active:
            return

        self.t_raw += self.speed_t * 1000 * delta_time
        self.t = self.ease_out(min(self.t_raw, 1.0))

        start_x = self.window.width * self.pos_inicial_x
        start_y = self.window.height * self.pos_inicial_y
        end_x = self.window.width * self.pos_final_x
        end_y = self.window.height * self.pos_final_y

        self.x = start_x + (end_x - start_x) * self.t
        self.y = start_y + (end_y - start_y) * self.t
        
        self.x += self.window.width * self.x_spread * self.t
        
        self.size = self.scale_inicial + (self.scale_final - self.scale_inicial) * self.t

        if self.t_raw > 1.5 or self.x < -self.window.width or self.x > self.window.width * 2:
            self.active = False


class ElementoEsquerda(AnimatedElement):
    def __init__(self, window: arcade.Window):
        todas = imagens_esquerda
        texture = random.choice(todas)
        super().__init__(texture, window)
        self.pos_inicial_x = 0.495
        self.pos_inicial_y = 0.40
        self.pos_final_x = -1.4 * 40
        self.pos_final_y = 0.475 * -2
        self.scale_inicial = 0.01
        self.scale_final = 30
        self.size = self.scale_inicial
        self.x_spread = random.uniform(-0.08, 0.08)
        
        self.x = window.width * self.pos_inicial_x
        self.y = window.height * self.pos_inicial_y
        print(f"ElementoEsquerda criado: x={self.x:.1f}, y={self.y:.1f}, size={self.size}")

    def update(self, delta_time: float):
        if not self.active:
            return

        self.t_raw += self.speed_t * 1000 * delta_time
        self.t = self.ease_out(min(self.t_raw, 1.0))

        start_x = self.window.width * self.pos_inicial_x
        start_y = self.window.height * self.pos_inicial_y
        end_x = self.window.width * self.pos_final_x
        end_y = self.window.height * self.pos_final_y

        self.x = start_x + (end_x - start_x) * self.t
        self.y = start_y + (end_y - start_y) * self.t
        
        self.x += self.window.width * self.x_spread * self.t
        
        self.size = self.scale_inicial + (self.scale_final - self.scale_inicial) * self.t

        if self.t_raw > 1.5 or self.x < -self.window.width or self.y > self.window.height + 200:
            self.active = False


class ElementoDireita(AnimatedElement):
    def __init__(self, window: arcade.Window):
        texture = random.choice(imagens_direita)
        super().__init__(texture, window)
        self.pos_inicial_x = 0.505
        self.pos_inicial_y = 0.40
        self.pos_final_x = 1.4 * 35
        self.pos_final_y = 0.475 * -2
        self.scale_inicial = 0.01
        self.scale_final = 30
        self.size = self.scale_inicial
        self.x_spread = random.uniform(-0.08, 0.08)

    def update(self, delta_time: float):
        if not self.active:
            return

        self.t_raw += self.speed_t * 1000 * delta_time
        self.t = self.ease_out(min(self.t_raw, 1.0))

        start_x = self.window.width * self.pos_inicial_x
        start_y = self.window.height * self.pos_inicial_y
        end_x = self.window.width * self.pos_final_x
        end_y = self.window.height * self.pos_final_y

        self.x = start_x + (end_x - start_x) * self.t
        self.y = start_y + (end_y - start_y) * self.t
        
        self.x += self.window.width * self.x_spread * self.t
        
        self.size = self.scale_inicial + (self.scale_final - self.scale_inicial) * self.t

        if self.t_raw > 1.5 or self.x > self.window.width + 300 or self.y > self.window.height + 200:
            self.active = False


class PerspectivaWindow(arcade.Window):
    def __init__(self, width, height, title="Perspectiva Python"):
        super().__init__(width, height, title, resizable=True)
        arcade.set_background_color(arcade.color.BLACK)

        self.elementos = []
        self.elemento_fixo = ElementoFixo(self)

        self.count_left = 0
        self.count_right = 0
        self.count_basic = 0

        self.MAX_ARVORES_POR_EIXO = 40
        self.MAX_BASIC_ELEMENTS = 15

        self.last_spawn_left = 0
        self.last_spawn_right = 0
        self.last_spawn_basic_left = 0
        self.last_spawn_basic_right = 0

        self.interval_left = get_left(ACCURACY)
        self.interval_right = get_right(ACCURACY)
        self.interval_basic_base = 3200
        self.interval_basic_left = self.interval_basic_base + random.randint(200, 400)
        self.interval_basic_right = self.interval_basic_base + random.randint(200, 400)

        self.bg_texture = bg_original
        
        self.bg_sprite = arcade.Sprite()
        self.bg_sprite.texture = self.bg_texture
        self.update_background_sprite()

    def update_background_sprite(self):
        self.bg_sprite.center_x = self.width / 2
        self.bg_sprite.center_y = self.height / 2
        scale_x = self.width / self.bg_texture.width
        scale_y = self.height / self.bg_texture.height
        self.bg_sprite.scale = max(scale_x, scale_y)

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.update_background_sprite()
        
        for elemento in self.elementos:
            if elemento.active:
                start_x = self.width * elemento.pos_inicial_x
                start_y = self.height * elemento.pos_inicial_y
                end_x = self.width * elemento.pos_final_x
                end_y = self.height * elemento.pos_final_y
                
                elemento.x = start_x + (end_x - start_x) * elemento.t
                elemento.y = start_y + (end_y - start_y) * elemento.t
        
        start_x = self.width * self.elemento_fixo.pos_inicial_x
        start_y = self.height * self.elemento_fixo.pos_inicial_y
        end_x = self.width * self.elemento_fixo.pos_final_x
        end_y = self.height * self.elemento_fixo.pos_final_y
        
        self.elemento_fixo.x = start_x + (end_x - start_x) * self.elemento_fixo.t
        self.elemento_fixo.y = start_y + (end_y - start_y) * self.elemento_fixo.t

    def on_draw(self):
        self.clear()

        rect = arcade.LBWH(0, 0, self.width, self.height)
        arcade.draw_texture_rect(self.bg_texture, rect)

        self.elementos = [e for e in self.elementos if e.active]
        self.elementos.sort(key=lambda e: e.size)

        for elemento in self.elementos:
            elemento.draw()

        self.elemento_fixo.draw()

    def on_update(self, delta_time: float):
        dt_ms = delta_time * 1000

        self.last_spawn_basic_left += dt_ms
        if self.last_spawn_basic_left >= self.interval_basic_left:
            self.elementos.append(BasicElement(is_left_side=True, window=self))
            self.last_spawn_basic_left = 0
            self.interval_basic_left = self.interval_basic_base + random.randint(200, 400)

        self.last_spawn_basic_right += dt_ms
        if self.last_spawn_basic_right >= self.interval_basic_right:
            self.elementos.append(BasicElement(is_left_side=False, window=self))
            self.last_spawn_basic_right = 0
            self.interval_basic_right = self.interval_basic_base + random.randint(200, 400)

        self.last_spawn_left += dt_ms
        if self.last_spawn_left >= self.interval_left:
            self.elementos.append(ElementoEsquerda(window=self))
            self.last_spawn_left = 0

        self.last_spawn_right += dt_ms
        if self.last_spawn_right >= self.interval_right:
            self.elementos.append(ElementoDireita(window=self))
            self.last_spawn_right = 0

        for elemento in self.elementos:
            elemento.update(delta_time)

        self.elemento_fixo.update(delta_time)

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.ESCAPE:
            arcade.close_window()


def main():
    window = PerspectivaWindow(WIDTH, HEIGHT)
    arcade.run()


if __name__ == '__main__':
    main()