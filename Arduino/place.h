#ifndef PLACE_H
#define PLACE_H

#include <Arduino.h>
#include <AccelStepper.h>
#include "pin_def.h"

extern AccelStepper stepperX;

// 步進馬達轉一圈步數
const int ONE_BLOCK = 223; // 待測
const int TO_FIRST_BLOCK = 0; //待測

void setupPlace() {
    pinMode(X_ENABLE_PIN, OUTPUT);
    digitalWrite(X_ENABLE_PIN, LOW); // LOW 為啟用馬達驅動器
    stepperX.setMaxSpeed(400.0);    // 設定最大速度 (每秒步數)
    stepperX.setAcceleration(200.0);
    stepperX.setCurrentPosition(0);
}

// 移動到指定位置(col 0-6)
void goToCol(int col) {
    int target = 0;

    if (col == 0) {
        target = TO_FIRST_BLOCK;
    } else if (col >= 1 && col <= 6) {
        target = TO_FIRST_BLOCK + col * ONE_BLOCK;
    } else {
        return; // 若超出 0-6 範圍則安全退出不動作
    }

    // 告訴馬達目標位置
    stepperX.moveTo(target);

    // 阻塞式運轉，直到馬達確實到達指定步數位置
    while (stepperX.distanceToGo() != 0) {
        stepperX.run();
    }
}

#endif

