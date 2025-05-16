import tkinter as tk


class MarioGame:
    def __init__(self, root):
        self.root = root
        self.width = 600
        self.height = 400
        self.root.title("Simple Mario Clone")
        self.canvas = tk.Canvas(root, width=self.width, height=self.height,
                               bg="skyblue")
        self.canvas.pack()

        # Level elements
        self.ground = self.canvas.create_rectangle(
            0, self.height - 40, self.width, self.height, fill="sienna"
        )
        self.player = self.canvas.create_rectangle(
            50, self.height - 70, 70, self.height - 40, fill="red"
        )

        # Define simple levels with enemy and coin positions
        self.levels = [
            {
                "enemy": (300, self.height - 60, 320, self.height - 40),
                "coin": (500, self.height - 70, 520, self.height - 50),
            },
            {
                "enemy": (200, self.height - 60, 220, self.height - 40),
                "coin": (400, self.height - 70, 420, self.height - 50),
            },
            {
                "enemy": (100, self.height - 60, 120, self.height - 40),
                "coin": (350, self.height - 70, 370, self.height - 50),
            },
        ]
        self.current_level = 0
        self.setup_level(self.current_level)

        # Physics
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
        self.update()

    def setup_level(self, index):
        """Create enemy and coin objects for the given level."""
        if hasattr(self, "enemy"):
            self.canvas.delete(self.enemy)
        if hasattr(self, "coin") and self.coin:
            self.canvas.delete(self.coin)
        level = self.levels[index]
        self.enemy = self.canvas.create_rectangle(*level["enemy"], fill="green")
        self.coin = self.canvas.create_oval(*level["coin"], fill="yellow")

    def next_level(self):
        self.current_level += 1
        if self.current_level >= len(self.levels):
            self.canvas.create_text(
                self.width / 2,
                self.height / 2,
                text="You Win!",
                fill="white",
                font=("Helvetica", 32),
            )
            self.root.unbind("<KeyPress>")
            self.root.unbind("<KeyRelease>")
            self.keys.clear()
        else:
            self.setup_level(self.current_level)
            self.canvas.coords(
                self.player,
                50,
                self.height - 70,
                70,
                self.height - 40,
            )
            self.player_vel = [0, 0]
            self.on_ground = False

    def key_down(self, event):
        self.keys.add(event.keysym)

    def key_up(self, event):
        self.keys.discard(event.keysym)

    def apply_gravity(self):
        self.player_vel[1] += self.gravity

    def move_player(self):
        if "Left" in self.keys:
            self.player_vel[0] = -3
        elif "Right" in self.keys:
            self.player_vel[0] = 3
        else:
            self.player_vel[0] = 0

        if "space" in self.keys and self.on_ground:
            self.player_vel[1] = self.jump_strength

        self.apply_gravity()

        self.canvas.move(self.player, self.player_vel[0], self.player_vel[1])
        x1, y1, x2, y2 = self.canvas.coords(self.player)

        if y2 >= self.height - 40:
            self.canvas.move(self.player, 0, self.height - 40 - y2)
            self.player_vel[1] = 0
            self.on_ground = True
        else:
            self.on_ground = False

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
            self.next_level()

        if self.overlap(self.player, self.enemy):
            self.canvas.create_text(
                self.width / 2,
                self.height / 2,
                text="Game Over",
                fill="white",
                font=("Helvetica", 32),
            )
            self.root.unbind("<KeyPress>")
            self.root.unbind("<KeyRelease>")
            self.keys.clear()
            return False
        return True

    def update(self):
        self.move_player()
        continue_game = self.check_collisions()
        if continue_game:
            self.root.after(16, self.update)


def main():
    root = tk.Tk()
    game = MarioGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
