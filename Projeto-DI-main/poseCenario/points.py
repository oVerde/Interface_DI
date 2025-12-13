import math

BASE_POINTS = 0.25
BASE_SIZE = 0.0004
BASE_SIZE_R = 3000
BASE_SIZE_L = 4500

def get_speed(accuracy):
    return BASE_POINTS * accuracy

def get_size(accuracy):
    return BASE_SIZE * accuracy

def get_right(accuracy):
    if accuracy == 0: return 3000
    return max(1400, 1600)

def get_left(accuracy):
    if accuracy == 0: return 3000
    return max(1400, 1700)

BASE_SPEED_Z = 15.0

def get_z_speed(accuracy):
    return BASE_SPEED_Z * accuracy

def get_spawn_delay(accuracy):
    if accuracy <= 0: return 2000
    return max(200, 3000 / accuracy)