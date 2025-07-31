import cv2
from datetime import datetime

def get_timestamp():
    return datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

def main():
    cap = cv2.VideoCapture(0)
    recording = False
    out = None
    print("Presiona 'r' para comenzar a grabar, 's' para detener, 'q' para salir.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("No se pudo acceder a la cámara.")
            break

        # Obtener y dibujar el timestamp en el video
        timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cv2.putText(frame, timestamp_str, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 255, 0), 2)

        # Mostrar la imagen
        cv2.imshow("Grabación", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('r') and not recording:
            # Empezar a grabar
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            filename = f"grabacion_{get_timestamp()}.avi"
            out = cv2.VideoWriter(filename, fourcc, 20.0, (frame.shape[1], frame.shape[0]))
            recording = True
            print(f"Grabando... ({filename})")

        elif key == ord('s') and recording:
            # Detener la grabación
            recording = False
            out.release()
            print("Grabación detenida y guardada.")

        elif key == ord('q'):
            # Salir
            if recording:
                out.release()
                print("Grabación detenida y guardada antes de salir.")
            break

        if recording:
            out.write(frame)

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
