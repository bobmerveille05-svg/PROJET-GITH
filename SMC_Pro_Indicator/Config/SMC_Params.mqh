//+------------------------------------------------------------------+
//|                                           SMC_Pro_Indicator/Config/SMC_Params.mqh |
//|                      Copyright 2025, ProDev SMC Team             |
//|                                        https://yourdevsite.com |
//+------------------------------------------------------------------+
#property copyright "2025, ProDev SMC Team"
#property link      "https://yourdevsite.com"

// --- Helper for creating input groups in MT5 ---
#define input_group(name) \
   input group name

//+------------------------------------------------------------------+
//| 🔹 GENERAL SETTINGS                                              |
//+------------------------------------------------------------------+
input_group("🔹 General Settings");
input int                MaxZonesToShow          = 10;                  // Max number of each zone type to display
input ENUM_TIMEFRAMES    HTF                     = PERIOD_H4;           // Higher Timeframe for confirmation
input bool               EnableHTFConfirmation   = false;               // Enable/Disable HTF confirmation filter

//+------------------------------------------------------------------+
//| 🔸 STRUCTURE SETTINGS (BOS/CHoCH)                                |
//+------------------------------------------------------------------+
input_group("🔸 Structure Settings (BOS/CHoCH)");
enum ENUM_STRUCTURE_MODE
{
   MODE_WICK,         // Breakout by wick
   MODE_BODY,         // Breakout by candle body close
   MODE_TWO_CANDLES   // Breakout by two consecutive closes
};
input ENUM_STRUCTURE_MODE StructureMode          = MODE_WICK;           // Breakout detection mode
input int                 StructureLookback      = 120;                 // Bars to look back for swing points

//+------------------------------------------------------------------+
//| 🔸 ORDER BLOCK SETTINGS                                          |
//+------------------------------------------------------------------+
input_group("🔸 Order Block Settings");
input double             OB_MinBodySizePips      = 10.0;                // Minimum OB body size in Pips
input int                OB_MaxAgeInBars         = 200;                 // Max validity of an OB in bars
input bool               OB_FilterByVolume       = true;                // Filter OBs by volume
input double             OB_MinVolumePercent     = 150.0;               // Minimum volume as % of average (e.g., 150%)
input int                OB_VolumeAvgPeriod      = 20;                  // Period for moving average of volume

//+------------------------------------------------------------------+
//| 🔸 FAIR VALUE GAP (FVG) SETTINGS                                 |
//+------------------------------------------------------------------+
input_group("🔸 Fair Value Gap (FVG) Settings");
input int                FVG_MaxGapAge           = 100;                 // Max validity of an FVG in bars
input bool               FVG_ShowFilled          = true;                // Show FVGs that have been partially or fully filled

//+------------------------------------------------------------------+
//| 🕯️ CANDLE PATTERNS                                               |
//+------------------------------------------------------------------+
input_group("🕯️ Candle Patterns");
input bool               EnableCandlePatterns    = true;                // Enable/Disable detection of candle patterns

//+------------------------------------------------------------------+
//| 🔔 ALERT SETTINGS                                                |
//+------------------------------------------------------------------+
input_group("🔔 Alert Settings");
input bool               EnableAlerts            = true;                // Master switch for all alerts
input bool               AlertOnNewOB            = true;                // Alert on new Order Block
input bool               AlertOnNewFVG           = true;                // Alert on new FVG
input bool               AlertOnBOS              = true;                // Alert on Break of Structure
input bool               EnableMT5Notifications  = true;                // Enable push notifications to MT5 mobile app
input bool               EnableEmailAlerts       = false;               // Enable email alerts
// --- Telegram requires manual setup (see documentation) ---
input bool               EnableTelegramAlerts    = false;               // Enable Telegram alerts
input string             TelegramBotToken        = "YOUR_BOT_TOKEN";    // Your Telegram Bot Token
input string             TelegramChatID          = "YOUR_CHAT_ID";      // Your Telegram Chat ID

//+------------------------------------------------------------------+
//| 🎨 VISUALIZATION                                                 |
//+------------------------------------------------------------------+
input_group("🎨 Visualization");
input color              Color_BullishOB         = clrDodgerBlue;
input color              Color_BearishOB         = clrTomato;
input color              Color_BullishFVG        = C'243,156,18';        // Orange
input color              Color_BearishFVG        = C'142,68,173';        // Violet
input color              Color_BOS_Line          = clrLimeGreen;
input color              Color_CHoCH_Line        = clrOrange;
input color              Color_DemandZone        = clrSeaGreen;
input color              Color_SupplyZone        = clrIndianRed;
input uchar              ZoneOpacity             = 30;                  // Opacity for filled zones (0-255)
input bool               EnableAutoFibonacci     = false;               // Auto Fibonacci on Zones
input bool               EnableDashboard         = true;                // Show/Hide the MTF Dashboard
