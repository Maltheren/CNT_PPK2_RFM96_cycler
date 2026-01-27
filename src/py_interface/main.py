from interface import LoRaSerial
import time
from itertools import product
import ppk2_api


spreading_factor = [6, 7, 8, 9, 10, 11, 12]        
bandwidth = [125, 250, 500]
tx_power = [2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,20]
code_rate = [5]





if __name__ == "__main__":
    rfm  = LoRaSerial("/dev/ttyUSB0")
    rfm.reset()
    time.sleep(2)
    for sf, bw, tx_pwr, cr in product(spreading_factor, bandwidth, tx_power, code_rate):
        print(f"sf: {sf},\t bw: {bw},\t power: {tx_pwr},\t cr: {cr}")
        tx_time = rfm.configure_and_transmit(sf, bw, tx_pwr, cr)
        print(tx_time)
        time.sleep(tx_time/1000 + 0.2)
