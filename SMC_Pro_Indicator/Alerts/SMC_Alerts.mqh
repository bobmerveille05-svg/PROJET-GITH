//+------------------------------------------------------------------+
//|                                     SMC_Pro_Indicator/Alerts/SMC_Alerts.mqh |
//|                      Copyright 2025, ProDev SMC Team             |
//|                                        https://yourdevsite.com |
//+------------------------------------------------------------------+
#include "../Core/Structures/SMC_Structs.mqh"
#include "../Config/SMC_Params.mqh"

class CSMC_Alerts
{
private:
   datetime m_last_ob_alert_time;
   datetime m_last_fvg_alert_time;
   datetime m_last_structure_alert_time;

public:
   //+------------------------------------------------------------------+
   //| Constructor                                                      |
   //+------------------------------------------------------------------+
   void CSMC_Alerts()
   {
      m_last_ob_alert_time = 0;
      m_last_fvg_alert_time = 0;
      m_last_structure_alert_time = 0;
   }

   //+------------------------------------------------------------------+
   //| Check for new signals and trigger alerts                         |
   //+------------------------------------------------------------------+
   void CheckAlerts(CArrayObj *orderBlocks, CArrayObj *fvgs, CArrayObj *structures)
   {
      if(!EnableAlerts) return;

      // --- Check for new Order Blocks ---
      if(AlertOnNewOB && CheckPointer(orderBlocks) != POINTER_INVALID && orderBlocks.Total() > 0)
      {
         SMC_OrderBlock *last_ob = orderBlocks.At(orderBlocks.Total() - 1);
         if(CheckPointer(last_ob) != POINTER_INVALID && last_ob.time > m_last_ob_alert_time)
         {
            m_last_ob_alert_time = last_ob.time;
            string desc = (last_ob.type == BULLISH ? "Bullish" : "Bearish") + " Order Block";
            TriggerAlert(desc, last_ob.bottom_price);
         }
      }

      // --- Check for new FVGs ---
      if(AlertOnNewFVG && CheckPointer(fvgs) != POINTER_INVALID && fvgs.Total() > 0)
      {
         SMC_FVG *last_fvg = fvgs.At(fvgs.Total() - 1);
         if(CheckPointer(last_fvg) != POINTER_INVALID && last_fvg.time > m_last_fvg_alert_time)
         {
            m_last_fvg_alert_time = last_fvg.time;
            string desc = (last_fvg.type == BULLISH ? "Bullish" : "Bearish") + " FVG";
            TriggerAlert(desc, last_fvg.bottom_price);
         }
      }

      // --- Check for new Structures ---
      if(AlertOnBOS && CheckPointer(structures) != POINTER_INVALID && structures.Total() > 0)
      {
         SMC_Structure *last_struc = structures.At(structures.Total() - 1);
         if(CheckPointer(last_struc) != POINTER_INVALID && last_struc.time > m_last_structure_alert_time)
         {
            m_last_structure_alert_time = last_struc.time;
            string desc = (last_struc.type == BOS ? "BOS" : "CHoCH") + " (" + (last_struc.direction == BULLISH ? "Bullish" : "Bearish") + ")";
            TriggerAlert(desc, last_struc.price_level);
         }
      }
   }

private:
   //+------------------------------------------------------------------+
   //| Send notifications based on user settings                        |
   //+------------------------------------------------------------------+
   void TriggerAlert(string signal_type, double price)
   {
      string message = "[SMC Pro] New " + signal_type + " on " + _Symbol + " " + PeriodToString(_Period) + " @ " + DoubleToString(price, _Digits);

      // Standard MT5 Alert
      Alert(message);

      // Push Notification
      if(EnableMT5Notifications)
      {
         SendNotification(message);
      }

      // Email
      if(EnableEmailAlerts)
      {
         SendMail("SMC Pro Alert: " + _Symbol, message);
      }

      // Telegram
      if(EnableTelegramAlerts)
      {
         SendTelegram(message);
      }
   }

   //+------------------------------------------------------------------+
   //| Telegram Sender (Placeholder)                                    |
   //+------------------------------------------------------------------+
   void SendTelegram(string message)
   {
      // Full Telegram implementation with photo requires advanced WebRequest handling.
      // This is a simplified text-only version.
      // Note: Allow WebRequest in MT5 options for this to work.
      string url = "https://api.telegram.org/bot" + TelegramBotToken + "/sendMessage";
      string headers = "Content-Type: application/x-www-form-urlencoded";
      string params = "chat_id=" + TelegramChatID + "&text=" + StringToUrl(message);

      char post_data[], result[];
      int timeout = 5000; // 5 seconds

      StringToCharArray(params, post_data);

      ResetLastError();
      int res = WebRequest("POST", url, headers, timeout, post_data, result, NULL);

      if(res != 200)
      {
         Print("Telegram alert failed. Response code: ", res, ". Error: ", GetLastError());
      }
   }

   //+------------------------------------------------------------------+
   //| Helper to URL-encode a string                                    |
   //+------------------------------------------------------------------+
   string StringToUrl(string text)
   {
      string result = "";
      int len = StringLen(text);
      for(int i = 0; i < len; i++)
      {
         ushort char_code = StringGetCharacter(text, i);
         if((char_code >= 'a' && char_code <= 'z') ||
            (char_code >= 'A' && char_code <= 'Z') ||
            (char_code >= '0' && char_code <= '9') ||
            (char_code == '-' || char_code == '.' || char_code == '_' || char_code == '~'))
         {
            result += CharToString(char_code);
         }
         else
         {
            result += StringFormat("%%%02X", char_code);
         }
      }
      return result;
   }
};
