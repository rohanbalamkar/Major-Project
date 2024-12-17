import tkinter as tk
import cv2
import threading
from pyzbar.pyzbar import decode
from PIL import Image, ImageTk
import pyttsx3  # For text-to-speech
import time  # For cooldown mechanism

# Initialize Text-to-Speech engine
tts_engine = pyttsx3.init(driverName='espeak')
tts_engine.setProperty('rate', 150)  # Adjust speaking speed

# Navigation data with directions and video file paths for arrows
navigation_data = {
    "Checkpoint 1": {
        "Kitchen": ("Go right for 5 meters", "/home/oggy/Rohan/Navigation_Camera/python/right.mp4"),
        "Washroom": ("Go left for 2 meters", "/home/oggy/Rohan/Navigation_Camera/python/left.mp4"),
        "Hall": ("Go straight", "/home/oggy/Rohan/Navigation_Camera/python/straight.mp4"),
    },
    "Checkpoint 2": {
        "Kitchen": ("Go straight for 3 meters", "/home/oggy/Rohan/Navigation_Camera/python/straight.mp4"),
        "Washroom": ("Turn right and go 1 meter", "/home/oggy/Rohan/Navigation_Camera/python/right.mp4"),
        "Hall": ("Turn left and go 4 meters", "/home/oggy/Rohan/Navigation_Camera/python/left.mp4"),
    },
}

# Initialize the main application window
root = tk.Tk()
root.title("Navigation System")
root.geometry("800x600")
root.config(bg="lightblue")

selected_destination = tk.StringVar(value="")
scanning_active = True  # Global variable to control QR scanning thread
recent_qr_codes = set()  # Track recently scanned QR codes
qr_cooldown_time = 3  # Cooldown time in seconds

# Function to announce directions via TTS
def announce_direction(direction_text):
    tts_engine.say(direction_text)
    tts_engine.runAndWait()

# Function to update direction with a directional video
def show_direction(checkpoint):
    destination = selected_destination.get()
    if not destination:
        direction_label.config(text="Please select a destination.", font=("Helvetica", 14, "bold"))
        return

    direction_text, video_path = navigation_data.get(checkpoint, {}).get(destination, ("No direction available.", ""))
    direction_label.config(text=f"Direction to {destination}: {direction_text}", font=("Helvetica", 16, "bold"))

    # Announce the direction via voice
    announce_direction(direction_text)

    # Play the video for direction
    play_video(video_path)

# Function to start scanning for QR codes
def start_qr_scanning():
    global scanning_active, recent_qr_codes
    cap = cv2.VideoCapture(0)  # Initialize the camera

    while scanning_active:
        ret, frame = cap.read()
        if not ret:
            break

        # Decode QR codes in the frame
        qr_codes = decode(frame)
        current_time = time.time()
        
        for qr_code in qr_codes:
            checkpoint = qr_code.data.decode('utf-8')
            
            # Skip already processed QR codes within the cooldown period
            if checkpoint in recent_qr_codes:
                continue

            if checkpoint in navigation_data:
                # Show direction if a valid QR code is scanned
                show_direction(checkpoint)
                
                # Add this QR code to the recently scanned set
                recent_qr_codes.add(checkpoint)
                
                # Schedule removal of the QR code from the set after cooldown
                threading.Timer(qr_cooldown_time, lambda: recent_qr_codes.remove(checkpoint)).start()

        # Display the camera feed in the corner
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_image = ImageTk.PhotoImage(Image.fromarray(frame).resize((200, 150)))  # Smaller camera feed
        camera_label.config(image=frame_image)
        camera_label.image = frame_image

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# Start the QR code scanning in a new thread
def start_scanner_thread():
    global scanning_active
    scanning_active = True
    scanner_thread = threading.Thread(target=start_qr_scanning, daemon=True)
    scanner_thread.start()

# Stop the QR code scanning thread
def stop_scanner_thread():
    global scanning_active
    scanning_active = False

# Function to play the directional video in the label
def play_video(video_path):
    cap = cv2.VideoCapture(video_path)

    def stream_video():
        ret, frame = cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Resize the video to a larger size
            resized_frame = cv2.resize(frame, (400, 300))  # Adjust width and height as needed
            
            frame_image = ImageTk.PhotoImage(Image.fromarray(resized_frame))
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
    stop_scanner_thread()  # Stop the scanning thread
    selected_destination.set("")
    direction_label.config(text="Please select a destination and scan QR code.", font=("Helvetica", 16), fg="black")
    arrow_label.config(image="")
    camera_label.config(image="")  # Clear the camera feed

# UI Layout
# Left frame for destination buttons
left_frame = tk.Frame(root, width=400, height=400, bg="lightblue")
left_frame.pack(side="left", fill="y")

# Buttons with larger font and size in the left frame
tk.Label(left_frame, text="Select Destination:", font=("Helvetica", 22, "bold"), bg="lightblue").pack(pady=20)

tk.Button(left_frame, text="Kitchen", font=("Helvetica", 18), bg="green", fg="white", width=20, height=2,
          command=lambda: navigate("Kitchen", "green")).pack(pady=15)
tk.Button(left_frame, text="Hall", font=("Helvetica", 18), bg="white", fg="black", width=20, height=2,
          command=lambda: navigate("Hall", "black")).pack(pady=15)
tk.Button(left_frame, text="Washroom", font=("Helvetica", 18), bg="yellow", fg="black", width=20, height=2,
          command=lambda: navigate("Washroom", "yellow")).pack(pady=15)

# Reset button at the bottom of the left frame
tk.Button(left_frame, text="Reset", font=("Helvetica", 18), bg="red", fg="white", width=20, height=2, command=reset_navigation).pack(pady=30)

# Right frame for displaying directions
right_frame = tk.Frame(root, width=400, height=400, bg="white", relief="solid", bd=2)
right_frame.pack(side="right", fill="both", expand=True)

# Display for directions in right frame
direction_label = tk.Label(right_frame, text="Please select a destination and scan QR code.", font=("Helvetica", 16))
direction_label.pack(pady=20)

# Label for directional video
arrow_label = tk.Label(right_frame)
arrow_label.pack(pady=20)

# Small camera feed label in the bottom-left corner
camera_label = tk.Label(root, bg="black")  # Black background for better visibility
camera_label.place(x=10, y=450, width=200, height=150)  # Positioned at the bottom-left corner

root.mainloop()