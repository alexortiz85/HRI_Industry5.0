import threading
import time
from datetime import datetime
from eeg_recorder import eegHeadset
from heart_rate_monitor import monitor_heart_rate
from video_recorder import record_video
from gsr_sensor import read_gsr

def main():
    # Get subject identifier
    subject_id = input("Enter subject ID: ")
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create stop events for all functions
    stop_event = threading.Event()
    
    # Create filenames with session ID for better organization
    eeg_filename = f"eeg_{subject_id}_{session_id}.csv"
    hr_filename = f"hr_{subject_id}_{session_id}.csv"
    gsr_filename = f"gsr_{subject_id}_{session_id}.csv"


    ESP32_MAC = "08:A6:F7:6B:48:36" 
    
    # Create threads for each recording modality
    threads = [
        threading.Thread(target=eegHeadset, args=(subject_id, stop_event), name="EEG"),
        threading.Thread(target=monitor_heart_rate, args=(stop_event, "24:AC:AC:02:FA:11", hr_filename), name="HeartRate"),
        threading.Thread(target=record_video, args=(stop_event, 0), name="Video"),
        threading.Thread(target=read_gsr, args=(stop_event, ESP32_MAC, gsr_filename), name="GSR")
    ]
    
    print("\n" + "="*60)
    print("Starting Multi-Modal Data Recording Session")
    print(f"Subject: {subject_id}")
    print(f"Session: {session_id}")
    print("="*60 + "\n")
    
    # Start all threads
    for thread in threads:
        thread.daemon = True
        thread.start()
        time.sleep(1)  # Small delay between starting threads
    
    print("\nAll recording modalities are now active!")
    print("Press Enter to stop all recordings")
    print("="*60 + "\n")
    
    try:
        # Wait for user input to stop
        input()
        
    except KeyboardInterrupt:
        print("\nStopping all recordings...")
    
    finally:
        # Set stop event to signal all threads to stop
        stop_event.set()
        
        # Wait for threads to finish
        for thread in threads:
            thread.join(timeout=5.0)
        
        print("\nAll recordings stopped")
        print(f"Data saved with subject ID: {subject_id}")
        print(f"Session ID: {session_id}")
        print("Files created:")
        print(f"  - EEG: {eeg_filename}")
        print(f"  - Heart Rate: {hr_filename}")
        print(f"  - GSR: {gsr_filename}")
        print(f"  - Video: video_16x9_{session_id}.mp4")

if __name__ == "__main__":
    main()