import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.mouse import Mouse
import board
import microcontroller
import digitalio
import time
import pwmio  # PWM support

# Relative HID units per report; host pointer acceleration also affects speed.
MOUSE_STEP = 4
MOUSE_INTERVAL = 0.01  # Repeat movement at most every 10 ms.
DEBOUNCE_INTERVAL = 0.02  # Require a stable switch state for 20 ms.
SCAN_INTERVAL = 0.005

bl_pwm_value = 32767   		#Midpoint
ad_pwm_value = 32767       	#Midpoint

try:
    # Set up USB keyboard, mouse, and media-control devices.
    mouse = Mouse(usb_hid.devices)
    kbd = Keyboard(usb_hid.devices)
    layout = KeyboardLayoutUS(kbd)
    consumer_control = ConsumerControl(usb_hid.devices)

except Exception as e:
    # Log initialization failures.
    print(f"Initialization failed: {e}")
    # Reset the RP2040.
    microcontroller.reset()

# Initialize GP22.
gp22 = digitalio.DigitalInOut(board.GP22)
gp22.direction = digitalio.Direction.OUTPUT
# Set GP22 low (False).
gp22.value = False

# Initialize GP19.
gp19 = digitalio.DigitalInOut(board.GP19)
gp19.direction = digitalio.Direction.OUTPUT
# Set GP19 low (False).
gp19.value = False

gp21 = digitalio.DigitalInOut(board.GP21)
gp21.direction = digitalio.Direction.OUTPUT
# Set GP21 low (False).
gp21.value = False

# Optional GP22 PWM output for a breathing LED effect.
# gp22_pwm = pwmio.PWMOut(board.GP22, frequency=5000, duty_cycle=0)

# Initialize backlight PWM.
BL_PWM_RP = pwmio.PWMOut(board.GP20, frequency=5000, duty_cycle=5000)

# Initialize audio PWM.
AD_PWM_RP = pwmio.PWMOut(board.GP18, frequency=5000, duty_cycle=32700)

def toggle_gp22():
    gp22.value = not gp22.value
    print(f"GP22 state toggled to: {gp22.value}")
    kbd.press(Keycode.CAPS_LOCK)
    kbd.release(Keycode.CAPS_LOCK)

def start_breathing_light():
    tmp_time = 0
    stop_loop = True  # Flag controlling the wait loop.
    kbd = None  # Initialize the local keyboard reference.
    gp22_temp = gp22.value #Save the current Caps Lock indicator state.

    for i in range(1,10+1):
        gp22.value = not gp22.value
        # print("GP22 TEST:",gp22.value)
        time.sleep(0.3)

    try:
        while stop_loop:
            tmp_time +=1

            if tmp_time >= 255:
                gp22.value = not gp22.value
                # print("GP22 IS:",gp22.value)
                tmp_time = 0

            current_keys = set(scan_keyboard())

            # Handle keys that are pressed
            for key in current_keys:
                if key is not None:
                    time.sleep(0.2)
                    if key is not None:
                        if kbd:
                            kbd.release_all()

                        gp22.value = gp22_temp
                        gp21.value = not gp21.value
                        stop_loop = False  # Exit the wait loop.
                        break
    finally:
        if kbd:
            kbd.release_all()
            gp22.value = gp22_temp


def toggle_gp19():
    gp19.value = not gp19.value
    # print(f"GP19 state toggled to: {gp19.value}")

def toggle_gp21():
    # The display-off wait loop blocks normal mouse updates.
    release_mouse_buttons()
    gp21.value = not gp21.value
    # print(f"GP21 state toggled to: {gp21.value}")
    start_breathing_light()

def ad_pwm_down():
    global ad_pwm_value
    if ad_pwm_value <= 0:
        ad_pwm_value = 0
    else:
        ad_pwm_value -= 6553
    ad_pwm_value = min(max(ad_pwm_value, 0), 65535)
    # Update the duty cycle.
    AD_PWM_RP.duty_cycle = ad_pwm_value
    print("pwm_value == ", ad_pwm_value)

def ad_pwm_up():
    global ad_pwm_value
    if ad_pwm_value >= 65535:
        ad_pwm_value = 65535
    else:
        ad_pwm_value += 6553
    ad_pwm_value = min(max(ad_pwm_value, 0), 65535)
    # Update the duty cycle.
    AD_PWM_RP.duty_cycle = ad_pwm_value
    print("pwm_value == ", ad_pwm_value)

#The backlight uses an NPN pull-down: a higher PWM duty cycle dims it.
# Therefore, bl_pwm_up lowers the duty cycle and bl_pwm_down raises it.
def bl_pwm_up():
    global bl_pwm_value
    if bl_pwm_value <= 0:
        bl_pwm_value = 0
    else:
        bl_pwm_value -= 6553
    bl_pwm_value = min(max(bl_pwm_value, 0), 65535)
    # Update the duty cycle.
    BL_PWM_RP.duty_cycle = bl_pwm_value
    print("pwm_value == ",bl_pwm_value)

def bl_pwm_down():
    global bl_pwm_value
    if bl_pwm_value >= 65535:
        bl_pwm_value = 65535
    else:
        bl_pwm_value += 6553
    bl_pwm_value = min(max(bl_pwm_value, 0), 65535)
    # Update the duty cycle.
    BL_PWM_RP.duty_cycle = bl_pwm_value
    print("pwm_value == ",bl_pwm_value)

def shift_left_bracket():
    kbd.press(Keycode.SHIFT, Keycode.LEFT_BRACKET)
    # kbd.release(Keycode.SHIFT)
    kbd.release_all()

def shift_right_bracket():
    kbd.press(Keycode.SHIFT, Keycode.RIGHT_BRACKET)
    # kbd.release(Keycode.SHIFT)
    kbd.release_all()

def shift_backslash():
    kbd.press(Keycode.SHIFT, Keycode.BACKSLASH)
    # kbd.release(Keycode.SHIFT)
    kbd.release_all()

def shift_grave_accent():
    kbd.press(Keycode.SHIFT, Keycode.GRAVE_ACCENT)
    # kbd.release(Keycode.SHIFT)
    kbd.release_all()

def lock_screen():
#Send Super+L; the host desktop determines the lock/sleep behavior.
    kbd.press(Keycode.WINDOWS, Keycode.L)
    kbd.release_all()

def scan_previous_track():
    consumer_control.press(ConsumerControlCode.SCAN_PREVIOUS_TRACK)
    consumer_control.release()

def play_pause():
    consumer_control.press(ConsumerControlCode.PLAY_PAUSE)
    consumer_control.release()

def scan_next_track():
    consumer_control.press(ConsumerControlCode.SCAN_NEXT_TRACK)
    consumer_control.release()

# Define custom function keys using a dictionary
CUSTOM_KEYS = {
    # Add more custom keys as needed
    "FN_KEY"                : -100,
    "FN_MUTE"               : -101,
    "FN_VOLUME_DOWN"        : -102,
    "FN_VOLUME_UP"          : -103,
    "FN_LOCK_SCREEN"        : -104,
    "FN_BL_CONTROL_SCREEN"  : -105,
    "FN_BL_PWM_DOWN"        : -106,
    "FN_BL_PWM_UP"          : -107,
    "SHIFT_GRAVE_ACCENT"    : -108,
    "SHIFT_BACKSLASH"       : -109,
    "SHIFT_LEFT_BRACKET"    : -110,
    "SHIFT_RIGHT_BRACKET"   : -111,
    "MOUSE_LEFT_BUTTON"         : -112,
    "MOUSE_RIGHT_BUTTON"        : -113,
    "MOUSE_UP"                  : -114,
    "MOUSE_LEFT"                : -115,
    "MOUSE_DOWN"                : -116,
    "MOUSE_RIGHT"               : -117
}

SPECIAL_KEY_FUNCTIONS = {
    CUSTOM_KEYS["FN_MUTE"]                  : toggle_gp19,
    CUSTOM_KEYS["FN_VOLUME_DOWN"]           : ad_pwm_down,
    CUSTOM_KEYS["FN_VOLUME_UP"]             : ad_pwm_up,
    CUSTOM_KEYS["FN_LOCK_SCREEN"]           : lock_screen,
    CUSTOM_KEYS["FN_BL_CONTROL_SCREEN"]     : toggle_gp21,
    CUSTOM_KEYS["FN_BL_PWM_DOWN"]           : bl_pwm_down,
    CUSTOM_KEYS["FN_BL_PWM_UP"]             : bl_pwm_up,
    CUSTOM_KEYS["SHIFT_GRAVE_ACCENT"]       : shift_grave_accent,
    CUSTOM_KEYS["SHIFT_BACKSLASH"]          : shift_backslash,
    CUSTOM_KEYS["SHIFT_LEFT_BRACKET"]       : shift_left_bracket,
    CUSTOM_KEYS["SHIFT_RIGHT_BRACKET"]      : shift_right_bracket,
    Keycode.CAPS_LOCK                       : toggle_gp22,
    ConsumerControlCode.SCAN_PREVIOUS_TRACK : scan_previous_track,
    ConsumerControlCode.PLAY_PAUSE          : play_pause,
    ConsumerControlCode.SCAN_NEXT_TRACK     : scan_next_track
}

# Define the number of rows and columns
NUM_ROWS = 7
NUM_COLS = 10

# Define the key map for the keyboard matrix
KEY_MAP = [
    #col0                       col1                                col2                                    col3                                col4                                        col5                                    col6                                    col7                                    col8                        col9
    # Dedicated controls only: arrows, L, R, X, Y, B, A (columns 0-9).
    [Keycode.UP_ARROW, Keycode.LEFT_ARROW, Keycode.DOWN_ARROW, Keycode.RIGHT_ARROW,
     CUSTOM_KEYS["MOUSE_LEFT_BUTTON"], CUSTOM_KEYS["MOUSE_RIGHT_BUTTON"],
     CUSTOM_KEYS["MOUSE_UP"], CUSTOM_KEYS["MOUSE_LEFT"],
     CUSTOM_KEYS["MOUSE_DOWN"], CUSTOM_KEYS["MOUSE_RIGHT"]],  # row 0
    [Keycode.ONE,               Keycode.TWO,                        Keycode.THREE,                          Keycode.FOUR,                       Keycode.FIVE,                               Keycode.SIX,                            Keycode.SEVEN,                          Keycode.EIGHT,                          Keycode.NINE,               Keycode.ZERO],          # row 1
    [Keycode.Q,                 Keycode.W,                          Keycode.E,                              Keycode.R,                          Keycode.T,                                  Keycode.Y,                              Keycode.U,                              Keycode.I,                              Keycode.O,                  Keycode.P],             # row 2
    [Keycode.A,                 Keycode.S,                          Keycode.D,                              Keycode.F,                          Keycode.G,                                  Keycode.H,                              Keycode.J,                              Keycode.K,                              Keycode.L,                  Keycode.BACKSPACE],     # row 3
    [Keycode.Z,                 Keycode.X,                          Keycode.C,                              Keycode.V,                          Keycode.B,                                  Keycode.N,                              Keycode.M,                              Keycode.FORWARD_SLASH,                  Keycode.ENTER,              None],                  # row 4
    [Keycode.TAB,               Keycode.CAPS_LOCK,                  Keycode.MINUS,                          Keycode.EQUALS,                     Keycode.SEMICOLON,                          Keycode.QUOTE,                          Keycode.COMMA,                          Keycode.PERIOD,                         Keycode.SHIFT,              None],                  # row 5
    [CUSTOM_KEYS["FN_KEY"],     Keycode.CONTROL,                    Keycode.LEFT_ALT,                       Keycode.PRINT_SCREEN,               Keycode.SPACE,                              Keycode.PAUSE,                          Keycode.RIGHT_ALT,                      Keycode.WINDOWS,                        CUSTOM_KEYS["FN_KEY"],      None]                   # row 6
]


# Define the FN key map for the keyboard matrix
FN_MAP = [
    #col0                       col1                                col2                                    col3                                col4                                        col5                                    col6                                    col7                                    col8                        col9
    # Dedicated controls only: arrows, L, R, X, Y, B, A (columns 0-9).
    [Keycode.UP_ARROW, Keycode.LEFT_ARROW, Keycode.DOWN_ARROW, Keycode.RIGHT_ARROW,
     CUSTOM_KEYS["MOUSE_LEFT_BUTTON"], CUSTOM_KEYS["MOUSE_RIGHT_BUTTON"],
     CUSTOM_KEYS["MOUSE_UP"], CUSTOM_KEYS["MOUSE_LEFT"],
     CUSTOM_KEYS["MOUSE_DOWN"], CUSTOM_KEYS["MOUSE_RIGHT"]],  # row 0
    [Keycode.F1,                Keycode.F2,                         Keycode.F3,                             Keycode.F4,                         Keycode.F5,                                 Keycode.F6,                             Keycode.F7,                             Keycode.F8,                             Keycode.F9,                 Keycode.F10],           # row 1
    [Keycode.ESCAPE,            CUSTOM_KEYS["FN_MUTE"],             CUSTOM_KEYS["FN_VOLUME_DOWN"],          CUSTOM_KEYS["FN_VOLUME_UP"],        ConsumerControlCode.SCAN_PREVIOUS_TRACK,    ConsumerControlCode.PLAY_PAUSE,         ConsumerControlCode.SCAN_NEXT_TRACK,    CUSTOM_KEYS["FN_LOCK_SCREEN"],          Keycode.F11,                Keycode.F12],           # row 2
    [Keycode.GRAVE_ACCENT,      CUSTOM_KEYS["SHIFT_GRAVE_ACCENT"],  Keycode.BACKSLASH,                      CUSTOM_KEYS["SHIFT_BACKSLASH"],     CUSTOM_KEYS["SHIFT_LEFT_BRACKET"],          CUSTOM_KEYS["SHIFT_RIGHT_BRACKET"],     Keycode.LEFT_BRACKET,                   Keycode.RIGHT_BRACKET,                  Keycode.L,                  Keycode.DELETE],        # row 3
    [Keycode.INSERT,            Keycode.HOME,                       CUSTOM_KEYS["FN_BL_CONTROL_SCREEN"],    Keycode.END,                        Keycode.PAGE_UP,                            Keycode.PAGE_DOWN,                      Keycode.SCROLL_LOCK,                    Keycode.FORWARD_SLASH,                  Keycode.ENTER,              None],                  # row 4
    [Keycode.TAB,               Keycode.CAPS_LOCK,                  CUSTOM_KEYS["FN_BL_PWM_DOWN"],          CUSTOM_KEYS["FN_BL_PWM_UP"],        Keycode.SEMICOLON,                          Keycode.QUOTE,                          Keycode.COMMA,                          Keycode.PERIOD,                         Keycode.SHIFT,              None],                  # row 5
    [CUSTOM_KEYS["FN_KEY"],     Keycode.CONTROL,                    Keycode.LEFT_ALT,                       Keycode.PRINT_SCREEN,               Keycode.SPACE,                              Keycode.PAUSE,                          Keycode.RIGHT_ALT,                      Keycode.WINDOWS,                        CUSTOM_KEYS["FN_KEY"],      None]                   # row 6
]

# Define the row and column pins
row_pins = [board.GP16, board.GP10, board.GP11, board.GP12, board.GP13, board.GP14, board.GP15]
col_pins = [board.GP0,  board.GP1,  board.GP2,  board.GP3,  board.GP4,  board.GP5,  board.GP6,  board.GP7,  board.GP8,  board.GP9]

# Initialize row and column pins
row_gpio = [digitalio.DigitalInOut(pin) for pin in row_pins]
col_gpio = [digitalio.DigitalInOut(pin) for pin in col_pins]

# Set rows as inputs with pull-up and columns as outputs set to low
for row in row_gpio:
    row.direction = digitalio.Direction.INPUT
    row.pull = digitalio.Pull.UP


for col in col_gpio:
    col.direction = digitalio.Direction.OUTPUT
    col.value = False

# Debounce each physical switch without blocking scans of other keys.
raw_key_states = [[False] * NUM_COLS for _ in range(NUM_ROWS)]
stable_key_states = [[False] * NUM_COLS for _ in range(NUM_ROWS)]
key_change_times = [[0.0] * NUM_COLS for _ in range(NUM_ROWS)]


def scan_keyboard():
    keys_pressed = []
    fn_active = False

    for col_index, col_pin in enumerate(col_gpio):
        col_pin.value = True
        for row_index, row_pin in enumerate(row_gpio):
            row_pin.pull = digitalio.Pull.DOWN
            pressed = row_pin.value
            now = time.monotonic()
            if pressed != raw_key_states[row_index][col_index]:
                raw_key_states[row_index][col_index] = pressed
                key_change_times[row_index][col_index] = now
            elif now - key_change_times[row_index][col_index] >= DEBOUNCE_INTERVAL:
                stable_key_states[row_index][col_index] = pressed

            if stable_key_states[row_index][col_index]:
                if KEY_MAP[row_index][col_index] == CUSTOM_KEYS["FN_KEY"]:
                    fn_active = True
                keys_pressed.append((row_index, col_index))
        col_pin.value = False

    active_map = FN_MAP if fn_active else KEY_MAP
    return [active_map[row][col] for row, col in keys_pressed]


mouse_buttons = 0
last_mouse_move = 0.0
last_mouse_direction = (0, 0)


def release_mouse_buttons():
    global mouse_buttons
    mouse.release_all()
    mouse_buttons = 0


def update_mouse(current_keys):
    global mouse_buttons, last_mouse_move, last_mouse_direction
    buttons = 0
    if CUSTOM_KEYS["MOUSE_LEFT_BUTTON"] in current_keys:
        buttons |= Mouse.LEFT_BUTTON
    if CUSTOM_KEYS["MOUSE_RIGHT_BUTTON"] in current_keys:
        buttons |= Mouse.RIGHT_BUTTON

    # Send button transitions only; holding L/R supports dragging.
    released = mouse_buttons & ~buttons
    pressed = buttons & ~mouse_buttons
    if released:
        mouse.release(released)
    if pressed:
        mouse.press(pressed)
    mouse_buttons = buttons

    dx = (int(CUSTOM_KEYS["MOUSE_RIGHT"] in current_keys)
          - int(CUSTOM_KEYS["MOUSE_LEFT"] in current_keys))
    dy = (int(CUSTOM_KEYS["MOUSE_DOWN"] in current_keys)
          - int(CUSTOM_KEYS["MOUSE_UP"] in current_keys))
    direction = (dx, dy)
    now = time.monotonic()
    # A new direction moves immediately; a held direction repeats on a timer.
    # Opposing directions cancel; perpendicular directions allow diagonal motion.
    if direction != (0, 0):
        if direction != last_mouse_direction or now - last_mouse_move >= MOUSE_INTERVAL:
            mouse.move(x=dx * MOUSE_STEP, y=dy * MOUSE_STEP)
            last_mouse_move = now
    last_mouse_direction = direction


def run_keyboard():
    previous_keys = set()
    while True:
        current_keys = set(scan_keyboard())
        update_mouse(current_keys)

        # Handle keys that were released.
        for key in previous_keys - current_keys:
            if key is not None and key >= 0:
                kbd.release(key)

        # Handle newly pressed keyboard and function keys.
        for key in current_keys - previous_keys:
            if key is not None:
                if key in SPECIAL_KEY_FUNCTIONS:
                    SPECIAL_KEY_FUNCTIONS[key]()
                elif key >= 0:  # Exclude custom mouse and Fn actions.
                    kbd.press(key)

        previous_keys = current_keys
        time.sleep(SCAN_INTERVAL)


try:
    run_keyboard()
except Exception as e:
    print(f"An error occurred: {e}")
    # Attempt each cleanup independently, even if another HID device fails.
    for release in (kbd.release_all, release_mouse_buttons, consumer_control.release):
        try:
            release()
        except Exception as cleanup_error:
            print(f"Error during cleanup: {cleanup_error}")
    microcontroller.reset()
