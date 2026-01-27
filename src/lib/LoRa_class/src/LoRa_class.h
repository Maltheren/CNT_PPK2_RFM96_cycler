#include<Arduino.h>


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