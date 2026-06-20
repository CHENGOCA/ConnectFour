#ifndef BLUETOOTH_H
#define BLUETOOTH_H

#include <Arduino.h>

// 宣告在 main.ino 裡面定義過的馬達與全域變數，讓這個檔案可以合法讀寫它們
extern bool gaming;
extern AccelStepper stepperX;
extern AccelStepper stepperY;
extern AccelStepper stepperZ;

// 📢 新增：宣告 sorting.h 裡面的濾波變數，讓這裡可以重置它們
extern int lastSampledM;
extern unsigned long mStateStableStartTime;

extern int b_count;
extern int w_count;

// 宣告定義在 place.h 與 elevate.h 裡面的動作函式
void goToCol(int col);
void elevator_White();
void elevator_Black();

// 📢 註解掉：不需要再記錄上一次落子的顏色
// char lastColor = ' ';

void BT_Process() {
  // 🔄 改動：檢查藍牙 Serial2 是否有資料進來
  if (Serial2.available() > 0) {
    
    // 🔄 改動：從 Serial2 讀取第一個字元
    char firstChar = Serial2.read();

    // 【情況 A】尚未開始遊戲：等待開局訊號 'S' 或 's'
    if (!gaming) {
      if (firstChar == 'S' || firstChar == 's') {
        gaming = true;
        // 📢 註解掉：開局時不需要重置顏色
        // lastColor = ' '; 
        Serial.println("Game Started! Status: gaming = true"); // 輸出到電腦 Console
        delay(500);
        Serial2.print("ACK_DONE\n"); // 🔄 改動：回傳給 Serial2 連接的電腦端
      }
      return; // 結束這一輪檢查
    }

    // 【情況 B】遊戲進行中：處理兩個字元的落子指令 (例如 W1, B5)
    if (gaming) {
      
      // 📢 改動：檢查是否收到遊戲結束訊號 'E' 或 'e'
      if (firstChar == 'E' || firstChar == 'e') {
        gaming = false; // 關閉遊戲狀態，這會自動封鎖後續的落子指令
        Serial.println("Game Over Command Received. Stop receiving moves.");
        
        // 🔄 改動：清空 Serial2 可能殘留的序列埠緩衝資料
        while (Serial2.available() > 0) { Serial2.read(); }

        // 📢 改動：在啟動分類前，強制把濾波計時器與狀態校正為「現在這一個瞬間」
        // 這樣第一顆球掉下來時，去彈跳計時才會100%從0毫秒重新乾淨計算！
        lastSampledM = 2;                     // 預設重置為沒球狀態
        mStateStableStartTime = millis();    // 時間同步為現在
        
        // 執行 X 軸歸位回到 col 0 (會阻塞直到抵達)
        Serial.println("Moving X-axis back to Col 0...");
        goToCol(0);
        Serial.println("X-axis arrived at Col 0. Sorting system activated.\n---");
        Serial2.print("ACK_DONE\n"); // 🔄 改動：回傳給 Serial2 連接的電腦端
        return; // 結束這輪處理
      }

      // ⏳ ⏳ 等待第二個字元進入 Serial2 快取區
      unsigned long timeout = millis();
      while (Serial2.available() == 0) {
        if (millis() - timeout > 150) { // 150ms 超時保護，避免程式卡死
          Serial.println("Error: Bluetooth Command Timeout. Missing second character.");
          return;
        }
      }

      // 🔄 改動：從 Serial2 讀取第二個字元
      char secondChar = Serial2.read();
      
      // 將字元 '0' ~ '6' 轉換為整數 0 ~ 6
      int targetCol = secondChar - '0';

      // 驗證指令合法性：必須是 W 或 B 開頭，且格子在 0 到 6 之間
      if ((firstChar == 'W' || firstChar == 'B') && (targetCol >= 0 && targetCol <= 6)) {
        
        /* 📢 註解掉防呆機制 1：不再檢查連續重複同顏色落子
        if (firstChar == lastColor) {
          Serial.print("Error: Anti-idiot protection triggered. Cannot play same color twice in a row! (Skipped: ");
          Serial.print(firstChar);
          Serial.println(secondChar);
          return; // 直接拒絕執行，退出
        }
        */

        Serial.print("Executing -> Color: ");
        Serial.print(firstChar);
        Serial.print(", Column: ");
        Serial.println(targetCol);

        // 🎯 步驟 1：先執行 X 軸水平定位 (此函式內含 while 迴圈，會阻塞直到抵達)
        goToCol(targetCol);
        Serial.println("X-axis reached destination.");

        // 🎯 步驟 2：X 軸停好後，根據棋子顏色，執行對應垂直軸的提升落子
        if (firstChar == 'W') {
          Serial.println("Starting Y-axis elevation for White...");
          elevator_White(); // 升上去落子，再降回原點

          w_count--;
        } 
        else if (firstChar == 'B') {
          Serial.println("Starting Z-axis elevation for Black...");
          elevator_Black(); // 升上去落子，再降回原點

          b_count--;
        }

        // 📢 註解掉防呆機制 2：成功落子後，不需要更新最後落子顏色
        // lastColor = firstChar;

        // 📢 防呆機制 3：馬達跑完後，清空「在馬達運轉期間 Serial2 偷偷傳過來」的所有雜訊與指令
        while (Serial2.available() > 0) {
          Serial2.read(); 
        }

        // 🎯 步驟 3：所有動作安全完成，發送 ACK 給電腦，代表電腦可以下下一手了
        Serial2.print("ACK_DONE\n"); // 🔄 改動：回傳給 Serial2 連接的電腦端
        Serial.println("Action complete. Waiting for next turn.\n---");

      } else {
        // 如果收到不認得的雜訊字串，跳過不處理並列印警告
        Serial.print("Unknown command format skipped: ");
        Serial.print(firstChar);
        Serial.println(secondChar);
      }
    }
  }
}

#endif