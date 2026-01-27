#include <Arduino.h>
#include <SPI.h>
#include <RadioLib.h>
#include <pins.h>
#include <LoRa_class.h>


char message[] = {0,0,0,0,0,0,0,0,0,0};
RFM96 radio = new Module(PIN_RFM_CS, RADIOLIB_NC, RADIOLIB_NC, RADIOLIB_NC);

int assert_rl(int response, String comment){
  Serial.write(0x66);
  Serial.print(comment);
  Serial.print(": \t");
  Serial.println(response);
  return response;
}

void dbg_msg(String msg){
  Serial.write(0x66);
  Serial.print(msg);
  Serial.write("\n");
}

void reset_testbed(){
  dbg_msg("Resetting module");
  assert_rl(radio.begin(), "Initializing radio");
  assert_rl(radio.setCurrentLimit(230), "Setting current limit");
  assert_rl(radio.setLowBatteryThreshold(-1, RADIOLIB_NC), "Disabling low battery indicator"); 
}



void setup() {
  dbg_msg("Starting");
  dbg_msg("Enabling SPI");

  SPI.begin(PIN_RFM_SCK, PIN_RFM_MISO, PIN_RFM_MOSI);
  Serial.begin(115200);
  Serial.setTimeout(20);
  SPI.setFrequency(250000);
  reset_testbed();
  dbg_msg("Ready");
  Serial.setTimeout(10);
}



//////////////////////////////77
// Protocol as is:
// 0x01: Reset and reinitialize lora module
// Returns 0x00\n for ok 

// 0x02, sf, bw, tx_power, cr, all in float4 format
// Returns 0x00\n for ok

// Spurious debug messages are prefixed with 0x66
// 

char rx_buffer[100] = {0};



void loop() { //Rent faktisk test ting

  int length = Serial.readBytesUntil('\n', rx_buffer, sizeof(rx_buffer));
  if (length == 0){
    delay(1);
    return;
  }
  float sf;
  float bw;
  float tx_pwr;
  float cr;
  uint32_t t_est;
  switch (rx_buffer[0])
  {
  case 0: //Reset esp
    reset_testbed();
    Serial.write(0);
    Serial.write('\n');

    /* code */
    break;
  case 1: //
    //Evil pointer hax
    memcpy(&sf,     &rx_buffer[1],  4);
    memcpy(&bw,     &rx_buffer[5],  4);
    memcpy(&tx_pwr, &rx_buffer[9],  4);
    memcpy(&cr,     &rx_buffer[13], 4);
    
    radio.setSpreadingFactor(sf);
    radio.setBandwidth(bw);
    radio.setOutputPower(tx_pwr);
    radio.setCodingRate(cr);
    Serial.write(0x66);
    Serial.printf("got: %d, %d, %d, %d", (int)sf, (int)bw, (int)tx_pwr, (int)cr);
    Serial.write('\n');


    t_est = radio.getTimeOnAir(sizeof(message));

    Serial.write(0);
    Serial.print(String(t_est));    
    Serial.write('\n');


    //TODO
    delay(100); 
    radio.transmit(message, sizeof(message));
    
    /* code */
    break;
  default:
    //beep boop
    break;
  }


}





void perform_cycle(LoRa_settings input, uint16_t package_length){
  uint8_t sf = input.sf;
  uint32_t bw = input.bw;
  uint8_t cr = input.cr;
  uint8_t tx_power = input.tx_power;
  
  radio.setFrequency(433.0);
  radio.setSpreadingFactor(sf);
  radio.setBandwidth(bw);
  radio.setCodingRate(cr);
  radio.setOutputPower(tx_power);

  
  double br = 0.0;
  uint32_t t_est = radio.getTimeOnAir(package_length);


  input.dump_settings();
  Serial.print("\t br: "); Serial.print(br);
  Serial.print("\t t: "); Serial.println(t_est);

  delay(100); //Venter 100ms og så rykker vi radioen
  radio.transmit(message, package_length);
}






