from interface import LoRaSerial
import time
from itertools import product
from ppk2_api.ppk2_api import PPK2_API
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

spreading_factor = [6, 7, 8, 9, 10, 11, 12]        
bandwidth = [125, 250, 500]
tx_power = [2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,20]
code_rate = [5]



def extract_tx(signal, threshold):
    signal = np.asarray(signal)

    # indices where signal is above threshold
    above = signal > threshold

    # find rising edge: False -> True
    start_candidates = np.where(np.diff(above.astype(int)) == 1)[0]
    if len(start_candidates) == 0:
        return None  # never goes above threshold

    start_idx = start_candidates[0] + 1

    # find falling edge: True -> False AFTER start
    end_candidates = np.where(
        np.diff(above[start_idx:].astype(int)) == -1
    )[0]

    if len(end_candidates) == 0:
        end_idx = len(signal)
    else:
        end_idx = start_idx + end_candidates[0] + 1

    return signal[start_idx:end_idx], [start_idx, end_idx]



def cycle_settings(ppk2: PPK2_API, rfm: LoRaSerial, vcc):
    #Set appropriate voltages
    ppk2.get_modifiers()
    ppk2.use_source_meter() 
    ppk2.set_source_voltage(vcc)
    ppk2.toggle_DUT_power("ON")
    time.sleep(0.2)
    #Reset testbench
    rfm.reset()
    time.sleep(0.2)
    
    samples = []


    print("sampling quietsent current")
    ppk2.start_measuring()
    # measurements are a constant stream of bytes
    # the number of measurements in one sampling period depends on the wait between serial reads
    # it appears the maximum number of bytes received is 1024
    # the sampling rate of the PPK2 is 100 samples per millisecond
    
    for i in range(0, 200):
        data = ppk2.get_data()
        if data != b'':
            block, _ = ppk2.get_samples(data)
            samples += block
        time.sleep(0.005)
    ppk2.stop_measuring()

    i_q = np.average(samples) / 1000; #In mA
    i_q_std = np.std(samples) / 1000; #standard deviation in mA 
    i_thres = (i_q*2+ i_q_std*10)*1000; #in uA
    print("average current mean {:.2f} mA, std: {:.2f} mA".format(i_q, i_q_std))
    print("setting thres at: {:.2f}".format(i_thres))
    time.sleep(2)
    for sf, bw, tx_pwr, cr in product(spreading_factor, bandwidth, tx_power, code_rate):
        #print(f"sf: {sf},\t bw: {bw},\t power: {tx_pwr},\t cr: {cr}")
        t_est = rfm.configure_and_transmit(sf, bw, tx_pwr, cr)
        
        ppk2.start_measuring()
        t_start = time.time()
        samples = []
        #data sampling

        while((time.time()- t_start) < (t_est/1000 + 0.2)):
            data = ppk2.get_data()
            if data != b'':
                block, _ = ppk2.get_samples(data)
                samples += block
        ppk2.stop_measuring()

        ##NOw we have the raw samples in uA
        tx_sample, limits = extract_tx(samples, i_thres)
        t_meas = len(tx_sample)/100 #time in ms
        i_avg = np.average(tx_sample) /1000
        
        plt.clf()
        plt.grid(True)
        plt.plot(np.arange(len(samples))/100,np.array(samples)/1000)
        plt.xlabel("t [ms]")
        plt.ylabel("I [mA]")
        plt.plot([limits[0]/100, limits[0]/100], [0, max(tx_sample)/1000], linestyle=':', linewidth=3, color='black')
        plt.plot([limits[1]/100, limits[1]/100], [0, max(tx_sample)/1000], linestyle=':', linewidth=3, color='black')


        plt.ion()
        plt.pause(0.1)        



        print("Results t_est: {:.2f} ms, \t, t_meas: {:.2f} ms, \t i_avg: {:.2f}".format(t_est, t_meas, i_avg))



if __name__ == "__main__":
    ppk2s_connected = PPK2_API.list_devices()
    print("Select devices")
    print(ppk2s_connected)

    ppk2 = PPK2_API("/dev/ttyACM1")
    rfm  = LoRaSerial("/dev/ttyUSB0")
    time.sleep(1)
    cycle_settings(ppk2, rfm, 2500)
