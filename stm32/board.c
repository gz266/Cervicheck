#include "board.h"
#include <stdio.h>
#include <string.h>
#include <math.h>
/*
 * board.c
 *
 *  Created on: Jul 12, 2026
 *      Author: minty
 */

// Pressure Constants
float pres_start = -1;
float pres_incr = -1;
int pres_num_incr = 20;
double imp_thresh = 500;
double gain[NUM_INCR + 1];
double phase[NUM_INCR + 1];

// MUX table
int MUXtable[8][3] = {
    { 1, 0, 1 }, { 1, 1, 0 }, { 0, 0, 0 }, { 1, 0, 0 },
    { 0, 1, 0 }, { 0, 0, 1 }, { 0, 1, 1 }, { 1, 1, 1 }
};

int curPad = 1;
float stressStrain[7] = {0,0,0,0,0,0,0};
float pressure;

// Pressure Constants
float slope = -79.24;
float yint = 44.45;

// Device
ADS1xx5_I2C ads;
MCP4725 dac;

void loop(void) {
    char data[20];
    char buffer[20];

    MCP4725_setVoltage(&dac, (0*4095)/5, MCP4725_FAST_MODE, MCP4725_POWER_DOWN_OFF);

    // Check if data is available on UART
    uint8_t userInput;
    if (HAL_UART_Receive(&huart2, &userInput, 1, 10) == HAL_OK) {

        if (userInput == 's') {
            long t1 = HAL_GetTick();
            pressureSweep();
            long t2 = HAL_GetTick();
            printf("Done!\r\n");
            for (int i = 1; i < 8; i++) {
                printf("%.2f\r\n", stressStrain[i-1]);
            }
            printf("Time: \r\n");
            printf("%ld\r\n", t2-t1);
            for (int i = 0; i < 7; i++) {
                stressStrain[i] = 0;
            }
            printf("Releasing Valve: \r\n");
            releaseValve(1);
            HAL_Delay(5000);
            releaseValve(0);
        }

        if (userInput == 'p') {
            calibratePressure();
        }

        if (userInput == 'r') {
            // Read slope
            HAL_UART_Receive(&huart2, (uint8_t*)data, sizeof(data), 1000);
            slope = atof(data);
            // Read yint
            memset(data, 0, sizeof(data));
            HAL_UART_Receive(&huart2, (uint8_t*)data, sizeof(data), 1000);
            yint = atof(data);
        }

        if (userInput == 'i') {
            // Read pres_start
            HAL_UART_Receive(&huart2, (uint8_t*)data, sizeof(data), 1000);
            pres_start = atof(data);
            // Read pres_incr
            memset(data, 0, sizeof(data));
            HAL_UART_Receive(&huart2, (uint8_t*)data, sizeof(data), 1000);
            pres_incr = atof(data);
            // Read pres_num_incr
            memset(data, 0, sizeof(data));
            HAL_UART_Receive(&huart2, (uint8_t*)data, sizeof(data), 1000);
            pres_num_incr = atoi(data);
            // Read imp_thresh
            memset(data, 0, sizeof(data));
            HAL_UART_Receive(&huart2, (uint8_t*)data, sizeof(data), 1000);
            imp_thresh = atof(data);
        }

        if (userInput == 't') {
            HAL_UART_Receive(&huart2, (uint8_t*)data, sizeof(data), 1000);
            releaseValve(atoi(data));
        }
    }
}
