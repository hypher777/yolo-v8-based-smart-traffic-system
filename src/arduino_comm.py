import serial
import time

class ArduinoComm:
    def __init__(self, port='COM3', baudrate=9600, simulation_mode=False):
        self.simulation = simulation_mode
        self.ser = None
        
        if not self.simulation:
            try:
                self.ser = serial.Serial(port, baudrate, timeout=1)
                time.sleep(2) # Wait for Arduino to reset
                print(f"Connected to Arduino on {port}")
            except serial.SerialException as e:
                print(f"Error connecting to Arduino: {e}")
                print("Switching to simulation mode for output temporarily.")
                self.simulation = True

    def send_command(self, road_idx, color):
        """
        Send a single-byte command to Arduino.
        Format: 0x<RoadNum><ColorCode>
        Color Codes: Green=1, Yellow=2, Red=3
        """
        road_num = road_idx + 1 # 1-indexed for hardware
        color_map = {"GREEN": 0x1, "YELLOW": 0x2, "RED": 0x3}
        
        if color not in color_map:
            return
            
        byte_cmd = (road_num << 4) | color_map[color]

        if self.simulation:
            print(f"[SIM-HARDWARE] Sending Byte: {hex(byte_cmd)} ({color} on Road {road_num})")
            return

        if self.ser and self.ser.is_open:
            try:
                self.ser.write(bytes([byte_cmd]))
            except Exception as e:
                print(f"Serial Write Error: {e}")

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
