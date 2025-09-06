import cv2
import datetime
import threading
import time
import sys

class VideoRecorder:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.is_recording = False
        self.video_writer = None
        self.cap = None
        
        # 16:9 resolution (you can change these values)
        self.width = 1280   # 1280x720 (HD)
        self.height = 720   # You can also use 1920x1080 (Full HD)
    
    def setup_camera(self):
        """Configure camera with robust error handling"""
        print(f"Video: Attempting to open camera at index {self.camera_index}")
        
        # Try different backends if available
        backends = [
            cv2.CAP_DSHOW,  # DirectShow (Windows)
            cv2.CAP_ANY     # Auto-detect
        ]
        
        for backend in backends:
            try:
                self.cap = cv2.VideoCapture(self.camera_index, backend)
                if self.cap.isOpened():
                    print(f"Video: Successfully opened camera with backend {backend}")
                    break
            except Exception as e:
                print(f"Video: Error with backend {backend}: {e}")
        
        # If still not opened, try without specifying backend
        if not self.cap or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.camera_index)
        
        # Check if camera opened successfully
        if not self.cap.isOpened():
            print(f"Video: Error: Could not open camera {self.camera_index}")
            
            # Try alternative camera indices
            for i in range(1, 4):  # Try indices 1, 2, 3
                print(f"Video: Trying alternative camera index {i}")
                self.cap = cv2.VideoCapture(i)
                if self.cap.isOpened():
                    print(f"Video: Successfully opened camera at index {i}")
                    self.camera_index = i
                    break
            
            if not self.cap.isOpened():
                print("Video: Could not open any camera")
                return False
        
        # Try to set resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        
        # Check actual resolution accepted by camera
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"Video: Requested resolution: {self.width}x{self.height}")
        print(f"Video: Camera's actual resolution: {actual_width}x{actual_height}")
        
        # If camera doesn't support requested resolution, use available
        if actual_width != self.width or actual_height != self.height:
            print("Video: Using camera's native resolution")
            self.width = actual_width
            self.height = actual_height
        
        # Get FPS
        fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        if fps == 0:
            fps = 30  # Default value
        
        return fps, self.width, self.height
    
    def create_video_writer(self, fps, width, height):
        """Create object to write video in MP4 format"""
        # Generate filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"video_16x9_{timestamp}.mp4"
        
        # Define codec for MP4
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        
        self.video_writer = cv2.VideoWriter(filename, fourcc, fps, (width, height))
        return filename
    
    def add_timestamp(self, frame):
        """Add timestamp to bottom right corner"""
        # Get current date and time
        now = datetime.datetime.now()
        timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # Configure text
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        color = (255, 255, 255)  # White
        thickness = 2
        
        # Get text size
        text_size = cv2.getTextSize(timestamp_str, font, font_scale, thickness)[0]
        
        # Position (bottom right corner with margin)
        margin = 10
        text_x = frame.shape[1] - text_size[0] - margin
        text_y = frame.shape[0] - margin
        
        # Add semi-transparent background for better readability
        bg_color = (0, 0, 0)  # Black
        bg_margin = 5
        cv2.rectangle(frame, 
                     (text_x - bg_margin, text_y - text_size[1] - bg_margin),
                     (text_x + text_size[0] + bg_margin, text_y + bg_margin),
                     bg_color, -1)
        
        # Add text
        cv2.putText(frame, timestamp_str, (text_x, text_y), 
                   font, font_scale, color, thickness, cv2.LINE_AA)
        
        return frame
    
    def start_recording(self, stop_event):
        """Start recording"""
        print("Video: Starting 16:9 format recording...")
        
        result = self.setup_camera()
        if not result:
            print("Video: Camera setup failed. Cannot start recording.")
            return
        
        fps, width, height = result
        filename = self.create_video_writer(fps, width, height)
        
        self.is_recording = True
        print(f"Video: Recording to: {filename}")
        print(f"Video: Resolution: {width}x{height} ({(width/height):.2f}:1 ratio)")
        print("Video: Press 'q' to stop recording")
        
        try:
            while self.is_recording and not stop_event.is_set():
                ret, frame = self.cap.read()
                
                if not ret:
                    print("Video: Error: Could not read frame")
                    # Try to reinitialize camera
                    self.cap.release()
                    time.sleep(1)
                    result = self.setup_camera()
                    if not result:
                        break
                    continue
                
                # Add timestamp to frame
                frame_with_timestamp = self.add_timestamp(frame.copy())
                
                # Write frame to video
                self.video_writer.write(frame_with_timestamp)
                
                # Show video in real time
                cv2.imshow('Recording - Press "q" to stop', frame_with_timestamp)
                
                # Exit if 'q' is pressed
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        except Exception as e:
            print(f"Video: Error during recording: {e}")
        
        finally:
            self.stop_recording()
    
    def stop_recording(self):
        """Stop recording and release resources"""
        self.is_recording = False
        
        if self.video_writer is not None:
            self.video_writer.release()
            print("Video: Video saved successfully")
        
        if self.cap is not None:
            self.cap.release()
        
        cv2.destroyAllWindows()

def record_video(stop_event, camera_index=0):
    """
    Function to record video
    
    Args:
        stop_event: Event to signal when to stop
        camera_index (int): Camera index (default 0)
    """
    recorder = VideoRecorder(camera_index)
    try:
        recorder.start_recording(stop_event)
    except Exception as e:
        print(f"Video: Error: {e}")
    finally:
        recorder.stop_recording()

# Simple test function to check camera access
def test_camera_access(camera_index=0):
    """Test if we can access the camera"""
    print(f"Testing camera access for index {camera_index}")
    
    # Try different backends
    backends = [cv2.CAP_DSHOW, cv2.CAP_ANY]
    
    for backend in backends:
        try:
            cap = cv2.VideoCapture(camera_index, backend)
            if cap.isOpened():
                print(f"Camera opened successfully with backend {backend}")
                ret, frame = cap.read()
                if ret:
                    print("Successfully captured a frame")
                    cv2.imshow('Test Frame', frame)
                    cv2.waitKey(1000)  # Show for 1 second
                    cv2.destroyAllWindows()
                else:
                    print("Could not read frame from camera")
                cap.release()
                return True
        except Exception as e:
            print(f"Error with backend {backend}: {e}")
    
    print("Could not access camera with any backend")
    return False

if __name__ == "__main__":
    # Test camera access if run directly
    test_camera_access()