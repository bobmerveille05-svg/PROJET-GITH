//+------------------------------------------------------------------+
//|                               SMC_Pro_Indicator/Dashboard/MTF_Dashboard.mqh |
//|                      Copyright 2025, ProDev SMC Team             |
//|                                        https://yourdevsite.com |
//+------------------------------------------------------------------+
#include "../Config/SMC_Params.mqh"

class CMTF_Dashboard
{
private:
   string m_label_name;
   int    m_ma_period;

public:
   //+------------------------------------------------------------------+
   //| Constructor                                                      |
   //+------------------------------------------------------------------+
   void CMTF_Dashboard()
   {
      m_label_name = "SMC_PRO_DASHBOARD_" + IntegerToString(ChartID());
      m_ma_period = 50; // Standard period for trend direction
   }

   //+------------------------------------------------------------------+
   //| Draw or update the dashboard on the chart                        |
   //+------------------------------------------------------------------+
   void DrawDashboard()
   {
      if(!EnableDashboard)
      {
         ClearDashboard(); // Clear if it was previously enabled
         return;
      }

      // --- Build the dashboard text ---
      string text = "📊 SMC Pro Dashboard\n";
      text += "---------------------\n";
      text += "TF    | Trend\n";
      text += "M15:  " + GetTrend(PERIOD_M15) + "\n";
      text += "H1:    " + GetTrend(PERIOD_H1) + "\n";
      text += "H4:    " + GetTrend(PERIOD_H4) + "\n";
      text += "D1:    " + GetTrend(PERIOD_D1);

      // --- Create or update the label object ---
      if(ObjectFind(0, m_label_name) != 0)
      {
         ObjectCreate(0, m_label_name, OBJ_LABEL, 0, 0, 0);
         ObjectSetInteger(0, m_label_name, OBJPROP_XDISTANCE, 10);
         ObjectSetInteger(0, m_label_name, OBJPROP_YDISTANCE, 20);
         ObjectSetInteger(0, m_label_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
         ObjectSetInteger(0, m_label_name, OBJPROP_BGCOLOR, clrBlack);
         ObjectSetInteger(0, m_label_name, OBJPROP_BORDER_COLOR, clrGray);
      }

      ObjectSetString(0, m_label_name, OBJPROP_TEXT, text);
      ObjectSetInteger(0, m_label_name, OBJPROP_COLOR, clrWhite);
      ObjectSetInteger(0, m_label_name, OBJPROP_FONTSIZE, 8);
      ObjectSetString(0, m_label_name, OBJPROP_FONT, "Lucida Console");
   }

   //+------------------------------------------------------------------+
   //| Clear the dashboard from the chart                               |
   //+------------------------------------------------------------------+
   void ClearDashboard()
   {
      if(ObjectFind(0, m_label_name) == 0)
      {
         ObjectDelete(0, m_label_name);
      }
   }

private:
   //+------------------------------------------------------------------+
   //| Get trend for a specific timeframe                               |
   //+------------------------------------------------------------------+
   string GetTrend(ENUM_TIMEFRAMES tf)
   {
      // Get the last 2 closes and MA values to determine trend
      double closes[2];
      double mas[2];

      if(CopyClose(_Symbol, tf, 0, 2, closes) < 2) return "Loading...";
      if(CopyBuffer(iMA(_Symbol, tf, m_ma_period, 0, MODE_SMA, PRICE_CLOSE), 0, 0, 2, mas) < 2) return "Loading...";

      double close_now = closes[1];
      double ma_now = mas[1];

      if(close_now > ma_now)
         return "▲ Bullish";
      else if(close_now < ma_now)
         return "▼ Bearish";
      else
         return "Neutral";
   }
};
