//+------------------------------------------------------------------+
//|                                SMC_Pro_Indicator/Core/Structures/SMC_Structs.mqh |
//|                      Copyright 2025, ProDev SMC Team             |
//|                                        https://yourdevsite.com |
//+------------------------------------------------------------------+
#property copyright "2025, ProDev SMC Team"
#property link      "https://yourdevsite.com"

#include <Object.mqh>

// --- Enum for universal types ---
enum ENUM_ZONE_TYPE
{
   BULLISH,
   BEARISH
};

//+------------------------------------------------------------------+
//| Class for Order Blocks (OB)                                      |
//+------------------------------------------------------------------+
class SMC_OrderBlock : public CObject
{
public:
   ENUM_ZONE_TYPE type;         // Bullish or Bearish OB
   double      top_price;    // Top price of the OB candle
   double      bottom_price; // Bottom price of the OB candle
   datetime    time;         // Time of the OB candle
   int         bar_index;    // Bar index of the OB
   bool        is_mitigated; // Has the OB been mitigated (price returned to it)?
};

//+------------------------------------------------------------------+
//| Class for Fair Value Gaps (FVG)                                  |
//+------------------------------------------------------------------+
class SMC_FVG : public CObject
{
public:
   ENUM_ZONE_TYPE type;         // Bullish FVG (gap up) or Bearish FVG (gap down)
   double      top_price;    // Top of the gap
   double      bottom_price; // Bottom of the gap
   datetime    time;         // Time of the middle candle of the FVG pattern
   int         bar_index;    // Bar index of the FVG
   bool        is_filled;    // Has the FVG been filled?
};

//+------------------------------------------------------------------+
//| Class for Market Structure (BOS/CHoCH)                           |
//+------------------------------------------------------------------+
enum ENUM_STRUCTURE_TYPE
{
   BOS,    // Break of Structure
   CHoCH   // Change of Character
};

class SMC_Structure : public CObject
{
public:
   ENUM_STRUCTURE_TYPE type;   // BOS or CHoCH
   ENUM_ZONE_TYPE      direction; // Bullish (break of high) or Bearish (break of low)
   double            price_level; // Price level of the break
   datetime          time;        // Time of the break
   int               bar_index;   // Bar index of the break
};

//+------------------------------------------------------------------+
//| Class for Supply and Demand Zones                                |
//+------------------------------------------------------------------+
enum ENUM_SD_ZONE_TYPE
{
   SUPPLY,
   DEMAND
};

class SMC_Zone : public CObject
{
public:
   ENUM_SD_ZONE_TYPE type;      // Supply or Demand
   double            top_price;
   double            bottom_price;
   datetime          time;
   int               bar_index;
   bool              is_mitigated;
};


//+------------------------------------------------------------------+
//| Class for Candle Patterns                                        |
//+------------------------------------------------------------------+
enum ENUM_CANDLE_PATTERN
{
   PATTERN_ENGULFING_BULLISH,
   PATTERN_ENGULFING_BEARISH,
   PATTERN_INSIDE_BAR,
};

class SMC_CandlePattern : public CObject
{
public:
   ENUM_CANDLE_PATTERN type;
   double              price_level; // e.g., high or low of the pattern
   datetime            time;
   int                 bar_index;
};
