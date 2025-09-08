//+------------------------------------------------------------------+
//|                                           SMC_Pro_Indicator/Core/SMC_Core.mqh |
//|                      Copyright 2025, ProDev SMC Team             |
//|                                        https://yourdevsite.com |
//+------------------------------------------------------------------+
#include "Structures/SMC_Structs.mqh"
#include <Arrays/ArrayObj.mqh>

class CSMC_Core
{
private:
   // --- Price Data ---
   const double    *m_open, *m_high, *m_low, *m_close;
   const datetime  *m_time;
   const long      *m_volume;
   int             m_rates_total;

   // --- Detected Structures ---
   CArrayObj*      m_orderBlocks;
   CArrayObj*      m_fvgs;
   CArrayObj*      m_structures;
   // More arrays for other structures can be added here

   // --- Swing points for structure detection ---
   double m_lastSwingHigh;
   double m_lastSwingLow;
   int    m_lastSwingHighIdx;
   int    m_lastSwingLowIdx;

public:
   //+------------------------------------------------------------------+
   //| Constructor                                                      |
   //+------------------------------------------------------------------+
   void CSMC_Core()
   {
      m_orderBlocks = new CArrayObj();
      m_orderBlocks.FreeMode(true); // Automatically delete objects

      m_fvgs = new CArrayObj();
      m_fvgs.FreeMode(true);

      m_structures = new CArrayObj();
      m_structures.FreeMode(true);

      m_lastSwingHigh = 0;
      m_lastSwingLow = 0;
      m_lastSwingHighIdx = -1;
      m_lastSwingLowIdx = -1;
   }

   //+------------------------------------------------------------------+
   //| Destructor                                                       |
   //+------------------------------------------------------------------+
   void ~CSMC_Core()
   {
      delete m_orderBlocks;
      delete m_fvgs;
      delete m_structures;
   }

   //+------------------------------------------------------------------+
   //| Update price data for calculations                               |
   //+------------------------------------------------------------------+
   void UpdateData(const double &open[], const double &high[], const double &low[], const double &close[],
                   const datetime &time[], const long &volume[], int rates_total)
   {
      m_open = open;
      m_high = high;
      m_low = low;
      m_close = close;
      m_time = time;
      m_volume = volume;
      m_rates_total = rates_total;
   }

   //+------------------------------------------------------------------+
   //| Clear all detected structures                                    |
   //+------------------------------------------------------------------+
   void ClearAll()
   {
      m_orderBlocks.Clear();
      m_fvgs.Clear();
      m_structures.Clear();
   }

   //+------------------------------------------------------------------+
   //| Detect Order Blocks                                              |
   //+------------------------------------------------------------------+
   void DetectOrderBlocks(int lookback, double min_pips)
   {
      double pip = _Point;
      if (StringFind(_Symbol, "JPY") != -1) pip *= 100;

      for(int i = 1; i < lookback && i < m_rates_total - 2; i++)
      {
         // Bullish OB: A down candle followed by a strong up move that breaks the high of the down candle.
         if (m_close[i] < m_open[i] && m_close[i-1] > m_open[i-1] && m_high[i-1] > m_high[i])
         {
            if (MathAbs(m_open[i] - m_close[i]) / pip > min_pips)
            {
               SMC_OrderBlock *ob = new SMC_OrderBlock();
               ob.type = BULLISH;
               ob.top_price = m_high[i];
               ob.bottom_price = m_low[i];
               ob.time = m_time[i];
               ob.bar_index = i;
               ob.is_mitigated = false; // Add mitigation logic later
               m_orderBlocks.Add(ob);
            }
         }
         // Bearish OB: An up candle followed by a strong down move that breaks the low of the up candle.
         else if (m_close[i] > m_open[i] && m_close[i-1] < m_open[i-1] && m_low[i-1] < m_low[i])
         {
             if (MathAbs(m_open[i] - m_close[i]) / pip > min_pips)
             {
               SMC_OrderBlock *ob = new SMC_OrderBlock();
               ob.type = BEARISH;
               ob.top_price = m_high[i];
               ob.bottom_price = m_low[i];
               ob.time = m_time[i];
               ob.bar_index = i;
               ob.is_mitigated = false;
               m_orderBlocks.Add(ob);
             }
         }
      }
   }

   //+------------------------------------------------------------------+
   //| Detect Fair Value Gaps (FVG)                                     |
   //+------------------------------------------------------------------+
   void DetectFVGs(int lookback)
   {
      for(int i = 1; i < lookback && i < m_rates_total - 2; i++)
      {
         // Bullish FVG: Gap between high of candle i and low of candle i-2
         if (m_high[i+1] < m_low[i-1])
         {
            SMC_FVG *fvg = new SMC_FVG();
            fvg.type = BULLISH;
            fvg.top_price = m_low[i-1];
            fvg.bottom_price = m_high[i+1];
            fvg.time = m_time[i];
            fvg.bar_index = i;
            fvg.is_filled = false; // Add fill logic later
            m_fvgs.Add(fvg);
         }
         // Bearish FVG: Gap between low of candle i and high of candle i-2
         else if (m_low[i+1] > m_high[i-1])
         {
            SMC_FVG *fvg = new SMC_FVG();
            fvg.type = BEARISH;
            fvg.top_price = m_high[i-1];
            fvg.bottom_price = m_low[i+1];
            fvg.time = m_time[i];
            fvg.bar_index = i;
            fvg.is_filled = false;
            m_fvgs.Add(fvg);
         }
      }
   }

   //+------------------------------------------------------------------+
   //| Detect Market Structure (BOS/CHoCH) - Simplified               |
   //+------------------------------------------------------------------+
   void DetectStructures(int lookback)
   {
       // This is a simplified implementation. A robust one would use ZigZag or more complex fractal analysis.
       // Find initial swing points
       m_lastSwingHighIdx = iHighest(NULL, 0, MODE_HIGH, lookback, 1);
       m_lastSwingLowIdx = iLowest(NULL, 0, MODE_LOW, lookback, 1);
       m_lastSwingHigh = m_high[m_lastSwingHighIdx];
       m_lastSwingLow = m_low[m_lastSwingLowIdx];

       string trend = "UNCERTAIN";
       if(m_lastSwingHighIdx < m_lastSwingLowIdx) trend = "UP";
       if(m_lastSwingHighIdx > m_lastSwingLowIdx) trend = "DOWN";

       for(int i = 1; i < m_lastSwingHighIdx && i < m_lastSwingLowIdx; i++)
       {
           if(trend == "UP" && m_high[i] > m_lastSwingHigh)
           {
               SMC_Structure *struc = new SMC_Structure();
               struc.type = BOS;
               struc.direction = BULLISH;
               struc.price_level = m_lastSwingHigh;
               struc.time = m_time[m_lastSwingHighIdx];
               struc.bar_index = m_lastSwingHighIdx;
               m_structures.Add(struc);

               // Update for next leg
               m_lastSwingLow = m_low[iLowest(NULL, 0, MODE_LOW, m_lastSwingHighIdx - i, i)];
               m_lastSwingHigh = m_high[i];
           }
           else if(trend == "DOWN" && m_low[i] < m_lastSwingLow)
           {
               // ... similar logic for Bearish BOS
           }
           // Add CHoCH logic: break of the last minor swing against the trend
       }
   }


   //+------------------------------------------------------------------+
   //| Getters for other modules                                        |
   //+------------------------------------------------------------------+
   CArrayObj* GetOrderBlocks() { return m_orderBlocks; }
   CArrayObj* GetFVGs()        { return m_fvgs; }
   CArrayObj* GetStructures()  { return m_structures; }
};
