import cv2

# Try different camera indices
for i in range(0, 4):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"Camera found at index {i}")
        ret, frame = cap.read()
        if ret:
            print("Frame captured successfully")
            cv2.imshow('Frame', frame)
            cv2.waitKey(1000)
        cap.release()
    else:
        print(f"No camera at index {i}")

cv2.destroyAllWindows()