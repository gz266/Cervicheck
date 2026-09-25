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
    { 1, 0, 1 }, { 1, 1, 0 }, { 0, 0, 0 }, { 1, 0, 0 },
    { 0, 1, 0 }, { 0, 0, 1 }, { 0, 1, 1 }, { 1, 1, 1 }
};

int curPad = 1;
float stressStrain[7] = {0,0,0,0,0,0,0};
float pressure;

// Pressure Control Constants
float slope = -79.24;
float yint = 44.45;

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

void calibratePressure(void) {
    printf("Voltage:\r\n");
    printf("50\r\n");
    printf("250\r\n");
    printf("500\r\n");
    printf("1500\r\n");
    printf("2500\r\n");
    printf("Pressure:\r\n");

    for (int i = 50; i < 251; i += 200) {
    	MCP4725_setValue(&dac, (uint16_t)i, MCP4725_FAST_MODE, MCP4725_POWER_DOWN_OFF);
        HAL_Delay(3000);
        printf("%.2f\r\n", getPressure());
    }

    for (int i = 500; i < 2501; i += 1000) {
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
        HAL_Delay(100);
        printf("Pressure Held: \r\n");
        printf("%.2f\r\n", getPressure());
        // Off
        releaseValve(1);
        selectPressure(0);
        HAL_Delay(250);
        printf("Pressure Released: \r\n");
        printf("%.2f\r\n", getPressure());
    }
    releaseValve(0);
}

void runTest(int padnum) {
    printf("Pad \r\n");
    printf("%d\r\n", padnum);
    printf(" being tested\r\n");
    printf("Pressure Tested (kPa): \r\n");
    printf("%.2f\r\n", getPressure());

    selectPad(padnum);
    int time1 = HAL_GetTick();
    frequencySweepStressStrain();
    int time2 = HAL_GetTick();

    printf("Test time (ms): \r\n");
    printf("%d\r\n", time2 - time1);
}

void pressureSweep(void) {
    curPad = 1;
    pressure = pres_start;
    int sweep;
    precondition(10);
    for (int i = 0; i < pres_num_incr; i++, pressure += pres_incr) {
        if (curPad == 8) {
            break;
        }
        if ((i < pres_num_incr + 1) == 0) {
            printf("Break\r\n");
            break;
        }
        printf("Sweeping at Pressure (kPa): \r\n");
        printf("%.2f\r\n", pressure);

        selectPressure(pressure);
        float currentPressure = getPressure();

        printf("Current Pressure (kPa): \r\n");
        printf("%.2f\r\n", currentPressure);

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
    int val = ADSreadADC_SingleEnded(&ads, 3);
    float voltage = 3.0 * val / 1000;
    if ((voltage < res_volt_thresh) && (curPad < 8)) {
        stressStrain[curPad-1] = getPressure();
        printf("Pad \r\n");
        printf("%d\r\n", curPad);
        printf(" has been contacted at \r\n");
        printf("%.2f\r\n", voltage);
        printf(" (volts)!\r\n");
        curPad++;
    } else {
        printf("Pad \r\n");
        printf("%d\r\n", curPad);
        printf(" has not been contacted at \r\n");
        printf("%.2f\r\n", voltage);
        printf(" (volts)\r\n");
    }
}

void loop(void) {
    uint8_t userInput;
    char data[20];

    MCP4725_setValue(&dac, (uint16_t)(0*4095)/5, MCP4725_FAST_MODE, MCP4725_POWER_DOWN_OFF);

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
            HAL_UART_Receive(&huart2, (uint8_t*)data, sizeof(data), 1000);
            slope = atof(data);
            memset(data, 0, sizeof(data));
            HAL_UART_Receive(&huart2, (uint8_t*)data, sizeof(data), 1000);
            yint = atof(data);
        }

        if (userInput == 'i') {
            HAL_UART_Receive(&huart2, (uint8_t*)data, sizeof(data), 1000);
            pres_start = atof(data);
            memset(data, 0, sizeof(data));
            HAL_UART_Receive(&huart2, (uint8_t*)data, sizeof(data), 1000);
            pres_incr = atof(data);
            memset(data, 0, sizeof(data));
            HAL_UART_Receive(&huart2, (uint8_t*)data, sizeof(data), 1000);
            pres_num_incr = atoi(data);
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
