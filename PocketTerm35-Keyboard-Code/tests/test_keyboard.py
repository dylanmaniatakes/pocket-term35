"""Desktop regression tests with simulated GPIO/HID; no hardware required."""
import ast
import contextlib
import io
from pathlib import Path
import string
import sys
import types
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "code.py"


class StopSimulation(BaseException):
    pass


class FakeTime:
    def __init__(self):
        self.now = 0.0
        self.sleeps = []

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


class FakeHID:
    LEFT_BUTTON = 1
    RIGHT_BUTTON = 2

    def __init__(self, devices):
        self.events = []
        self.buttons = 0

    def press(self, *keys):
        self.events.append(("press", *keys))

    def release(self, *keys):
        self.events.append(("release", *keys))

    def release_all(self):
        self.events.append(("release_all",))

    def move(self, *, x, y):
        self.events.append(("move", x, y))


class Matrix:
    ROW_PINS = [16, 10, 11, 12, 13, 14, 15]

    def __init__(self):
        self.pressed = set()
        self.pins = {}

    def digital_in_out(self, number):
        matrix = self

        class Pin:
            direction = None
            pull = None
            output = False

            @property
            def value(self):
                if number in matrix.ROW_PINS:
                    row = matrix.ROW_PINS.index(number)
                    return any((row, col) in matrix.pressed
                               and matrix.pins[col].output for col in range(10))
                return self.output

            @value.setter
            def value(self, value):
                self.output = value

        pin = Pin()
        self.pins[number] = pin
        return pin


def module(**attrs):
    return types.SimpleNamespace(**attrs)


def load_firmware():
    tree = ast.parse(SOURCE.read_text(), filename=str(SOURCE))
    # Load the actual initialization, mappings, scanner, and handlers, but run
    # the infinite main loop explicitly with bounded simulated inputs below.
    main = tree.body.pop()
    assert isinstance(main, ast.Try)
    names = sorted({n.attr for n in ast.walk(tree)
                    if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)
                    and n.value.id == "Keycode"})
    keycodes = {name: 100 + index for index, name in enumerate(names)}
    keycodes.update({letter: 4 + index for index, letter in enumerate(string.ascii_uppercase)})
    keycodes.update(UP_ARROW=82, DOWN_ARROW=81, LEFT_ARROW=80, RIGHT_ARROW=79)
    keycode = module(**keycodes)
    matrix = Matrix()
    clock = FakeTime()
    reset = []
    modules = {
        "usb_hid": module(devices=[]),
        "board": module(**{"GP%d" % i: i for i in range(30)}),
        "microcontroller": module(reset=lambda: reset.append(True)),
        "digitalio": module(DigitalInOut=matrix.digital_in_out,
                            Direction=module(INPUT=0, OUTPUT=1),
                            Pull=module(UP=1, DOWN=0)),
        "pwmio": module(PWMOut=lambda *a, **kw: module(**kw)),
        "time": clock,
        "adafruit_hid": module(),
        "adafruit_hid.keyboard": module(Keyboard=FakeHID),
        "adafruit_hid.keycode": module(Keycode=keycode),
        "adafruit_hid.consumer_control": module(ConsumerControl=FakeHID),
        "adafruit_hid.consumer_control_code": module(ConsumerControlCode=module(
            SCAN_PREVIOUS_TRACK=182, PLAY_PAUSE=205, SCAN_NEXT_TRACK=181)),
        "adafruit_hid.keyboard_layout_us": module(KeyboardLayoutUS=lambda kbd: None),
        "adafruit_hid.mouse": module(Mouse=FakeHID),
    }
    scope = {}
    with patch.dict(sys.modules, modules):
        exec(compile(tree, str(SOURCE), "exec"), scope)
    return scope, matrix, clock, reset, main


class KeyboardTests(unittest.TestCase):
    def setUp(self):
        self.fw, self.matrix, self.clock, self.resets, self.main = load_firmware()
        self.mouse = self.fw["mouse"]
        self.kbd = self.fw["kbd"]

    def scan(self, positions):
        self.matrix.pressed = set(positions)
        self.fw["scan_keyboard"]()
        self.clock.now += 0.021
        return set(self.fw["scan_keyboard"]())

    def update(self, positions):
        self.fw["update_mouse"](self.scan(positions))

    def run_frames(self, frames):
        frames = iter(frames)

        def sleep(seconds):
            self.clock.now += seconds
            try:
                self.matrix.pressed = set(next(frames))
            except StopIteration:
                raise StopSimulation()

        self.matrix.pressed = set(next(frames))
        self.clock.sleep = sleep
        with self.assertRaises(StopSimulation):
            self.fw["run_keyboard"]()

    def test_each_direction_with_either_fn_key(self):
        for fn in [set(), {(6, 0)}, {(6, 8)}]:
            for col, movement in [(9, (4, 0)), (7, (-4, 0)), (6, (0, -4)), (8, (0, 4))]:
                with self.subTest(fn=fn, col=col):
                    self.update(set())
                    self.mouse.events.clear()
                    self.update({(0, col)} | fn)
                    self.assertEqual(self.mouse.events, [("move", *movement)])

    def test_held_movement_repeats_and_release_stops(self):
        keys = self.scan({(0, 9)})
        self.fw["update_mouse"](keys)
        self.clock.now += 0.005
        self.fw["update_mouse"](keys)
        self.assertEqual(len(self.mouse.events), 1)
        self.clock.now += 0.006
        self.fw["update_mouse"](keys)
        self.assertEqual(self.mouse.events, [("move", 4, 0)] * 2)
        self.update(set())
        self.clock.now += 1.0
        self.fw["update_mouse"](set())
        self.assertEqual(len(self.mouse.events), 2)

    def test_diagonal_and_opposite_directions(self):
        self.update({(0, 9), (0, 6)})
        self.assertEqual(self.mouse.events, [("move", 4, -4)])
        self.update({(0, 9), (0, 7)})
        self.update({(0, 6), (0, 8)})
        self.update({(0, 6), (0, 7), (0, 8), (0, 9)})
        self.assertEqual(len(self.mouse.events), 1)

    def test_clicks_hold_until_release_without_repeated_presses(self):
        for col, button in [(4, 1), (5, 2)]:
            self.mouse.events.clear()
            self.update({(0, col)})
            self.update({(0, col)})
            self.update(set())
            self.assertEqual(self.mouse.events, [("press", button), ("release", button)])

    def test_drag_and_independent_button_release(self):
        self.update({(0, 4), (0, 5), (0, 9)})
        self.update({(0, 5)})
        self.update(set())
        self.assertEqual(self.mouse.events, [
            ("press", 3), ("move", 4, 0), ("release", 1), ("release", 2)])

    def test_fn_transitions_do_not_interrupt_drag(self):
        for fn in [set(), {(6, 0)}, {(6, 8)}, set()]:
            self.update({(0, 4), (0, 9)} | fn)
        self.update(set())
        self.assertEqual(self.mouse.events[0], ("press", 1))
        self.assertEqual(self.mouse.events[-1], ("release", 1))
        self.assertEqual(sum(e[0] == "move" for e in self.mouse.events), 4)
        self.assertEqual(sum(e[0] == "press" for e in self.mouse.events), 1)

    def test_typing_keys_and_arrows_do_not_move_mouse(self):
        positions = {(3, 0), (4, 4), (4, 1), (2, 5), (3, 8), (2, 3)}
        keys = self.scan(positions)
        self.assertEqual(keys, {self.fw["Keycode"].__dict__[k] for k in "ABXYLR"})
        self.fw["update_mouse"](keys)
        for fn in [set(), {(6, 0)}]:
            keys = self.scan({(0, i) for i in range(4)} | fn)
            self.assertTrue({79, 80, 81, 82}.issubset(keys))
            self.fw["update_mouse"](keys)
        self.assertEqual(self.mouse.events, [])

    def test_press_and_release_bounce_are_filtered_without_sleep(self):
        scan = self.fw["scan_keyboard"]
        for pressed in [True, False, True, False, True]:
            self.matrix.pressed = {(0, 4)} if pressed else set()
            self.assertEqual(scan(), [])
            self.clock.now += 0.004
        self.clock.now += 0.021
        held = set(scan())
        self.fw["update_mouse"](held)
        for pressed in [False, True, False]:
            self.matrix.pressed = {(0, 4)} if pressed else set()
            self.assertEqual(set(scan()), held)
            self.clock.now += 0.004
        self.clock.now += 0.021
        self.assertEqual(scan(), [])
        self.fw["update_mouse"](set())
        self.assertEqual(self.mouse.events, [("press", 1), ("release", 1)])
        self.assertEqual(self.clock.sleeps, [])

    def test_keys_debounce_independently(self):
        self.scan({(0, 9)})
        for positions in [{(0, 9), (3, 0)}, {(0, 9)}, {(0, 9), (3, 0)}]:
            self.matrix.pressed = positions
            self.clock.now += 0.005
            self.assertEqual(set(self.fw["scan_keyboard"]()), {self.fw["CUSTOM_KEYS"]["MOUSE_RIGHT"]})
        self.clock.now += 0.021
        self.assertEqual(len(self.fw["scan_keyboard"]()), 2)
        self.assertTrue(all(not self.matrix.pins[c].output for c in range(10)))

    def test_main_loop_typing_and_mouse_can_coexist(self):
        held = {(0, 9), (0, 4), (3, 0), (0, 0)}
        self.run_frames([held] * 20 + [set()] * 20)
        self.assertEqual(set(self.kbd.events), {("press", 4), ("press", 82),
                                              ("release", 4), ("release", 82)})
        self.assertEqual(self.mouse.events[0], ("press", 1))
        self.assertEqual(self.mouse.events[-1], ("release", 1))
        self.assertGreater(sum(e[0] == "move" for e in self.mouse.events), 2)

    def test_dedicated_controls_never_type_letters(self):
        positions = {(0, col) for col in range(4, 10)}
        self.run_frames([positions] * 10 + [positions | {(6, 0)}] * 10
                        + [positions] * 10 + [set()] * 10)
        self.assertEqual(self.kbd.events, [])
        self.assertEqual(self.mouse.events, [("press", 3), ("release", 3)])

    def test_existing_fn_shortcut_still_dispatches(self):
        self.assertFalse(self.fw["gp19"].value)
        self.run_frames([{(6, 0), (2, 1)}] * 10 + [set()] * 10)
        self.assertTrue(self.fw["gp19"].value)
        self.assertEqual(self.mouse.events, [])

    def test_display_wait_releases_mouse_and_can_resume_drag(self):
        self.update({(0, 4)})
        waited = []
        self.fw["start_breathing_light"] = lambda: waited.append(self.fw["mouse_buttons"])
        self.fw["toggle_gp21"]()
        self.assertEqual(waited, [0])
        self.update({(0, 4)})
        self.assertEqual(self.mouse.events, [("press", 1), ("release_all",), ("press", 1)])

    def test_exception_cleanup_releases_mouse_even_if_keyboard_fails(self):
        self.update({(0, 4)})

        def fail():
            raise RuntimeError("simulated USB failure")

        self.kbd.release_all = fail
        self.fw["run_keyboard"] = fail
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(ast.Module(body=[self.main], type_ignores=[]), str(SOURCE), "exec"), self.fw)
        self.assertEqual(self.mouse.events[-1], ("release_all",))
        self.assertEqual(self.fw["consumer_control"].events, [("release",)])
        self.assertEqual(self.resets, [True])


if __name__ == "__main__":
    unittest.main()
