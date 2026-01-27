#include <Arduino.h>
#include <SPI.h>
#include <RadioLib.h>
#include <pins.h>



char message[] = {0,0,0,0,0,0,0,0,0,0};
uint8_t nBytes = sizeof(message);
RFM96 radio = new Module(PIN_RFM_CS, RADIOLIB_NC, RADIOLIB_NC, RADIOLIB_NC);


//https://github.com/chandrawi/LoRaRF-Arduino/blob/main/examples/SX126x/SX126x_LoRa_transmitter/SX126x_LoRa_transmitter.ino 





void reset_pins(){
  Serial.println("Done");
}


class LoRa_settings{
  public:

  uint16_t tx_power = 0;
  bool PA_enabled;
  uint16_t sf = 0;
  float bw = 0;
  uint8_t cr = 0;


  LoRa_settings(uint16_t sf, uint32_t bw, uint8_t cr, uint16_t tx_power, bool PA_enabled){
    this->sf = sf;
    this->bw = bw;
    this->cr = cr;
    this->tx_power = tx_power;
    this->PA_enabled = PA_enabled;
  }
  //estimates the bitrate
  double bitrate(){
    return double(sf) * (4.0/double(cr))/(pow(2, double(sf))/(double(bw)/1000.0)) *1000.0;
  }
  //estimates the transmission time in seconds
  double transmission_time(uint16_t preamble_and_payload){
    double R_b = bitrate();
    double t_transmit = (double((preamble_and_payload)*8)+105)/R_b;
    return t_transmit;
  }
  void dump_settings(){
    Serial.print("sf: "); Serial.print(sf);
    Serial.print("\t bw: "); Serial.print(bw);
    Serial.print("\t cr: "); Serial.print(cr);
    Serial.print("\t pwr: "); Serial.print(tx_power);
    Serial.print("\t pa: "); Serial.print(PA_enabled);
  }
};

void perform_cycle(LoRa_settings input, uint16_t package_length);
LoRa_settings Settingcycler(uint32_t n, uint32_t *next_n);



void setup() {

  SPI.begin(PIN_RFM_SCK, PIN_RFM_MISO, PIN_RFM_MOSI);
  Serial.begin(115200);
  Serial.setTimeout(20);
  

  while(!Serial){
    delay(100);
  }


  Serial.printf("Initializing radio: %d\n", radio.begin());
  Serial.print("Setting spi-speed\n");

  SPI.setFrequency(250000);
  Serial.printf("Setting current limit: %d\n", radio.setCurrentLimit(230));
  
  Serial.printf("Setting battery low limit: %d\n", radio.setLowBatteryThreshold(-1, RADIOLIB_NC));
  Serial.println("OK");
  }



void loop() { //Rent faktisk test ting



  delay(1000);

  
  //Serial.println("Set packet parameters:\n\tExplicit header type\n\tPreamble length = 12\n\tPayload Length = 15\n\tCRC on");
  uint16_t preambleLength = 12;                                       // Set preamble length to 12
  uint8_t payloadLength = sizeof(message);                                         // Initialize payloadLength to 15
  bool crcType = false;                                                // Set CRC enable


  u_int16_t tx_power = 0;
  uint32_t next_n = 0;
  while(true){
    if(Serial.available()){
      String message = Serial.readString();
      //Serial.print("message: "); Serial.println(message);
      int n = message.toInt();
      LoRa_settings settings = Settingcycler(n, &next_n);

      Serial.print("ID: "); Serial.print(n); Serial.print("\t");
      perform_cycle(settings, payloadLength);
    }
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

  delay(100); //Venter 500ms og så rykker vi radioen
  radio.transmit(message, package_length);
}











LoRa_settings Settingcycler(uint32_t n, uint32_t *next_n) {

  uint16_t tx_power[] = {2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17}; // Transmit power levels
  uint16_t sf[] = {6, 7, 8};  // Spreading factor
  float bw[] = {125.0, 250.0, 500.0};  // Bandwidth
  uint16_t cr[] = {7};  // Coding rate

  // Sizes
  constexpr uint16_t tx_size = sizeof(tx_power) / sizeof(tx_power[0]);
  constexpr uint16_t sf_size = sizeof(sf) / sizeof(sf[0]);
  constexpr uint16_t bw_size = sizeof(bw) / sizeof(bw[0]);
  constexpr uint16_t cr_size = sizeof(cr) / sizeof(cr[0]);

  constexpr uint32_t total_combinations = tx_size * sf_size * bw_size * cr_size;

  // Wrap around if n exceeds total combinations
  n %= total_combinations;

  (*next_n) = n + 1; // Next index

  // Compute indices using modular arithmetic
  uint16_t tx_index = n % tx_size;
  n /= tx_size;
  uint16_t sf_index = n % sf_size;
  n /= sf_size;
  uint16_t bw_index = n % bw_size;
  n /= bw_size;
  uint16_t cr_index = n % cr_size;

  //EN ordenlig debug linje
  //Serial.print(tx_index); Serial.print("\t"); Serial.print(sf_index); Serial.print("\t");Serial.print(bw_index); Serial.print("\t");Serial.print(cr_index); Serial.print("\t");

  return LoRa_settings(sf[sf_index], bw[bw_index], cr[cr_index], tx_power[tx_index], true);
}