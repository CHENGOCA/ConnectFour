#ifndef SORTING_H
#define SORTING_H

#include <Arduino.h>
#include <Servo.h>
#include "pin_def.h"

extern Servo servo_180;
extern Servo servo_360;
const int threshold_N = 4; 
int b_count = 4;
int w_count = 3;

enum SortState {
    IDLE,               
    SERVO_MOVE_OUT,     
    SERVO_HOLD,         
    SERVO_MOVE_BACK,    
    SORT_COOLDOWN       
};

SortState currentState = IDLE;
unsigned long stateStartTime = 0; 
int currentPos = 90;              
int targetPos = 90;               
int moveDirection = 0;            
unsigned long lastServoUpdateTime = 0; 

// ====== 濾波去彈跳（Debounce）核心變數 ======
int lastSampledM = 2;              
unsigned long mStateStableStartTime = 0; 
const unsigned long DEBOUNCE_DELAY = 300; 

int confirmedM = 2; 
int lastServo360Speed = -1;

// 📢 新增：序列埠定時除錯變數
unsigned long lastLogTime = 0;
const unsigned long LOG_INTERVAL = 100; // ⏱️ 每 300 毫秒（0.3秒）在螢幕印一次狀態

void setupSorting() {
    servo_180.attach(SERVO_180_PIN);  
    servo_180.write(90);                  
    servo_360.attach(SERVO_360_PIN);
    servo_360.write(90);                  
    pinMode(SORT_IR_PIN, INPUT);  
    
    mStateStableStartTime = millis(); 
    lastSampledM = 2; 
    confirmedM = 2; 
    lastServo360Speed = -1;
    lastLogTime = 0;
}

void setServo360Speed(int speed) {
    if (speed != lastServo360Speed) {
        servo_360.write(speed);
        lastServo360Speed = speed;
    }
}

void Sort() {
    unsigned long currentTime = millis();

    // ==================== 第一層：全時運作的獨立濾波器 ====================
    int check = analogRead(SORT_IR_PIN);
    int currentM;
    if (check < 80) currentM = 1;
    else if (check >= 80 && check <= 750) currentM = 0;
    else currentM = 2;

    // 1. 只要硬體即時雜訊跟上一刻不同，就代表還在晃動，不斷刷新計時器
    if (currentM != lastSampledM) {
        mStateStableStartTime = currentTime;
    //   Serial.print("shaking, curr:");
    //   Serial.println(currentM);
    //   Serial.print("shaking, lat:");
    //   Serial.println(lastSampledM);
    }

    // 2. 隨時把當前狀態存下來，當作下一輪的比對基礎
    lastSampledM = currentM;

    // 3. 只有當訊號已經穩定維持了足夠久 (DEBOUNCE_DELAY)
    if ((currentTime - mStateStableStartTime) >= DEBOUNCE_DELAY) {
        // Serial.print("start switching from ");
        // Serial.print(confirmedM);
        // Serial.print(" to ");
        // Serial.print(currentM);
        // 4. 且這個穩定訊號跟我們「目前認定的狀態」不一樣時，才允許更新一次！
        if (currentM != confirmedM) {
            confirmedM = currentM; 
        }
    }

    // ==================== 📢 新增：定時螢幕除錯監控 ====================
    if (currentTime - lastLogTime >= LOG_INTERVAL) {
        Serial.print(b_count);
        Serial.println(w_count);
        lastLogTime = currentTime;
        
        Serial.print("[DEBUG] State: ");
        // 將 enum 轉換成看得懂的文字印出
        switch(currentState) {
            case IDLE:            Serial.print("IDLE           "); break;
            case SERVO_MOVE_OUT:  Serial.print("SERVO_MOVE_OUT "); break;
            case SERVO_HOLD:      Serial.print("SERVO_HOLD     "); break;
            case SERVO_MOVE_BACK: Serial.print("SERVO_MOVE_BACK"); break;
            case SORT_COOLDOWN:   Serial.print("SORT_COOLDOWN  "); break;
        }
        
        Serial.print(" | ConfirmedM: ");
        switch(confirmedM) {
            case 1:  Serial.print("1 (WHITE)"); break;
            case 0:  Serial.print("0 (BLACK)"); break;
            case 2:  Serial.print("2 (EMPTY)"); break;
        }
        
        Serial.print(" | IR Raw: ");
        Serial.println(check); // 順便把即時的類比讀值印出來對照
    }

    // ==================== 第二層：核心狀態機邏輯 ====================
    switch (currentState) {
        
        case IDLE: {
            if (confirmedM == 2) {
                setServo360Speed(105); 
            }
            else if (confirmedM == 0) {
                setServo360Speed(90);  
                // if (b_count >= threshold_N) return;
                
                targetPos = 120; 
                moveDirection = 1;
                currentState = SERVO_MOVE_OUT; 
                stateStartTime = currentTime;
            }
            else if (confirmedM == 1) {
                setServo360Speed(90);  
                // if (w_count >= threshold_N) return;
                
                targetPos = 60;  
                moveDirection = -1;
                currentState = SERVO_MOVE_OUT; 
                stateStartTime = currentTime;
            }
            break;
        }

        case SERVO_MOVE_OUT:
            if (currentTime - lastServoUpdateTime >= 5) {
                lastServoUpdateTime = currentTime;
                currentPos += moveDirection;
                servo_180.write(currentPos);
                
                if (currentPos == targetPos) {
                    currentState = SERVO_HOLD;
                    stateStartTime = currentTime; 
                }
            }
            break;

        case SERVO_HOLD:
            if (currentTime - stateStartTime >= 200) {
                moveDirection = -moveDirection; 
                currentState = SERVO_MOVE_BACK;
            }
            break;

        case SERVO_MOVE_BACK:
            if (currentTime - lastServoUpdateTime >= 5) {
                lastServoUpdateTime = currentTime;
                currentPos += moveDirection;
                servo_180.write(currentPos);
                
                if (currentPos == 90) {
                    if (targetPos == 120) b_count++;
                    else if (targetPos == 60) w_count++;
                    
                    currentState = SORT_COOLDOWN;
                    stateStartTime = currentTime;
                }
            }
            break;

        case SORT_COOLDOWN:
            if (currentTime - stateStartTime >= 500) {
                currentState = IDLE; 
                lastSampledM = currentM; 
                mStateStableStartTime = currentTime;
            }
            break;
    }
}
#endif