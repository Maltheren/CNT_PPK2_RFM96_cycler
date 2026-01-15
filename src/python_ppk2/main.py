import time
from ppk2_api.ppk2_api import PPK2_API
import serial
import matplotlib.pyplot as plt
import pandas as pd
ppk2s_connected = PPK2_API.list_devices()


print("Select devices")
print(ppk2s_connected)
ppk2 = PPK2_API("/dev/ttyACM1")



def Perfom_measurement(time, cal_const): ##RUns for the specified time and calculates the charge minus the quescent current 

    print("starting to sample")
    # measurements are a constant stream of bytes
    # the number of measurements in one sampling period depends on the wait between serial reads
    # it appears the maximum number of bytes received is 1024
    # the sampling rate of the PPK2 is 100 samples per millisecond
    total_samples = []
    ppk2.start_measuring()
    
    
    while (True):
        raw_data = ppk2.get_data()
        within = False
        i = 0 
        if raw_data != b'': #If we have actually recieved anything
            
            samples, raw_samples = ppk2.get_samples(raw_data)
            total_samples.extend(samples)
            
            i += 1
            if ((i % 100) == 0):
                print(samples[0])
                i = 0



            if len(total_samples) > int(100*time):
                break

    ppk2.stop_measuring()
    ppk2.get_data() ##Flusher hvis vi nu skulle have noget liggende
    print("DOne")
    f_s = 1/(10**(-5)) #100 samples pr millisecond
    
    within_transmission = False
    transmission = []
    for i in range(0, len(total_samples)):
        #Afgører hvornår vi skal hoppe ind i vores transmission buffer
        if(total_samples[i]/1000 > cal_const*3):
            within_transmission = True
        if(within_transmission):
            transmission.append(total_samples[i])
            
            if(total_samples[i]/1000 < cal_const*2):
                break ##vi har fundet enden af vores transmission så vi dumper resten
    

    
    t_transmission = len(transmission)/100 #Hvor lang transmission time var i ms
    print("Actual transmission time: {} ms".format(t_transmission))


    avg = sum(transmission)/len(transmission) #Current in uA
    
    charge_avg = (avg/1000) * (t_transmission/1000) #[mA] * [s] = [mC]

    charge_compensated = (charge_avg) #Vi har 2 hoperfmoduler så vi trækker naboens passive strømtræk fra.

    print("avg current: {} uA".format(avg))
    print("q = {:.2f} mC".format(charge_compensated))
    return avg/1000, charge_compensated, t_transmission

def unpack(input: str):
    elements = input.split(b'\t')
    output = []
    for element in elements:
        output.append(element.split(b':')[1])

    return output


esp32 = serial.Serial('/dev/ttyUSB0', 115200, timeout=100) ##TODO replace med argument

def read_esp():
    temp = esp32.readline()

    print("[ESP32]: {}".format(temp.decode('ascii')))
    return temp


def runtest():
    





if __name__ == "__main__":

    #==== test cycle ====
    # Measure the passive current
    # get n => to ESP
    # ESP => corresponding settings back & estimated transmssion time
    # Measure the current draw for said time
    # repeat
    
    setofN = range(0, 300) ##Indencies to test



    ppk2.get_modifiers()
    ppk2.use_source_meter()  # set source meter mode
    ppk2.set_source_voltage(3300)  #set  source voltage in mV
    ppk2.toggle_DUT_power("ON")


    line = read_esp()

    while(line.rstrip() != b'OK'):
        print("Weird error with the ESP, trying again")
        line = read_esp()


    #We measure silence
    print("Calibrating")
    I_compensation, _, _ = Perfom_measurement(4000, 0)
    
    print("Read quescent current: {:.2f} mA".format(I_compensation))


    columns = ["n", "sf", "bw", "cr", "pwr", "pa", "br [bits/s]", "t_est [s]", "t_meas [s]", "Q [mC]", "I_avg [mA]"]
    output = pd.DataFrame(columns=columns)


    for n in setofN:
        print("index: {}".format(n))
        message = "{}".format(n)
        esp32.write(bytes(message, encoding='ascii')) ##Type conversion magic

        response = read_esp()
        settings = unpack(response)
        
        duration = float(settings[7].rstrip())/1000 #Gets the time in milliseconds
        
        i_avg, q, t_meas = Perfom_measurement(duration+500, I_compensation)
        settings.extend([t_meas/1000, q, i_avg])
        data = {}

        data = {columns[i]: float(settings[i]) for i in range(len(settings))}
        row = pd.DataFrame([data])  # Wrap the dictionary in a list to ensure proper DataFrame structure

        output = pd.concat([output, row], ignore_index=True)
        time.sleep(0.5)



    output.to_csv("Test_Term_16ohm_100cm.csv")

    #Now we have the passive current draw so we can actually start looking at the transmission difference










