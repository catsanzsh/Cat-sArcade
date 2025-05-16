import tkinter as tk
import winsound  # On Linux/Mac, use os.system('beep') or similar
import time

class MarioGame:
    """Simple Mario-style game with overworld, one level, and beeps/boops for sound."""

    def __init__(self, root):
        self.root = root
        self.width = 600
        self.height = 400
        self.root.title("Simple Mario Clone")
        self.canvas = tk.Canvas(
            root, width=self.width, height=self.height, bg="skyblue"
        )
        self.canvas.pack()

        # state management
        self.state = "overworld"  # "overworld" or "level"
        self.current_level = 0

        # physics
        self.player_vel = [0, 0]
        self.gravity = 0.5
        self.jump_strength = -10
        self.on_ground = False

        self.score = 0
        self.score_text = self.canvas.create_text(
            50, 20, text="Score: 0", fill="white", font=("Helvetica", 16)
        )

        self.keys = set()
        self.root.bind("<KeyPress>", self.key_down)
        self.root.bind("<KeyRelease>", self.key_up)

        self.start_overworld()

    # ---- SOUND ENGINE ----
    def beep(self, freq=523, dur=100):
        try:
            winsound.Beep(freq, dur)
        except Exception:
            pass  # Cross-platform: ignore if not available

    def boop(self, freq=330, dur=60):
        try:
            winsound.Beep(freq, dur)
        except Exception:
            pass

    def jump_sound(self):
        self.beep(784, 60)
    def coin_sound(self):
        self.beep(1046, 80)
    def gameover_sound(self):
        for f in [523, 415, 349, 261]:
            self.boop(f, 80)
    def move_sound(self):
        self.boop(392, 40)

    # ---- CONTROLS ----
    def key_down(self, event):
        self.keys.add(event.keysym)
    def key_up(self, event):
        self.keys.discard(event.keysym)

    def apply_gravity(self):
        self.player_vel[1] += self.gravity

    # ---------- Level logic ----------
    def start_level(self):
        """Set up a very small platform level."""
        self.canvas.delete("all")
        self.state = "level"

        self.ground = self.canvas.create_rectangle(
            0, self.height - 40, self.width, self.height, fill="sienna"
        )
        self.player = self.canvas.create_rectangle(
            50, self.height - 70, 70, self.height - 40, fill="red"
        )
        self.enemy = self.canvas.create_rectangle(
            300, self.height - 60, 320, self.height - 40, fill="green"
        )
        self.coin = self.canvas.create_oval(
            500, self.height - 70, 520, self.height - 50, fill="yellow"
        )

        self.score_text = self.canvas.create_text(
            50, 20, text=f"Score: {self.score}", fill="white", font=("Helvetica", 16)
        )

        self.player_vel = [0, 0]
        self.on_ground = False

        self.update_level()

    def move_player(self):
        moved = False
        if "Left" in self.keys:
            self.player_vel[0] = -3
            moved = True
        elif "Right" in self.keys:
            self.player_vel[0] = 3
            moved = True
        else:
            self.player_vel[0] = 0

        if "space" in self.keys and self.on_ground:
            self.player_vel[1] = self.jump_strength
            self.jump_sound()

        self.apply_gravity()

        self.canvas.move(self.player, self.player_vel[0], self.player_vel[1])
        x1, y1, x2, y2 = self.canvas.coords(self.player)

        if y2 >= self.height - 40:
            self.canvas.move(self.player, 0, self.height - 40 - y2)
            self.player_vel[1] = 0
            self.on_ground = True
        else:
            self.on_ground = False
        if moved and self.on_ground:
            self.move_sound()

    def overlap(self, item1, item2):
        if not self.canvas.coords(item1) or not self.canvas.coords(item2):
            return False
        x1, y1, x2, y2 = self.canvas.coords(item1)
        a1, b1, a2, b2 = self.canvas.coords(item2)
        return x1 < a2 and x2 > a1 and y1 < b2 and y2 > b1

    def check_collisions(self):
        if self.coin and self.overlap(self.player, self.coin):
            self.canvas.delete(self.coin)
            self.coin = None
            self.score += 1
            self.canvas.itemconfig(self.score_text, text=f"Score: {self.score}")
            self.coin_sound()

        if self.overlap(self.player, self.enemy):
            self.canvas.create_text(
                self.width / 2,
                self.height / 2,
                text="Game Over",
                fill="white",
                font=("Helvetica", 32),
            )
            self.gameover_sound()
            self.root.unbind("<KeyPress>")
            self.root.unbind("<KeyRelease>")
            self.keys.clear()
            return False
        return True

    def update_level(self):
        self.move_player()
        continue_game = self.check_collisions()
        if continue_game:
            self.root.after(16, self.update_level)
        else:
            # back to overworld after a brief pause
            self.root.after(1000, self.start_overworld)

    # ---------- Overworld logic ----------
    def start_overworld(self):
        """Display a very simple overworld with three level nodes."""
        self.canvas.delete("all")
        self.state = "overworld"

        # ensure key bindings are active (may have been unbound on game over)
        self.root.bind("<KeyPress>", self.key_down)
        self.root.bind("<KeyRelease>", self.key_up)

        # positions of nodes
        self.level_positions = [(100, 300), (300, 250), (500, 300)]
        self.nodes = []
        for x, y in self.level_positions:
            self.nodes.append(
                self.canvas.create_oval(x - 15, y - 15, x + 15, y + 15, fill="white")
            )

        # path lines between nodes
        self.canvas.create_line(100, 300, 300, 250, fill="white", width=2)
        self.canvas.create_line(300, 250, 500, 300, fill="white", width=2)

        self.selected = self.current_level
        x, y = self.level_positions[self.selected]
        self.cursor = self.canvas.create_rectangle(
            x - 10, y - 25, x + 10, y - 5, fill="red"
        )

        self.canvas.create_text(
            self.width / 2,
            50,
            text="Overworld - Press Enter to Play",
            fill="white",
            font=("Helvetica", 16),
        )

        self.update_overworld()

    def update_overworld(self):
        moved = False
        if "Left" in self.keys and self.selected > 0:
            self.selected -= 1
            moved = True
            self.keys.discard("Left")
        if "Right" in self.keys and self.selected < len(self.level_positions) - 1:
            self.selected += 1
            moved = True
            self.keys.discard("Right")
        if moved:
            x, y = self.level_positions[self.selected]
            self.canvas.coords(self.cursor, x - 10, y - 25, x + 10, y - 5)
            self.move_sound()

        if "Return" in self.keys:
            self.keys.discard("Return")
            self.current_level = self.selected
            self.start_level()
            return

        self.root.after(16, self.update_overworld)


def main():
    root = tk.Tk()
    game = MarioGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
