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
    above = signal > (threshold + (0.5*threshold))

    # find rising edge: False -> True
    start_candidates = np.where(np.diff(above.astype(int)) == 1)[0]
    if len(start_candidates) == 0:
        return None  # never goes above threshold

    start_idx = start_candidates[0] + 1


    above = signal > (threshold)
    # find falling edge: True -> False AFTER startthreshold
    end_candidates = np.where(
        np.diff(above[start_idx:].astype(int)) == -1
    )[0]

    if len(end_candidates) == 0:
        end_idx = len(signal)
    else:
        end_idx = start_idx + end_candidates[0] + 1

    return signal[start_idx:end_idx], [start_idx, end_idx]



def cycle_settings(ppk2: PPK2_API, rfm: LoRaSerial, vcc: float, filename):

    ppk2.use_source_meter() 
    ppk2.set_source_voltage(int(vcc))
    ppk2.toggle_DUT_power("ON")
    time.sleep(0.5)
    #Reset testbench
    rfm.reset()
    time.sleep(0.5)
    
    samples = []


    print("sampling threshold current current")
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


    results = {
        "vcc": [],      #supply voltage [mV]
        "sf": [],       #spreading factor
        "bw": [],       #bandwidh [kHz]
        "pwr": [],      #tx power in [dBm]
        "cr": [],       #code rate x/7
        "t_est": [],    #estimated time on air [ms]
        "t_meas": [],   #measured time in high draw state [ms]
        "i_q": [],      #current draw outside tx [mA]
        "i_tx": []      #current draw in [mA]
    }

    for sf, bw, tx_pwr, cr in product(spreading_factor, bandwidth, tx_power, code_rate):
        
  
        t_est = rfm.configure_and_transmit(sf, bw, tx_pwr, cr)
        
        ppk2.start_measuring()
        t_start = time.time()
        samples = []
        
        #data sampling af strømtræk
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

        ##alle de samples vi ikke var i tx
        I_q_samples = (samples[:limits[0]], samples[limits[1]:])
        
        ##Finder vores averages
        I_q_result = np.average(np.concatenate(I_q_samples))
        I_tx_result = np.average(tx_sample)
        
    

        results["sf"].append(sf)    
        results["bw"].append(bw)    
        results["pwr"].append(tx_pwr)    
        results["cr"].append(cr)  
        results["i_q"].append(I_q_result/1000) #converts uA to mA
        results["i_tx"].append(I_tx_result/1000) #converts uA to mA
        results["t_meas"].append(t_meas) #in milliseconds
        results["t_est"].append(t_est / 1000) #converts us to ms
        results["vcc"].append(vcc) #Vcc in mV


        if True:
            plt.clf()
            plt.grid(True)
            plt.plot(np.arange(len(I_q_samples[0]))/100,np.array(I_q_samples[0])/1000, color="Blue")
            plt.plot((np.arange(len(I_q_samples[1]))+limits[1])/100 ,np.array(I_q_samples[1])/1000, color="Blue")
            plt.plot(np.linspace(limits[0]/100, limits[1]/100, len(tx_sample)),np.array(tx_sample)/1000, color="Red")
            plt.xlabel("t [ms]")
            plt.ylabel("I [mA]")
            plt.ion()
            plt.pause(0.1)        
        else:
            time.sleep(0.1)
        print("Results t_est: {:.2f} ms, \t, t_meas: {:.2f} ms, \t i_avg: {:.2f}".format(t_est, t_meas, i_avg))
    final_data = pd.DataFrame(results)
    final_data.to_csv(filename)
   


if __name__ == "__main__":
    ppk2s_connected = PPK2_API.list_devices()
    print("Select devices")
    print(ppk2s_connected)

    ppk2 = PPK2_API("/dev/ttyACM1")
    #Set appropriate voltages
    ppk2.get_modifiers()
    rfm  = LoRaSerial("/dev/ttyUSB0")
    time.sleep(1)
    for vcc in np.linspace(3300, 1800, 4):
        cycle_settings(ppk2, rfm, vcc, f"test_{vcc}_-tempdeg.csv")
        time.sleep(0.5) #Delay to not spam rfm and ppk2f"test_{vcc}.csv"