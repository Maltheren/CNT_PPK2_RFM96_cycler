import serial
import struct
import time

#Heheh konstrueret af katten selv
class LoRaSerial:
    CMD_RESET = 0x00
    CMD_CONFIG_AND_TX = 0x01

    DEBUG_PREFIX = 0x66
    OK_RESPONSE = b"\x00\n"

    def __init__(self, port, baudrate=115200, timeout=10):
        self.ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=timeout
        )
        # Give ESP time to boot after opening serial
        time.sleep(2)

    def close(self):
        self.ser.close()

    def _read_response(self):
        """
        Reads lines until we get a non-debug response.
        """
        while True:
            line = self.ser.readline()
            if not line:
                raise TimeoutError("No response from device")

            # Debug messages are prefixed with 0x66
            if line[0] == self.DEBUG_PREFIX:
                print(f"[DEBUG] {line[1:].decode(errors='ignore').strip()}")
                continue

            return line

    def reset(self):
        """
        Send reset command (0x00)
        """
        packet = bytes([self.CMD_RESET]) + b"\n"
        self.ser.write(packet)

        resp = self._read_response()
        if resp != self.OK_RESPONSE:
            raise RuntimeError(f"Unexpected response: {resp!r}")

    def configure_and_transmit(self, sf, bw, tx_power, cr):
        """
        Send config + transmit command (0x01)
        All params are float32.
        Returns transmission  time in milliseconds
        """
        packet = bytearray()
        packet.append(self.CMD_CONFIG_AND_TX)

        # Little-endian float packing
        packet += struct.pack("<f", sf)
        packet += struct.pack("<f", bw)
        packet += struct.pack("<f", tx_power)
        packet += struct.pack("<f", cr)

        packet += b"\n"

        self.ser.write(packet)

        resp = self._read_response()
        if resp[0] != 0x00:
            raise RuntimeError(f"Unexpected response: {resp!r}")
        else:
            return int(resp[1:]) / 1000 #Returns transmission  time in milliseconds
        