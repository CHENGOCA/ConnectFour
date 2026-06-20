#include <Servo.h>
#include <AccelStepper.h>
#include "pin_def.h"          

/*===========================全域變數===========================*/
Servo servo_180;
Servo servo_360;
AccelStepper stepperX(AccelStepper::DRIVER, X_STEP_PIN, X_DIR_PIN);
AccelStepper stepperY(AccelStepper::DRIVER, Y_STEP_PIN, Y_DIR_PIN);
AccelStepper stepperZ(AccelStepper::DRIVER, Z_STEP_PIN, Z_DIR_PIN);

bool gaming = false;
/*=============================================================*/

#include "bluetooth.h"      
#include "sorting.h"       
#include "elevate.h"
#include "place.h"

// ⏳ 時間標記變數，用來在遊戲進行中進行非阻塞定時分揀
unsigned long lastSortTime = 0;

void setup() {
  // 1. 基本通訊初始化
  Serial.begin(115200);
  Serial2.begin(9600);

  // 2. 硬體腳位與基本參數初始化
  setupPlace();
  setupSorting();
  setupElevate();
  
  // 3. (可選) 物理定位歸零：如果你的極限開關已經接好，可以把 place.h 的 initialToCol0 註解打開並在這裡呼叫
  // initialToCol0();

  Serial.println("[SYSTEM] Arduino Ready. Waiting for Game Start ('S')...");
}

unsigned long lastSortRunTime = 0;
const unsigned long SORT_INTERVAL = 50; // 每 50 毫秒執行一次

void loop() {
  unsigned long currentTime = millis();
  // 1. 不斷檢查並處理藍牙/序列埠傳來的指令
  BT_Process();
  
  // 📢 改動：當遊戲結束或尚未開始時 (gaming == false)，開啟分揀馬達與紅外線偵測
  if (gaming == false || gaming == true) {
      if (currentTime - lastSortRunTime >= SORT_INTERVAL) {
        lastSortRunTime = currentTime; // 碼表按下去，重新計時   
        Sort(); // 👈 呼叫你 sorting.h 裡面的分揀狀態機
    }

  } else {
    // 遊戲正在進行中時，分揀馬達停止滾動，專心讓步進馬達落子
    servo_360.write(90);
  }
  
}
