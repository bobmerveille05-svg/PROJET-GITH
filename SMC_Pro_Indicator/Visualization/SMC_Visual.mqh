//+------------------------------------------------------------------+
//|                                SMC_Pro_Indicator/Visualization/SMC_Visual.mqh |
//|                      Copyright 2025, ProDev SMC Team             |
//|                                        https://yourdevsite.com |
//+------------------------------------------------------------------+
#include "../Core/Structures/SMC_Structs.mqh"
#include "../Config/SMC_Params.mqh"

class CSMC_Visual
{
private:
   string m_prefix; // Unique prefix for all objects created by this indicator instance

public:
   //+------------------------------------------------------------------+
   //| Constructor                                                      |
   //+------------------------------------------------------------------+
   void CSMC_Visual()
   {
      // Create a unique prefix based on chart ID and indicator short name
      m_prefix = "SMC_PRO_" + IntegerToString(ChartID()) + "_";
   }

   //+------------------------------------------------------------------+
   //| Clear all objects created by this indicator                      |
   //+------------------------------------------------------------------+
   void ClearOldObjects()
   {
      for(int i = ObjectsTotal(0, -1, -1) - 1; i >= 0; i--)
      {
         string name = ObjectName(0, i, -1, -1);
         if(StringFind(name, m_prefix) == 0)
         {
            ObjectDelete(0, name);
         }
      }
   }

   //+------------------------------------------------------------------+
   //| Draw Order Blocks                                                |
   //+------------------------------------------------------------------+
   void DrawOrderBlocks(CArrayObj *blocks)
   {
      if(CheckPointer(blocks) == POINTER_INVALID) return;
      int total = blocks.Total();
      int drawn_count = 0;

      for(int i = total - 1; i >= 0 && drawn_count < MaxZonesToShow; i--)
      {
         SMC_OrderBlock *ob = blocks.At(i);
         if(CheckPointer(ob) == POINTER_INVALID) continue;

         string objName = m_prefix + "OB_" + TimeToString(ob.time);
         datetime expiration_time = ob.time + (PeriodSeconds() * OB_MaxAgeInBars);

         ObjectCreate(0, objName, OBJ_RECTANGLE, 0, ob.time, ob.top_price, expiration_time, ob.bottom_price);
         ObjectSetInteger(0, objName, OBJPROP_COLOR, ob.type == BULLISH ? Color_BullishOB : Color_BearishOB);
         ObjectSetInteger(0, objName, OBJPROP_STYLE, STYLE_SOLID);
         ObjectSetInteger(0, objName, OBJPROP_WIDTH, 1);
         ObjectSetInteger(0, objName, OBJPROP_BACK, true);
         ObjectSetInteger(0, objName, OBJPROP_FILL, true);

         // Make mitigated zones more transparent
         uchar opacity = ob.is_mitigated ? ZoneOpacity / 2 : ZoneOpacity;
         color fill_color = ColorToARGB(ob.type == BULLISH ? Color_BullishOB : Color_BearishOB, 255 - opacity);
         ObjectSetInteger(0, objName, OBJPROP_BGCOLOR, fill_color);

         drawn_count++;
      }
   }

   //+------------------------------------------------------------------+
   //| Draw Fair Value Gaps                                             |
   //+------------------------------------------------------------------+
   void DrawFVGs(CArrayObj *fvgs)
   {
      if(CheckPointer(fvgs) == POINTER_INVALID) return;
      int total = fvgs.Total();
      int drawn_count = 0;

      for(int i = total - 1; i >= 0 && drawn_count < MaxZonesToShow; i--)
      {
         SMC_FVG *fvg = fvgs.At(i);
         if(CheckPointer(fvg) == POINTER_INVALID) continue;

         string objName = m_prefix + "FVG_" + TimeToString(fvg.time);
         datetime expiration_time = fvg.time + (PeriodSeconds() * FVG_MaxGapAge);

         ObjectCreate(0, objName, OBJ_RECTANGLE, 0, fvg.time, fvg.top_price, expiration_time, fvg.bottom_price);
         ObjectSetInteger(0, objName, OBJPROP_COLOR, fvg.type == BULLISH ? Color_BullishFVG : Color_BearishFVG);
         ObjectSetInteger(0, objName, OBJPROP_STYLE, STYLE_DOT);
         ObjectSetInteger(0, objName, OBJPROP_WIDTH, 1);
         ObjectSetInteger(0, objName, OBJPROP_BACK, true);

         if(FVG_ShowFilled || !fvg.is_filled)
         {
            ObjectSetInteger(0, objName, OBJPROP_FILL, true);
            uchar opacity = fvg.is_filled ? ZoneOpacity / 2 : ZoneOpacity;
            color fill_color = ColorToARGB(fvg.type == BULLISH ? Color_BullishFVG : Color_BearishFVG, 255 - opacity);
            ObjectSetInteger(0, objName, OBJPROP_BGCOLOR, fill_color);
         }
         drawn_count++;
      }
   }

   //+------------------------------------------------------------------+
   //| Draw Market Structures                                           |
   //+------------------------------------------------------------------+
   void DrawStructures(CArrayObj *structures)
   {
      if(CheckPointer(structures) == POINTER_INVALID) return;
      int total = structures.Total();

      for(int i = 0; i < total; i++)
      {
         SMC_Structure *struc = structures.At(i);
         if(CheckPointer(struc) == POINTER_INVALID) continue;

         string lineName = m_prefix + (struc.type == BOS ? "BOS_" : "CHoCH_") + TimeToString(struc.time);
         string labelName = m_prefix + "Label_" + (struc.type == BOS ? "BOS_" : "CHoCH_") + TimeToString(struc.time);
         color line_color = struc.type == BOS ? Color_BOS_Line : Color_CHoCH_Line;

         // Draw horizontal line
         ObjectCreate(0, lineName, OBJ_HLINE, 0, 0, struc.price_level);
         ObjectSetInteger(0, lineName, OBJPROP_COLOR, line_color);
         ObjectSetInteger(0, lineName, OBJPROP_STYLE, STYLE_DASH);
         ObjectSetInteger(0, lineName, OBJPROP_WIDTH, 1);

         // Draw label
         ObjectCreate(0, labelName, OBJ_TEXT, 0, struc.time, struc.price_level);
         ObjectSetString(0, labelName, OBJPROP_TEXT, struc.type == BOS ? "BOS" : "CHoCH");
         ObjectSetInteger(0, labelName, OBJPROP_COLOR, line_color);
         ObjectSetInteger(0, labelName, OBJPROP_ANCHOR, ANCHOR_LEFT);
         ObjectSetInteger(0, labelName, OBJPROP_FONTSIZE, 8);
      }
   }
};
