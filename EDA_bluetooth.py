import asyncio
import sys
from bleak import BleakClient
from datetime import datetime
from pathlib import Path
import pandas as pd
import keyboard  # pip install keyboard

# BLE config
ESP32_MAC = "08:A6:F7:6B:37:C2"
CHARACTERISTIC_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"

# ADC/GSR settings
ADC_RESOLUTION = 4095
VCC = 3.3
R_FIXED = 10000

# Thresholds for impulse detection
THRESHOLD_MIN = 0.1
THRESHOLD_MAX = 0.5

# Global control
csv_path = None
guardando = False
ventana_gsr = []

# Windows event loop policy
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

def adc_to_microsiemens(adc_value, vcc=VCC, adc_resolution=ADC_RESOLUTION, r_fixed=R_FIXED):
    v_out = adc_value / adc_resolution * vcc
    try:
        r_skin = r_fixed * (v_out / (vcc - v_out))
        microsiemens = (1 / r_skin) * 1e6
    except ZeroDivisionError:
        microsiemens = 0
    return microsiemens

def crear_archivo_csv():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"GSR_data_{timestamp}.csv"
    ruta = Path.cwd() / nombre_archivo
    df = pd.DataFrame(columns=["timestamp", "datetime", "ADC", "microsiemens", "impulse"])
    df.to_csv(ruta, index=False)
    print(f"📝 Guardado iniciado: {ruta}")
    return ruta

def guardar_lectura(ruta, ts_unix, ts_human, adc, microsiemens, impulse):
    df = pd.DataFrame([[ts_unix, ts_human, adc, microsiemens, impulse]],
                      columns=["timestamp", "datetime", "ADC", "microsiemens", "impulse"])
    df.to_csv(ruta, mode='a', header=False, index=False)

async def run():
    global guardando, csv_path, ventana_gsr

    async with BleakClient(ESP32_MAC) as client:
        print(f"✅ Conectado al ESP32_GSR ({ESP32_MAC})")
        print("Presiona 's' para comenzar a guardar y 'q' para detener.")

        while True:
            try:
                # Leer GSR
                data = await client.read_gatt_char(CHARACTERISTIC_UUID)
                adc = int(data.decode())
                gsr_uS = adc_to_microsiemens(adc)

                # Timestamp
                ts_unix = datetime.now().timestamp()
                ts_human = datetime.now().isoformat(sep=' ', timespec='milliseconds')

                # Media móvil y detección de impulso
                ventana_gsr.append(gsr_uS)
                if len(ventana_gsr) > 10:
                    ventana_gsr.pop(0)
                media_movil = sum(ventana_gsr) / len(ventana_gsr)
                delta = gsr_uS - media_movil
                impulse = THRESHOLD_MIN < delta < THRESHOLD_MAX

                # Mostrar
                print(f"[{ts_unix:.3f}] {ts_human} → ADC: {adc} → {gsr_uS:.2f} µS | Δ={delta:.2f} → Impulse: {impulse}")

                # Comenzar/detener guardado
                if keyboard.is_pressed('s') and not guardando:
                    csv_path = crear_archivo_csv()
                    guardando = True

                elif keyboard.is_pressed('q') and guardando:
                    print("🛑 Guardado detenido.")
                    guardando = False

                if guardando:
                    guardar_lectura(csv_path, ts_unix, ts_human, adc, gsr_uS, impulse)

            except Exception as e:
                print(f"⚠️ Error: {e}")

            await asyncio.sleep(0.25)

if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\n🔚 Finalizando programa.")
