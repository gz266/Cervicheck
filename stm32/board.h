/*
 * board.h
 *
 *  Created on: Jul 12, 2026
 *      Author: minty
 */

#ifndef BOARD_H_
#define BOARD_H_
#include "ADS1015_ADS1115.h"
#include "MCP4725.h"

// AD5933 Constants
#define START_FREQ      10000
#define FREQ_INCR       10000
#define NUM_INCR        2
#define REF_RESIST      300

// Pressure Constants
extern float pres_start;
extern float pres_incr;
extern int pres_num_incr;
extern double imp_thresh;
extern double gain[NUM_INCR + 1];
extern double phase[NUM_INCR + 1];
extern int MUXtable[8][3];
extern int curPad;
extern float stressStrain[7];
extern float pressure;

// Pressure Constants
extern float slope;
extern float yint;

// Device
extern ADS1xx5_I2C ads;
extern MCP4725 dac;

// Functions
void releaseValve(int a);
void precondition(int cycles);
void runTest(int padnum);
void pressureSweep(void);
void resistanceRead(void);
void selectPad(int p);
void selectPressure(float p);
void calibratePressure(void);
float getPressure(void);
void loop(void);


#endif /* BOARD_H_ */
