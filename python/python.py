import tkinter as tk
import cv2
import threading
from pyzbar.pyzbar import decode
from PIL import Image, ImageTk

# Navigation data with directions and video file paths for arrows
navigation_data = {
    "Checkpoint 1": {
        "Kitchen": ("Go right for 5 meters", "right.mp4"),
        "Washroom": ("Go left for 2 meters", "left.mp4"),
        "Hall": ("Go straight", "straight.mp4"),
    },
    "Checkpoint 2": {
        "Kitchen": ("Go straight for 3 meters", "straight.mp4"),
        "Washroom": ("Turn right and go 1 meter", "right.mp4"),
        "Hall": ("Turn left and go 4 meters", "left.mp4"),
    },
}

# Initialize the main application window
root = tk.Tk()
root.title("Navigation System")
root.geometry("800x400")
root.config(bg="lightblue")

selected_destination = tk.StringVar(value="")

# Function to update direction with a directional video
def show_direction(checkpoint):
    destination = selected_destination.get()
    if not destination:
        direction_label.config(text="Please select a destination.", font=("Helvetica", 14, "bold"))
        return

    direction_text, video_path = navigation_data.get(checkpoint, {}).get(destination, ("No direction available.", ""))
    direction_label.config(text=f"Direction to {destination}: {direction_text}", font=("Helvetica", 16, "bold"))

    # Play the video for direction
    play_video(video_path)

# Function to start scanning for QR codes
def start_qr_scanning():
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        for qr_code in decode(frame):
            checkpoint = qr_code.data.decode('utf-8')
            if checkpoint in navigation_data:
                show_direction(checkpoint)
        cv2.imshow("QR Code Scanner", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

# Start the QR code scanning in a new thread
def start_scanner_thread():
    scanner_thread = threading.Thread(target=start_qr_scanning, daemon=True)
    scanner_thread.start()

# Function to play the directional video in the label
def play_video(video_path):
    cap = cv2.VideoCapture(video_path)
    
    def stream_video():
        ret, frame = cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_image = ImageTk.PhotoImage(Image.fromarray(frame).resize((100, 100)))
            arrow_label.config(image=frame_image)
            arrow_label.image = frame_image
            root.after(50, stream_video)
        else:
            cap.release()
    
    stream_video()

# Function to set destination, start scanning, and color the direction display
def navigate(destination, color):
    selected_destination.set(destination)
    direction_label.config(text=f"Navigating to {destination}...", font=("Helvetica", 16, "italic"), fg=color)
    start_scanner_thread()

# Function to reset the navigation system
def reset_navigation():
    selected_destination.set("")
    direction_label.config(text="Please select a destination and scan QR code.", font=("Helvetica", 16), fg="black")
    arrow_label.config(image="")

# UI Layout
# Left frame for destination buttons
left_frame = tk.Frame(root, width=400, height=400, bg="lightblue")
left_frame.pack(side="left", fill="y")

# Buttons with color and alignment in left frame
tk.Label(left_frame, text="Select Destination:", font=("Helvetica", 18, "bold"), bg="lightblue").pack(pady=10)

tk.Button(left_frame, text="Kitchen", font=("Helvetica", 14), bg="green", fg="white", width=15,
          command=lambda: navigate("Kitchen", "green")).pack(pady=10)
tk.Button(left_frame, text="Hall", font=("Helvetica", 14), bg="white", fg="black", width=15,
          command=lambda: navigate("Hall", "black")).pack(pady=10)
tk.Button(left_frame, text="Washroom", font=("Helvetica", 14), bg="yellow", fg="black", width=15,
          command=lambda: navigate("Washroom", "yellow")).pack(pady=10)

# Reset button at the bottom of the left frame
tk.Button(left_frame, text="Reset", font=("Helvetica", 14), bg="red", fg="white", width=15, command=reset_navigation).pack(pady=20)

# Right frame for displaying directions
right_frame = tk.Frame(root, width=400, height=400, bg="white", relief="solid", bd=2)
right_frame.pack(side="right", fill="both", expand=True)

# Display for directions in right frame
direction_label = tk.Label(right_frame, text="Please select a destination and scan QR code.", font=("Helvetica", 16))
direction_label.pack(pady=20)

# Label for directional video
arrow_label = tk.Label(right_frame)
arrow_label.pack(pady=20)

root.mainloop()
