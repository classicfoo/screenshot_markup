import tkinter as tk
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import sys
import win32clipboard
from io import BytesIO

class ImageViewer(tk.Tk):
    def __init__(self, image_path=None):
        super().__init__()
        self.title("Screenshot Markup")

        # Bind Ctrl+C to copy the image to clipboard
        self.bind("<Control-c>", self.copy_image)

        # Image handling
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.original_image = None
        #self.load_image(image_path)
        self.final_image = None

        # Setting up the canvas
        self.canvas = tk.Canvas(self, cursor="cross")
        self.canvas.pack(fill="both", expand=True)

        # Bind mouse events for drawing
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

        # Bind Ctrl+V to load image from clipboard
        self.bind("<Control-v>", lambda event: self.load_image_from_clipboard())

        # Display the image
        self.update_image()

    def copy_image(self, event):
        if self.final_image is not None:
            copy_to_clipboard(self.final_image)

    def load_image(self, image_path):
        # Try to get image from clipboard
        img = get_image_from_clipboard()
        if img is None and image_path is not None:
            # Load the image from file
            img = Image.open(image_path)
        self.original_image = img
    
    def load_image_from_clipboard(self):
        img = get_image_from_clipboard()
        if img is not None:
            self.original_image = img
            self.update_image()
        else:
            print("No image found in clipboard.")

    def update_image(self):
        if self.original_image is not None:
            self.final_image = add_shadow(self.original_image)
            self.display_image = ImageTk.PhotoImage(self.final_image)

            # Update canvas with the new image
            self.canvas.create_image(0, 0, anchor="nw", image=self.display_image)
            self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

            # Resize the window to fit the final image
            window_width = self.final_image.width
            window_height = self.final_image.height
            self.geometry(f"{window_width}x{window_height}")

    def on_button_press(self, event):
        # Convert event coordinates to canvas coordinates
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        # Create a rectangle (initially a single point)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x + 1, self.start_y + 1, outline="yellow")

    def on_move_press(self, event):
        curX, curY = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        if self.rect:
            # Determine the smallest and largest x and y coordinates
            x0, y0 = min(self.start_x, curX), min(self.start_y, curY)
            x1, y1 = max(self.start_x, curX), max(self.start_y, curY)
            self.canvas.coords(self.rect, x0, y0, x1, y1)
            self.canvas.itemconfig(self.rect, outline="yellow", fill="yellow", stipple="gray50")


    def on_button_release(self, event):
        if self.rect and self.original_image is not None:
            end_x, end_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            
            # Determine the smallest and largest x and y coordinates
            x0, y0 = min(self.start_x, end_x) - 20, min(self.start_y, end_y) - 20
            x1, y1 = max(self.start_x, end_x) - 20, max(self.start_y, end_y) - 20

            # Create a transparent overlay
            overlay = Image.new('RGBA', self.original_image.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)

            # Draw the semi-transparent rectangle on the overlay
            semi_transparent_color = (255, 255, 0, 128)  # Yellow, 50% opacity
            draw.rectangle([x0, y0, x1, y1], fill=semi_transparent_color)

            # Combine original image with overlay
            self.original_image = Image.alpha_composite(self.original_image.convert('RGBA'), overlay)

            self.update_image()


# Existing functions
def get_image_from_clipboard():
    win32clipboard.OpenClipboard()
    try:
        # Check if the clipboard contains an image format
        if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
            data = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
            image = Image.open(BytesIO(data))
            return image
        else:
            print("No image in clipboard")
            return None
    finally:
        win32clipboard.CloseClipboard()


def add_shadow(image, offset=(13, 13), background_color='white', shadow_color='grey', border=20, blur_radius=8):
    # Ensure the image has an alpha channel
    if image.mode != 'RGBA':
        image = image.convert('RGBA')

    # Create an image for the shadow
    total_width = image.width + abs(offset[0]) + 2*border
    total_height = image.height + abs(offset[1]) + 2*border
    shadow = Image.new('RGBA', (total_width, total_height), background_color)

    # Place the shadow, with blur
    shadow_left = border + max(offset[0], 0)
    shadow_top = border + max(offset[1], 0)
    shadow.paste(shadow_color, [shadow_left, shadow_top, shadow_left + image.width, shadow_top + image.height])
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    # Paste the original image on top of the shadow
    image_left = border - min(offset[0], 0)
    image_top = border - min(offset[1], 0)
    shadow.paste(image, (image_left, image_top), image)

    return shadow

def copy_to_clipboard(image):
    output = BytesIO()
    image.convert('RGB').save(output, 'BMP')
    data = output.getvalue()[14:]  # Remove the 14-byte BMP header
    output.close()

    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    win32clipboard.CloseClipboard()

def load_image_from_clipboard(self):
    img = get_image_from_clipboard()
    if img is not None:
        self.original_image = img
        self.update_image()
    else:
        print("No image found in clipboard.")


def main(image_path=None):
    app = ImageViewer(image_path)
    app.mainloop()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
