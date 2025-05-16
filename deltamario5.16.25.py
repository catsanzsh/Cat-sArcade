import tkinter as tk
import winsound
import threading
import time

class SMB3Clone:
    def __init__(self, root):
        self.root = root
        self.root.title("SMB3 Clone - No PNG, Just Tk & Beeps!")
        self.width = 512
        self.height = 448

        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height, bg="black")
        self.canvas.pack()

        # Game state
        self.state = "overworld"  # "overworld" or "level"
        self.current_level = 0
        self.score = 0
        self.lives = 3

        # Player properties
        self.player_vel = [0, 0]
        self.gravity = 0.6
        self.jump_strength = -10
        self.on_ground = False

        self.keys = set()
        self.root.bind("<KeyPress>", self.key_down)
        self.root.bind("<KeyRelease>", self.key_up)

        # Make a text label for instructions or info
        self.info_label = self.canvas.create_text(
            self.width // 2,
            20,
            text="SMB3 Clone: Arrow Keys/Space, Enter to select level\nPress Q to Quit",
            fill="white",
            font=("Helvetica", 14),
        )

        # Start on the overworld map
        self.start_overworld()

        # Start background music thread (infinite loop)
        self.play_music = True
        music_thread = threading.Thread(target=self.background_music, daemon=True)
        music_thread.start()

        # Begin main loop at ~60 FPS
        self.update_game()

    # ===================================================
    #                SOUND AND MUSIC
    # ===================================================

    def beep(self, freq=440, dur=100):
        """Simple wrapper to handle beep safely."""
        try:
            winsound.Beep(freq, dur)
        except:
            pass

    def short_boop(self):
        """Short beep for moves, collisions, etc."""
        self.beep(392, 40)

    def jump_sound(self):
        self.beep(784, 60)

    def coin_sound(self):
        self.beep(1046, 80)

    def gameover_sound(self):
        # A quick downward scale
        for f in [523, 415, 349, 261]:
            self.beep(f, 120)

    def background_music(self):
        """
        A rough beep-based approximation of the SMB3 Overworld theme in a loop.
        This is purely for fun and definitely not the real thing.
        To keep the main loop from freezing, it runs in a separate thread.
        """
        # Frequencies (approx NES pitch) and durations (in milliseconds).
        # This is a VERY simplified snippet, repeated in a loop.
        # Real SMB3 is more complex, but we keep it short to avoid a huge code block.
        theme_notes = [
            (659, 150), (659, 150), (0, 100),    # E E (pause)
            (659, 150), (0, 100),               # E (pause)
            (523, 150), (659, 150), (587, 300), # C E D
            (0, 150),                           # pause
            (494, 150), (0, 150), (523, 150),   # B (pause) C
            (0, 150), (392, 300), (0, 300),
        ]

        while self.play_music:
            for freq, dur in theme_notes:
                if not self.play_music:
                    break
                if freq > 0:
                    try:
                        winsound.Beep(freq, dur)
                    except:
                        pass
                else:
                    time.sleep(dur / 1000.0)  # rest
            time.sleep(0.1)  # tiny gap before repeating

    # ===================================================
    #                     INPUT
    # ===================================================

    def key_down(self, event):
        self.keys.add(event.keysym)

    def key_up(self, event):
        self.keys.discard(event.keysym)

    # ===================================================
    #                  OVERWORLD
    # ===================================================

    def start_overworld(self):
        """Draw a minimal SMB3-like map with a few 'nodes' for levels."""
        self.canvas.delete("all")
        self.state = "overworld"

        # Overworld background color
        self.canvas.config(bg="darkgreen")

        # Re-draw the info label on top
        self.info_label = self.canvas.create_text(
            self.width // 2,
            20,
            text="SMB3 Overworld - Arrow Keys to move cursor, Enter to enter level",
            fill="white",
            font=("Helvetica", 14),
        )

        # Some nodes to represent levels
        self.level_positions = [(100, 300), (200, 250), (300, 200), (400, 250), (500, 300)]
        self.nodes = []
        for x, y in self.level_positions:
            node = self.canvas.create_rectangle(
                x - 10, y - 10, x + 10, y + 10, fill="white"
            )
            self.nodes.append(node)

        # Lines connecting nodes
        for i in range(len(self.level_positions) - 1):
            x1, y1 = self.level_positions[i]
            x2, y2 = self.level_positions[i + 1]
            self.canvas.create_line(x1, y1, x2, y2, fill="white", width=2)

        # A simple "cursor" to show which level is selected
        self.selected_node = self.current_level
        sx, sy = self.level_positions[self.selected_node]
        self.cursor = self.canvas.create_polygon(
            sx, sy - 25, sx - 10, sy - 15, sx + 10, sy - 15,
            fill="red"
        )

    def update_overworld(self):
        moved = False
        if "Left" in self.keys and self.selected_node > 0:
            self.selected_node -= 1
            self.keys.discard("Left")
            moved = True
        if "Right" in self.keys and self.selected_node < len(self.level_positions) - 1:
            self.selected_node += 1
            self.keys.discard("Right")
            moved = True

        # Update cursor if we moved
        if moved:
            self.short_boop()
            sx, sy = self.level_positions[self.selected_node]
            self.canvas.coords(
                self.cursor,
                sx, sy - 25, sx - 10, sy - 15, sx + 10, sy - 15
            )

        # Enter level
        if "Return" in self.keys:
            self.keys.discard("Return")
            self.current_level = self.selected_node
            self.start_level()

    # ===================================================
    #                     LEVEL
    # ===================================================

    def start_level(self):
        """Set up a simple platformer level with tile-like shapes."""
        self.canvas.delete("all")
        self.state = "level"
        self.canvas.config(bg="skyblue")

        # Info overlay
        self.info_label = self.canvas.create_text(
            self.width // 2,
            20,
            text=f"Level {self.current_level + 1} - Lives: {self.lives}  Score: {self.score}",
            fill="white",
            font=("Helvetica", 14),
        )

        # Ground: a row of 'bricks' at the bottom
        self.tiles = []
        tile_width = 32
        tile_height = 32
        for i in range(self.width // tile_width):
            rect = self.canvas.create_rectangle(
                i * tile_width, self.height - tile_height,
                (i + 1) * tile_width, self.height,
                fill="sienna", outline="black"
            )
            self.tiles.append(rect)

        # A few floating blocks
        block_positions = [(100, 300), (132, 300), (300, 250), (332, 250)]
        for (bx, by) in block_positions:
            rect = self.canvas.create_rectangle(
                bx, by, bx + tile_width, by + tile_height,
                fill="sienna", outline="black"
            )
            self.tiles.append(rect)

        # Player (small 16x24 rectangle to approximate Mario)
        self.player = self.canvas.create_rectangle(
            50, self.height - tile_height - 24,
            66, self.height - tile_height,
            fill="red", outline="black"
        )
        self.player_vel = [0, 0]
        self.on_ground = False

        # A coin to collect
        self.coin = self.canvas.create_oval(
            320, 200, 336, 216, fill="yellow", outline="black"
        )

        # A simple 'enemy'
        self.enemy = self.canvas.create_rectangle(
            200, self.height - tile_height - 16,
            216, self.height - tile_height,
            fill="green", outline="black"
        )

    def update_level(self):
        """Handle keyboard input, movement, collisions, etc."""
        # Horizontal movement
        accel = 0
        if "Left" in self.keys:
            accel = -3
        elif "Right" in self.keys:
            accel = 3

        self.player_vel[0] = accel

        # Jump
        if "space" in self.keys and self.on_ground:
            self.player_vel[1] = self.jump_strength
            self.jump_sound()

        # Gravity
        self.player_vel[1] += self.gravity

        # Move player
        self.canvas.move(self.player, self.player_vel[0], self.player_vel[1])

        # Check for collisions with level tiles
        self.on_ground = False
        px1, py1, px2, py2 = self.canvas.coords(self.player)
        for tile in self.tiles:
            tx1, ty1, tx2, ty2 = self.canvas.coords(tile)
            # Basic bounding-box overlap
            if not (px2 < tx1 or px1 > tx2 or py2 < ty1 or py1 > ty2):
                # We have a collision; figure out from which side
                overlap_w = min(px2, tx2) - max(px1, tx1)
                overlap_h = min(py2, ty2) - max(py1, ty1)
                if abs(overlap_w) < abs(overlap_h):
                    # Collided horizontally
                    if px1 < tx1:
                        # Player on left
                        self.canvas.move(self.player, -overlap_w, 0)
                    else:
                        # Player on right
                        self.canvas.move(self.player, overlap_w, 0)
                    self.player_vel[0] = 0
                else:
                    # Collided vertically
                    if py1 < ty1:
                        # Player above tile
                        self.canvas.move(self.player, 0, -overlap_h)
                        self.player_vel[1] = 0
                        if abs(self.player_vel[1]) < 0.1:
                            self.on_ground = True
                    else:
                        # Player below tile
                        self.canvas.move(self.player, 0, overlap_h)
                        self.player_vel[1] = 0

        # Collect coin if overlap
        if self.coin is not None:
            if self.check_overlap(self.player, self.coin):
                self.coin_sound()
                self.canvas.delete(self.coin)
                self.coin = None
                self.score += 100
                self.update_info_text()

        # Check enemy collision
        if self.check_overlap(self.player, self.enemy):
            # For simplicity, just do "game over" immediately
            self.lives -= 1
            if self.lives <= 0:
                self.game_over()
            else:
                # Reset position
                self.canvas.coords(self.player, 50, self.height - 56, 66, self.height - 32)
            self.update_info_text()

    def update_info_text(self):
        """Refresh displayed text for score/lives/etc."""
        self.canvas.itemconfig(
            self.info_label,
            text=f"Level {self.current_level + 1} - Lives: {self.lives}  Score: {self.score}",
        )

    def game_over(self):
        self.gameover_sound()
        self.canvas.create_text(
            self.width // 2, self.height // 2,
            text="GAME OVER!",
            fill="white",
            font=("Helvetica", 32, "bold")
        )
        # Return to overworld after a pause
        def return_to_overworld():
            if self.lives <= 0:
                self.lives = 3
                self.score = 0
            self.start_overworld()

        self.root.after(2000, return_to_overworld)

    def check_overlap(self, obj1, obj2):
        """Returns True if two canvas items overlap."""
        x1, y1, x2, y2 = self.canvas.coords(obj1)
        a1, b1, a2, b2 = self.canvas.coords(obj2)
        if x2 < a1 or x1 > a2 or y2 < b1 or y1 > b2:
            return False
        return True

    # ===================================================
    #                MAIN UPDATE LOOP
    # ===================================================

    def update_game(self):
        """Called ~60 times per second via after(16, ...)"""
        if "q" in self.keys or "Q" in self.keys:
            self.play_music = False
            self.root.destroy()
            return

        if self.state == "overworld":
            self.update_overworld()
        elif self.state == "level":
            self.update_level()

        # Keep running at about 60 FPS
        self.root.after(16, self.update_game)


def main():
    root = tk.Tk()
    game = SMB3Clone(root)
    root.mainloop()

if __name__ == "__main__":
    main()
