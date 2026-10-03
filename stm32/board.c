#include "board.h"
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>

// printf changes (?)
int __io_putchar(int ch) {
    HAL_UART_Transmit(&huart2, (uint8_t*)&ch, 1, 100);
    return ch;
}

// Pressure Constants
float pres_start = -1;
float pres_incr = -1;
int pres_num_incr = 20;
double imp_thresh = 500;
double gain[NUM_INCR + 1];
double phase[NUM_INCR + 1];

// MUX table
int MUXtable[8][3] = {
    { 1, 1, 1 }, { 1, 1, 0 }, { 1, 0, 1 }, { 1, 0, 0 },
    { 0, 1, 1 }, { 0, 1, 0 }, { 0, 0, 1 }, { 0, 0, 0 }
};

int curPad = 0;
float stressStrain[NUM_PADS] = {0,0,0,0,0,0,0,0};
float padRes[NUM_PADS] = {5,5,5,5,5,5,5,5};
float pressure;

// Pressure Control Constants
// y = mx where y is digital value to supply DAC and x is desired pressure (-kPa)
float slope = -79.24;
float yint = 44.45;
float res_volt_thresh = 4.5;

// Device
ADS1xx5_I2C ads;
MCP4725 dac;

float getPressure(void) {
    float ch0 = ADSreadADC_SingleEnded(&ads, 0) * 3.0 / 1000;
    float ch2 = ADSreadADC_SingleEnded(&ads, 2) * 3.0 / 1000;
    return (ch0 - (0.92 * ch2)) / (0.018 * ch2);
}

void selectPressure(float p) {
    if (p > 0) {
        p = p * -1;
    }
    MCP4725_setValue(&dac, (uint16_t)(slope*p + yint), MCP4725_FAST_MODE, MCP4725_POWER_DOWN_OFF);
}

void selectPad(int p) {
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_9,  MUXtable[p][0]);
    HAL_GPIO_WritePin(GPIOC, GPIO_PIN_7,  MUXtable[p][1]);
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_6,  MUXtable[p][2]);
}

void releaseValve(int a) {
    if (a == 1) {
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_8, GPIO_PIN_SET);
    } else {
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_8, GPIO_PIN_RESET);
    }
}

void calibCheck(void) {
    for (int k = 0; k < NUM_PADS; k++) {
        selectPad(k);
        HAL_Delay(50);
        int val = ADSreadADC_SingleEnded(&ads, 3);
        float voltage = 3.0 * val / 1000;
        printf("CALIBCHECK,Pad %d Voltage: %.2f\r\n", k, voltage);
    }
    printf("DONE\r\n");
}

void readAllPads(float res_arr[]) {
    for (int k = 0; k < NUM_PADS; k++) {
        selectPad(k);
        HAL_Delay(50);
        res_arr[k] = ADSreadADC_SingleEnded(&ads, 3) * 3.0 / 1000;
    }
}

void calibratePressure(void) {
    printf("Voltage:\r\n");
    printf("50\r\n");
    printf("250\r\n");
    printf("500\r\n");
    printf("750\r\n");
    printf("1000\r\n");
    printf("1250\r\n");
    printf("Pressure:\r\n");

    for (int i = 50; i < 251; i += 200) {
    	MCP4725_setValue(&dac, (uint16_t)i, MCP4725_FAST_MODE, MCP4725_POWER_DOWN_OFF);
        HAL_Delay(3000);
        printf("%.2f\r\n", getPressure());
    }

    for (int i = 500; i < 1251; i += 250) {
    	MCP4725_setValue(&dac, (uint16_t)i, MCP4725_FAST_MODE, MCP4725_POWER_DOWN_OFF);
        HAL_Delay(3000);
        printf("%.2f\r\n", getPressure());
    }

    printf("Done!\r\n");
}

void precondition(int cycles) {
    for (int i = 0; i < cycles; i++) {
        // On
        releaseValve(0);
        selectPressure(0.5);
        HAL_Delay(200);
        printf("Pressure Held: %.2f\r\n", getPressure());
        // Off
        releaseValve(1);
        selectPressure(0);
        HAL_Delay(500);
        printf("Pressure Released: %.2f\r\n", getPressure());
    }
    releaseValve(0);
}

void runTest(int padnum) {
    printf("Pad %d being tested\r\n", padnum);
    printf("Pressure Tested (kPa): %.2f\r\n", getPressure());

    selectPad(padnum);
    int time1 = HAL_GetTick();
    resistanceRead();
    int time2 = HAL_GetTick();

    printf("Test time (ms): %d\r\n", time2 - time1);
}

void pressureSweep(void) {
    curPad = 0;
    pressure = pres_start;
    precondition(10);
    for (int i = 0; i < pres_num_incr; i++, pressure += pres_incr) {
        if (curPad == NUM_PADS) {
            break;
        }
        if ((i < pres_num_incr + 1) == 0) {
            printf("Break\r\n");
            break;
        }
        printf("Sweeping at Pressure (kPa): %.2f\r\n", pressure);

        selectPressure(pressure);
        float currentPressure = getPressure();

        printf("Current Pressure (kPa): %.2f\r\n", currentPressure);

        streamPressureSample(pressure, currentPressure, curPad);
        int count = 0;
        float error = 0.1;
        while (fabs(currentPressure - pressure) > error) {
            count++;
            currentPressure = getPressure();
            if (count % 5 == 0) {
                streamPressureSample(pressure, currentPressure, curPad);
            }
            if (count > 100) {
                break;
            }
        }
        streamPressureSample(pressure, currentPressure, curPad);
        runTest(curPad);
    }
}

void resistanceRead(void) {
    readAllPads(padRes);
    float voltage = 5.0;
    for (int v = curPad; v < NUM_PADS; v++) {
        if (padRes[v] < res_volt_thresh) {
            voltage = padRes[v];
            curPad = v;
        } else {
            break;
        }
    }

    if ((voltage < res_volt_thresh) && (curPad < NUM_PADS)) {
        float contactPressure = getPressure();
        stressStrain[curPad] = contactPressure;
        streamPressureSample(pressure, contactPressure, curPad);
        streamContactMarker(curPad, contactPressure, voltage);
        printf("Pad %d has been contacted at %.2f (volts)!\r\n", curPad, padRes[curPad]);
        curPad++;
    } else {
        printf("Pad %d has not been contacted at %.2f (volts)\r\n", curPad, voltage);
    }
}

void streamPressureSample(float targetPressure, float actualPressure, int padnum) {
    printf("PRESSURE,%lu,%.2f,%.2f,%d\r\n", (unsigned long)HAL_GetTick(), targetPressure, actualPressure, padnum);
}

void streamContactMarker(int padnum, float contactPressure, double impedance) {
    printf("CONTACT,%lu,%d,%.2f,%.2f\r\n", (unsigned long)HAL_GetTick(), padnum, contactPressure, impedance);
}
