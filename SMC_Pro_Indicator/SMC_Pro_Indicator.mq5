//+------------------------------------------------------------------+
//|                                        SMC_Pro_Indicator.mq5 |
//|                      Copyright 2025, ProDev SMC Team             |
//|                                        https://yourdevsite.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, ProDev SMC Team"
#property link      "https://yourdevsite.com"
#property version   "1.0"
#property strict
#property indicator_chart_window
#property indicator_buffers 0
#property indicator_plots   0

// --- Main Modules ---
#include "Config/SMC_Params.mqh"
#include "Core/SMC_Core.mqh"
#include "Visualization/SMC_Visual.mqh"
#include "Alerts/SMC_Alerts.mqh"
#include "Dashboard/MTF_Dashboard.mqh"

// --- Global Module Instances ---
CSMC_Core       smcCore;
CSMC_Visual     smcVisual;
CSMC_Alerts     smcAlerts;
CMTF_Dashboard  dashboard;

//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("✅ SMC Pro Indicator v1.0 Initialized.");
   Print("Chart: ", ChartSymbol(), ", Timeframe: ", PeriodToString(_Period));
   Print("Author: ProDev SMC Team");

   // Set a unique prefix for visual objects based on the chart ID
   // This is handled in the CSMC_Visual constructor now.

   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Custom indicator deinitialization function                       |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   // --- Clean up all graphical objects ---
   smcVisual.ClearOldObjects();
   dashboard.ClearDashboard();

   Print("⛔ SMC Pro Indicator Deinitialized. Reason: ", reason);
}

//+------------------------------------------------------------------+
//| Custom indicator iteration function                              |
//+------------------------------------------------------------------+
int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &time[],
                const double &open[],
                const double &high[],
                const double &low[],
                const double &close[],
                const long &tick_volume[],
                const long &volume[],
                const int &spread[])
{
   // --- Wait for enough bars to be loaded ---
   int lookback = MathMax(StructureLookback, MathMax(OB_MaxAgeInBars, FVG_MaxGapAge));
   if(rates_total < lookback)
   {
      Alert("Not enough bars on chart for calculation. Required: ", lookback);
      return(0);
   }

   // --- Main Calculation Block ---

   // 1. Update data in the core module
   smcCore.UpdateData(open, high, low, close, time, volume, rates_total);

   // 2. Clear previously detected structures before new analysis
   smcCore.ClearAll();

   // 3. Run detection algorithms
   smcCore.DetectOrderBlocks(OB_MaxAgeInBars, OB_MinBodySizePips);
   smcCore.DetectFVGs(FVG_MaxGapAge);
   smcCore.DetectStructures(StructureLookback);
   // Add other detections here...

   // 4. Clear old graphical objects from the chart
   smcVisual.ClearOldObjects();

   // 5. Draw the newly detected structures
   smcVisual.DrawOrderBlocks(smcCore.GetOrderBlocks());
   smcVisual.DrawFVGs(smcCore.GetFVGs());
   smcVisual.DrawStructures(smcCore.GetStructures());
   // Add other drawing calls here...

   // 6. Draw or update the dashboard
   dashboard.DrawDashboard();

   // 7. Check for alerts on the latest data
   // Run this only on new bar to avoid spamming on every tick
   if(prev_calculated < rates_total)
   {
      smcAlerts.CheckAlerts(smcCore.GetOrderBlocks(), smcCore.GetFVGs(), smcCore.GetStructures());
   }

   // --- Return value of prev_calculated for next call ---
   return(rates_total);
}
//+------------------------------------------------------------------+
