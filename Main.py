
import os
import math
import wave
import struct
import random

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import (
    Color, Rectangle, Ellipse, Line, Triangle,
    RoundedRectangle
)
from kivy.metrics import dp


class FlappyBird(Widget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        Window.fullscreen = 'auto'
        Window.clearcolor = (0.35, 0.75, 0.95, 1)

        self.gravity = 0
        self.bird_y = 0
        self.velocity = 0
        self.pipes = []
        self.clouds = []
        self.score = 0
        self.state = "ready"
        self.spawn_timer = 0
        self.cloud_timer = 0

        self.score_label = Label(
            text="0",
            font_size=dp(42),
            bold=True,
            color=(1, 1, 1, 1),
            outline_width=2,
            outline_color=(0, 0, 0, 1),
            size_hint=(None, None),
            size=(dp(120), dp(65)),
            pos_hint={"center_x": 0.5, "top": 0.98}
        )
        self.add_widget(self.score_label)

        self.message = Label(
            text="FLAPPY BIRD\n\nTap to Start",
            font_size=dp(27),
            bold=True,
            halign="center",
            valign="middle",
            color=(1, 1, 1, 1),
            outline_width=2,
            outline_color=(0, 0, 0, 1),
            size_hint=(0.9, 0.3),
            pos_hint={"center_x": 0.5, "center_y": 0.55}
        )
        self.add_widget(self.message)

        self.bind(size=self.reset_game, pos=self.redraw)
        Clock.schedule_interval(self.update, 1 / 60)

        self.create_sounds()
        self.reset_game()

    def create_sounds(self):
        self.sounds = {}

        try:
            folder = App.get_running_app().user_data_dir

            for name, freq in [
                ("jump", 650),
                ("score", 950),
                ("hit", 180)
            ]:
                path = os.path.join(folder, name + ".wav")

                if not os.path.exists(path):
                    rate = 22050
                    duration = 0.12
                    samples = int(rate * duration)

                    with wave.open(path, "w") as wav:
                        wav.setnchannels(1)
                        wav.setsampwidth(2)
                        wav.setframerate(rate)

                        data = bytearray()

                        for i in range(samples):
                            t = i / rate
                            fade = 1 - i / samples
                            value = int(
                                9000 * fade *
                                math.sin(2 * math.pi * freq * t)
                            )
                            data.extend(struct.pack("<h", value))

                        wav.writeframes(data)

                self.sounds[name] = SoundLoader.load(path)

        except Exception:
            self.sounds = {}

    def play_sound(self, name):
        sound = self.sounds.get(name)

        if sound:
            sound.stop()
            sound.play()

    def reset_game(self, *args):
        if self.width < 10 or self.height < 10:
            return

        self.bird_x = self.x + self.width * 0.28
        self.bird_y = self.y + self.height * 0.55

        self.velocity = 0
        self.score = 0
        self.pipes = []
        self.spawn_timer = 0
        self.state = "ready"

        self.clouds = [
            [
                self.x + random.uniform(0, self.width),
                self.y + random.uniform(
                    self.height * 0.65,
                    self.height * 0.95
                ),
                random.uniform(0.7, 1.3)
            ]
            for _ in range(5)
        ]

        self.score_label.text = "0"
        self.message.text = "FLAPPY BIRD\n\nTap to Start"
        self.redraw()

    def flap(self):
        self.velocity = self.height * 0.72
        self.play_sound("jump")

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)

        if self.state == "ready":
            self.state = "playing"
            self.message.text = ""
            self.flap()

        elif self.state == "playing":
            self.flap()

        elif self.state == "over":
            self.reset_game()

        return True

    def update(self, dt):
        if self.width < 10 or self.height < 10:
            return

        dt = min(dt, 0.033)

        # Move clouds
        for cloud in self.clouds:
            cloud[0] -= self.width * 0.045 * cloud[2] * dt

            if cloud[0] < self.x - 100:
                cloud[0] = self.x + self.width + 50
                cloud[1] = self.y + random.uniform(
                    self.height * 0.65,
                    self.height * 0.95
                )

        if self.state == "playing":
            self.velocity -= self.height * 1.8 * dt
            self.bird_y += self.velocity * dt

            # Create pipes
            self.spawn_timer += dt

            if self.spawn_timer >= 1.75:
                self.spawn_timer = 0

                gap_center = self.y + random.uniform(
                    self.height * 0.40,
                    self.height * 0.72
                )

                self.pipes.append({
                    "x": self.x + self.width + 30,
                    "gap": gap_center,
                    "scored": False
                })

            pipe_speed = self.width * 0.48
            gap_size = self.height * 0.27
            pipe_width = self.width * 0.17

            bird_radius = self.width * 0.035
            bird_left = self.bird_x - bird_radius
            bird_right = self.bird_x + bird_radius
            bird_bottom = self.bird_y - bird_radius
            bird_top = self.bird_y + bird_radius

            for pipe in self.pipes:
                pipe["x"] -= pipe_speed * dt

                left = pipe["x"]
                right = left + pipe_width

                bottom_top = pipe["gap"] - gap_size / 2
                top_bottom = pipe["gap"] + gap_size / 2

                horizontal = (
                    bird_right > left and bird_left < right
                )

                if horizontal:
                    if (
                        bird_bottom < bottom_top
                        or bird_top > top_bottom
                    ):
                        self.game_over()
                        break

                if not pipe["scored"] and right < self.bird_x:
                    pipe["scored"] = True
                    self.score += 1
                    self.score_label.text = str(self.score)
                    self.play_sound("score")

            self.pipes = [
                p for p in self.pipes
                if p["x"] > self.x - pipe_width - 20
            ]

            ground = self.y + self.height * 0.075

            if bird_bottom < ground or bird_top > self.y + self.height:
                self.game_over()

        self.redraw()

    def game_over(self):
        if self.state != "playing":
            return

        self.state = "over"
        self.play_sound("hit")

        self.message.text = (
            "GAME OVER\n\n"
            f"Score: {self.score}\n\n"
            "Tap to Restart"
        )

    def draw_cloud(self, x, y, scale):
        Color(1, 1, 1, 0.85)

        r = self.width * 0.035 * scale

        Ellipse(pos=(x, y), size=(r * 2, r * 1.5))
        Ellipse(pos=(x + r, y + r * 0.3),
                size=(r * 2.2, r * 1.8))
        Ellipse(pos=(x + r * 2, y),
                size=(r * 2, r * 1.5))

    def draw_bird(self):
        x = self.bird_x
        y = self.bird_y
        r = self.width * 0.035

        angle = max(-25, min(30, self.velocity / self.height * 7))

        # Body
        Color(1, 0.78, 0.05)
        Ellipse(pos=(x-r, y-r), size=(r*2, r*2))

        # Wing
        Color(1, 0.57, 0.03)
        Ellipse(
            pos=(x-r*0.65, y-r*0.35),
            size=(r*1.15, r*0.85)
        )

        # Eye
        Color(1, 1, 1)
        Ellipse(pos=(x+r*0.15, y+r*0.25),
                size=(r*0.75, r*0.75))

        Color(0.05, 0.05, 0.05)
        Ellipse(pos=(x+r*0.48, y+r*0.40),
                size=(r*0.27, r*0.27))

        # Beak
        Color(1, 0.32, 0.02)
        Triangle(points=[
            x+r*0.75, y,
            x+r*1.65, y-r*0.12,
            x+r*0.75, y-r*0.35
        ])

    def draw_pipe(self, x, gap):
        w = self.width * 0.17
        h = self.height
        gap_size = h * 0.27

        bottom_top = gap - gap_size / 2
        top_bottom = gap + gap_size / 2

        # Pipe body
        Color(0.12, 0.65, 0.12)
        Rectangle(
            pos=(x, self.y + h * 0.075),
            size=(w, bottom_top - self.y - h * 0.075)
        )

        Rectangle(
            pos=(x, top_bottom),
            size=(w, self.y + h - top_bottom)
        )

        # Pipe highlights
        Color(0.28, 0.88, 0.20)
        Rectangle(
            pos=(x+w*0.15, self.y+h*0.075),
            size=(w*0.16, bottom_top-self.y-h*0.075)
        )

        Rectangle(
            pos=(x+w*0.15, top_bottom),
            size=(w*0.16, self.y+h-top_bottom)
        )

        # Pipe caps
        Color(0.08, 0.48, 0.08)
        Rectangle(
            pos=(x-w*0.08, bottom_top-w*0.18),
            size=(w*1.16, w*0.18)
        )

        Rectangle(
            pos=(x-w*0.08, top_bottom),
            size=(w*1.16, w*0.18)
        )

        Color(0.30, 0.90, 0.20)
        Line(
            rectangle=(
                x, self.y+h*0.075,
                w, bottom_top-self.y-h*0.075
            ),
            width=1
        )

    def redraw(self, *args):
        if self.width < 10 or self.height < 10:
            return

        self.canvas.clear()

        with self.canvas:
            h = self.height
            w = self.width
            ground = h * 0.075

            # Sky
            Color(0.35, 0.75, 0.95)
            Rectangle(pos=self.pos, size=self.size)

            # Sun
            Color(1, 0.88, 0.30)
            Ellipse(
                pos=(self.x+w*0.77, self.y+h*0.78),
                size=(w*0.13, w*0.13)
            )

            # Clouds
            for cloud in self.clouds:
                self.draw_cloud(*cloud)

            # Pipes
            for pipe in self.pipes:
                self.draw_pipe(pipe["x"], pipe["gap"])

            # Ground
            Color(0.85, 0.72, 0.37)
            Rectangle(
                pos=(self.x, self.y),
                size=(w, ground)
            )

            Color(0.35, 0.72, 0.18)
            Rectangle(
                pos=(self.x, self.y+ground),
                size=(w, h*0.025)
            )

            # Ground pattern
            Color(0.68, 0.51, 0.25)
            for i in range(12):
                px = self.x + i*w/12
                Rectangle(
                    pos=(px, self.y+ground*0.35),
                    size=(w*0.025, ground*0.12)
                )

            # Bird
            if self.state != "over":
                self.draw_bird()
            else:
                self.draw_bird()


class FlappyApp(App):

    def build(self):
        self.title = "Flappy Bird"
        return FlappyBird()


if __name__ == "__main__":
    FlappyApp().run()
