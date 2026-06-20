#ifndef ELEVATE_H
#define ELEVATE_H

#include <Arduino.h>
#include <AccelStepper.h>
#include "pin_def.h"

extern AccelStepper stepperY;
extern AccelStepper stepperZ;

const int HEIGHT_Y = 3655; // 待定
const int HEIGHT_Z = 3665; // 待定
const int HEIGHT_READY = 3000;

// 初始化升降馬達設定
void setupElevate() {
    // 啟用 Y 軸驅動器
    pinMode(Y_ENABLE_PIN, OUTPUT);
    digitalWrite(Y_ENABLE_PIN, LOW);

    // 啟用 Z 軸驅動器
    pinMode(Z_ENABLE_PIN, OUTPUT);
    digitalWrite(Z_ENABLE_PIN, LOW);

    // 設定 Y 軸運動參數
    stepperY.setMaxSpeed(800.0);
    stepperY.setAcceleration(200.0);
    stepperY.setCurrentPosition(HEIGHT_READY);

    // 設定 Z 軸運動參數
    stepperZ.setMaxSpeed(800.0);
    stepperZ.setAcceleration(200.0);
    stepperZ.setCurrentPosition(HEIGHT_READY);
}

void elevator_White() {
    // 1. 爬升到指定高度 HEIGHT
    stepperY.moveTo(HEIGHT_Y);
    while (stepperY.distanceToGo() != 0) {
        stepperY.run();
    }
    
    // 2. 抵達頂端，停留 200ms
    delay(200); 
    
    // 3. 降回最底部原點 (0)
    stepperY.moveTo(0);
    while (stepperY.distanceToGo() != 0) {
        stepperY.run();
    }

    delay(100);

    stepperY.moveTo(HEIGHT_READY);
    while (stepperY.distanceToGo() != 0) {
        stepperY.run();
    }
}

void elevator_Black() {
    // 1. 爬升到指定高度 HEIGHT
    stepperZ.moveTo(HEIGHT_Z);
    while (stepperZ.distanceToGo() != 0) {
        stepperZ.run();
    }
    
    // 2. 抵達頂端，停留 200ms
    delay(200); 
    
    // 3. 降回最底部原點 (0)
    stepperZ.moveTo(0);
    while (stepperZ.distanceToGo() != 0) {
        stepperZ.run();
    }

    stepperZ.moveTo(HEIGHT_READY);
    while (stepperZ.distanceToGo() != 0) {
        stepperZ.run();
    }
}

#endif