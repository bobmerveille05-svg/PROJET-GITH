//+------------------------------------------------------------------+
//| SMC Indicator.mq5                                                |
//| Copyright 2025, Custom Indicator                           |
//|                                                                  |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, Custom Indicator"
#property link      ""
#property version   "2.00" // Final Version
#property description "Indicator to display Order Blocks, FVG, Liquidity, and other SMC concepts with MTF and JSON export."

#property indicator_chart_window
#property indicator_buffers 0
#property indicator_plots   0

//--- input parameters
input int consolidationBars = 7;
input double maxconsolidationSpread = 50;
input int barstowaitafterbreakout = 3;
input double impulseMultiplier = 1.0;
input color bullishOrderBlockColor = clrGreen;
input color bearishOrderBlockColor = clrRed;
input color mitigatedOrderBlockColor = clrGray;
input color labelTextColor = clrBlack;

// --- Fibonacci Settings ---
input bool  enableFibonacci = true;
input int   fiboLookbackPeriod = 100;
input color fiboColor = clrGoldenrod;

// --- FVG/IMB Settings ---
input bool  enableFVG = true;
input int   fvgLookback = 200;
input color bullishFVGColor = clrAqua;
input color bearishFVGColor = clrMagenta;
input color mitigatedFVGColor = clrDarkGray;

// --- Liquidity Settings ---
input bool  enableLiquidity = true;
input int   liquidityLookback = 500;
input int   swingPeriod = 5;
input color buysideColor = clrDodgerBlue;
input color sellsideColor = clrSaddleBrown;
input color takenLiquidityColor = clrGray;

// --- Inducement (IDM) Settings ---
input bool  enableInducement = true;
input int   inducementSwingPeriod = 3;
input color inducementColor = clrGold;
input color takenInducementColor = clrDarkSlateGray;

// --- Multi-Timeframe (MTF) Settings ---
input string mtfTimeframes = "M15,H1"; // Comma-separated timeframes to scan

// --- JSON Export Settings ---
input bool  enableJsonExport = true;
input string jsonFilename = "smc_data.json";
input int   jsonUpdateInterval = 5; // Seconds

// --- Global Variables for MTF ---
ENUM_TIMEFRAMES timeframesToScan[];

// --- Data Structures for JSON Export ---
struct Coordinates {
    datetime start_time;
    datetime end_time;
    double   top_price;
    double   bottom_price;
};
struct DataObject {
    string   type;
    string   direction;
    string   status;
    string   timeframe;
    Coordinates coordinates;
    color    color_val;
    string   label;
    string   additional_info;
    string   chart_object_name;
    string   chart_label_name;
};
DataObject AllObjects[];

// --- Global Variables for OB Detection ---
struct PriceAndIndex{ double price; int index; };
PriceAndIndex rangeHighestHigh = {0,0};
PriceAndIndex rangeLowestLow = {0,0};
bool isBreakoutDetected = false;
double lastImpulseLow = 0.0;
double lastImpulseHigh = 0.0;
int breakoutBarNumber = -1;
datetime breakoutTimestamp = 0;
bool isBullishImpulse = false;
bool isBearishImpulse = false;
#define OB_Prefix "OB_REC "

//+------------------------------------------------------------------+
//| String to Timeframe Conversion                                   |
//+------------------------------------------------------------------+
ENUM_TIMEFRAMES StringToTimeframe(string tfStr) {
    StringUpper(tfStr);
    if(tfStr=="M1") return(PERIOD_M1); if(tfStr=="M5") return(PERIOD_M5); if(tfStr=="M15") return(PERIOD_M15);
    if(tfStr=="M30") return(PERIOD_M30); if(tfStr=="H1") return(PERIOD_H1); if(tfStr=="H4") return(PERIOD_H4);
    if(tfStr=="D1") return(PERIOD_D1); if(tfStr=="W1") return(PERIOD_W1); if(tfStr=="MN1") return(PERIOD_MN1);
    return(WRONG_VALUE);
}

//+------------------------------------------------------------------+
//| Initialization function                                          |
//+------------------------------------------------------------------+
int OnInit(){
    string tf_parts[];
    ushort separator = ',';
    StringSplit(mtfTimeframes, separator, tf_parts);
    int count = 0;
    ArrayResize(timeframesToScan, ArraySize(tf_parts) + 1);
    for(int i = 0; i < ArraySize(tf_parts); i++) {
        ENUM_TIMEFRAMES tf = StringToTimeframe(tf_parts[i]);
        if(tf != WRONG_VALUE) {
            bool found = false;
            for(int j=0; j<count; j++) if(timeframesToScan[j] == tf) { found = true; break; }
            if(!found) { timeframesToScan[count] = tf; count++; }
        }
    }
    bool found = false;
    for(int j=0; j<count; j++) if(timeframesToScan[j] == _Period) { found = true; break; }
    if(!found) { timeframesToScan[count] = _Period; count++; }
    ArrayResize(timeframesToScan, count);
    return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Deinitialization function                                        |
//+------------------------------------------------------------------+
void OnDeinit(const int reason) {
    for (int i = ArraySize(AllObjects) - 1; i >= 0; i--) {
        ObjectDelete(0, AllObjects[i].chart_object_name);
        ObjectDelete(0, AllObjects[i].chart_label_name);
    }
    ArrayFree(AllObjects);
}

//+------------------------------------------------------------------+
//| Master Analysis Function per Timeframe                           |
//+------------------------------------------------------------------+
void RunAllAnalysis(ENUM_TIMEFRAMES tf) {
    HandleOrderBlocks(tf);
    if(enableFibonacci) HandleFibonacci(tf);
    if(enableFVG) HandleFVG(tf);
    if(enableLiquidity) HandleLiquidity(tf);
    if(enableInducement) HandleInducement(tf);
}

//+------------------------------------------------------------------+
//| Main indicator iteration function                                |
//+------------------------------------------------------------------+
int OnCalculate(const int rates_total, const int prev_calculated, const datetime &time[], const double &open[], const double &high[], const double &low[], const double &close[], const long &tick_volume[], const long &volume[], const int &spread[]){
    static int bars = 0;
    if(bars == rates_total) return(rates_total);
    bars = rates_total;

    for(int i = 0; i < ArraySize(timeframesToScan); i++) {
        RunAllAnalysis(timeframesToScan[i]);
    }

    for (int j = ArraySize(AllObjects) - 1; j >= 0; j--) {
        DataObject &currentObject = AllObjects[j];
        if (currentObject.coordinates.end_time != 0 && iTime(_Symbol, _Period, 0) >= currentObject.coordinates.end_time) {
            RemoveObjectByIndex(j);
            continue;
        }
        if (currentObject.type == "OrderBlock" && currentObject.status == "active") {
            double currentClose = iClose(_Symbol, _Period, 1);
            if ((currentObject.direction == "bullish" && currentClose < currentObject.coordinates.bottom_price) || (currentObject.direction == "bearish" && currentClose > currentObject.coordinates.top_price)) {
                currentObject.status = "mitigated";
                ObjectSetInteger(0, currentObject.chart_object_name, OBJPROP_COLOR, mitigatedOrderBlockColor);
                ObjectSetString(0, currentObject.chart_label_name, OBJPROP_TEXT, "Mitigated " + currentObject.label);
                ChartRedraw(0);
            }
        }
        if (currentObject.type == "FVG" && currentObject.status == "active") {
            if ((currentObject.direction == "bullish" && iLow(_Symbol, _Period, 1) <= currentObject.coordinates.top_price) || (currentObject.direction == "bearish" && iHigh(_Symbol, _Period, 1) >= currentObject.coordinates.bottom_price)) {
                currentObject.status = "mitigated";
                ObjectSetInteger(0, currentObject.chart_object_name, OBJPROP_COLOR, mitigatedFVGColor);
                ObjectSetString(0, currentObject.chart_object_name, OBJPROP_TOOLTIP, "Mitigated");
                ChartRedraw(0);
            }
        }
        if (currentObject.type == "Liquidity" && currentObject.status == "active") {
            if ((currentObject.direction == "buyside" && iHigh(_Symbol, _Period, 1) > currentObject.coordinates.top_price) || (currentObject.direction == "sellside" && iLow(_Symbol, _Period, 1) < currentObject.coordinates.bottom_price)) {
                currentObject.status = "mitigated";
                ObjectSetInteger(0, currentObject.chart_object_name, OBJPROP_COLOR, takenLiquidityColor);
                ObjectSetString(0, currentObject.chart_object_name, OBJPROP_TEXT, "x");
                ChartRedraw(0);
            }
        }
        if (currentObject.type == "Inducement" && currentObject.status == "active") {
            if ((currentObject.direction == "buyside" && iHigh(_Symbol, _Period, 1) > currentObject.coordinates.top_price) || (currentObject.direction == "sellside" && iLow(_Symbol, _Period, 1) < currentObject.coordinates.bottom_price)) {
                currentObject.status = "mitigated";
                ObjectSetInteger(0, currentObject.chart_object_name, OBJPROP_COLOR, takenInducementColor);
                ObjectSetString(0, currentObject.chart_object_name, OBJPROP_TEXT, "IDM x");
                ChartRedraw(0);
            }
        }
    }
    WriteJsonToFile();
    return(rates_total);
}

//+------------------------------------------------------------------+
//| Helper to check if object exists in data array                   |
//+------------------------------------------------------------------+
bool ObjectExistsInData(string name) {
    for (int i = 0; i < ArraySize(AllObjects); i++) {
        if (AllObjects[i].chart_object_name == name) return true;
    }
    return false;
}

//+------------------------------------------------------------------+
//| Helper to remove an object from the array and chart              |
//+------------------------------------------------------------------+
void RemoveObjectByIndex(int index) {
    if (index < 0 || index >= ArraySize(AllObjects)) return;
    ObjectDelete(0, AllObjects[index].chart_object_name);
    ObjectDelete(0, AllObjects[index].chart_label_name);
    for (int i = index; i < ArraySize(AllObjects) - 1; i++) {
        AllObjects[i] = AllObjects[i+1];
    }
    ArrayResize(AllObjects, ArraySize(AllObjects) - 1);
}

// --- Analysis and Drawing Functions ---

void HandleOrderBlocks(ENUM_TIMEFRAMES tf) {
    if(tf != _Period) return;
    int startBarIndex = 1;
    if(!isBreakoutDetected){
        if(rangeHighestHigh.price == 0 && rangeLowestLow.price == 0){
            bool isConsolidated = true;
            for(int i=startBarIndex; i<startBarIndex+consolidationBars-1; i++){
                if(MathAbs(iHigh(_Symbol, tf, i) - iHigh(_Symbol, tf, i+1)) > maxconsolidationSpread * _Point || MathAbs(iLow(_Symbol, tf, i) - iLow(_Symbol, tf, i+1)) > maxconsolidationSpread * _Point) {
                    isConsolidated = false; break;
                }
            }
            if(isConsolidated){
                rangeHighestHigh.price = iHigh(_Symbol, tf, startBarIndex);
                rangeLowestLow.price = iLow(_Symbol, tf, startBarIndex);
                for(int i=startBarIndex+1; i<startBarIndex+consolidationBars; i++){
                    if(iHigh(_Symbol, tf, i) > rangeHighestHigh.price) rangeHighestHigh.price = iHigh(_Symbol, tf, i);
                    if(iLow(_Symbol, tf, i) < rangeLowestLow.price) rangeLowestLow.price = iLow(_Symbol, tf, i);
                }
            }
        }
    }
    if(rangeHighestHigh.price > 0 && rangeLowestLow.price > 0 && (iClose(_Symbol, tf, 1) > rangeHighestHigh.price || iClose(_Symbol, tf, 1) < rangeLowestLow.price)) isBreakoutDetected = true;
    if(isBreakoutDetected){
        breakoutBarNumber = 1;
        breakoutTimestamp = iTime(_Symbol, tf, 0);
        lastImpulseHigh = rangeHighestHigh.price;
        lastImpulseLow = rangeLowestLow.price;
        isBreakoutDetected = false;
        rangeHighestHigh.price = 0; rangeLowestLow.price = 0;
    }
    if(breakoutBarNumber >= 0 && iTime(_Symbol, tf, 0) > breakoutTimestamp+barstowaitafterbreakout*PeriodSeconds(tf)){
        double impulseRange = lastImpulseHigh - lastImpulseLow;
        double impulseThresholdPrice = impulseRange * impulseMultiplier;
        isBullishImpulse = false; isBearishImpulse = false;
        for(int i=1; i<=barstowaitafterbreakout; i++){
            double closePrice = iClose(_Symbol, tf, i);
            if(closePrice >= lastImpulseHigh+impulseThresholdPrice) { isBullishImpulse = true; break; }
            if(closePrice <= lastImpulseLow-impulseThresholdPrice) { isBearishImpulse = true; break; }
        }
        if(isBullishImpulse || isBearishImpulse){
            datetime blockStartTime = iTime(_Symbol,tf,consolidationBars+barstowaitafterbreakout+1);
            string tf_str = PeriodToString(tf);
            string name = tf_str + "_" + OB_Prefix+"("+TimeToString(blockStartTime)+")";
            if(!ObjectExistsInData(name)){
                DataObject ob;
                ob.type = "OrderBlock";
                ob.direction = isBullishImpulse ? "bullish" : "bearish";
                ob.status = "active";
                ob.timeframe = tf_str;
                ob.coordinates.start_time = blockStartTime;
                ob.coordinates.end_time = blockStartTime+(int)ChartGetInteger(0,CHART_VISIBLE_BARS)*PeriodSeconds(tf);
                ob.coordinates.top_price = lastImpulseHigh;
                ob.coordinates.bottom_price = lastImpulseLow;
                ob.color_val = isBullishImpulse ? bullishOrderBlockColor : bearishOrderBlockColor;
                ob.label = tf_str + " " + (isBullishImpulse ? "Bullish OB" : "Bearish OB");
                ob.chart_object_name = name;
                ob.chart_label_name = name + "_label";
                ObjectCreate(0,ob.chart_object_name,OBJ_RECTANGLE,0,ob.coordinates.start_time,ob.coordinates.top_price,ob.coordinates.end_time,ob.coordinates.bottom_price);
                ObjectSetInteger(0,ob.chart_object_name,OBJPROP_COLOR,ob.color_val);
                ObjectSetInteger(0,ob.chart_object_name,OBJPROP_FILL,true);
                ObjectCreate(0,ob.chart_label_name,OBJ_TEXT,0,ob.coordinates.start_time, (ob.coordinates.top_price+ob.coordinates.bottom_price)/2);
                ObjectSetString(0,ob.chart_label_name,OBJPROP_TEXT,ob.label);
                ObjectSetInteger(0,ob.chart_label_name,OBJPROP_COLOR,labelTextColor);
                ObjectSetInteger(0,ob.chart_label_name,OBJPROP_ANCHOR,ANCHOR_LEFT);
                int new_size = ArraySize(AllObjects) + 1;
                ArrayResize(AllObjects, new_size);
                AllObjects[new_size - 1] = ob;
            }
        }
        breakoutBarNumber = -1;
    }
}

void HandleFibonacci(ENUM_TIMEFRAMES tf) {
    if(fiboLookbackPeriod <= 1) return;
    int high_idx = iHighest(_Symbol, tf, MODE_HIGH, fiboLookbackPeriod, 1);
    int low_idx = iLowest(_Symbol, tf, MODE_LOW, fiboLookbackPeriod, 1);
    string tf_str = PeriodToString(tf);
    string name = tf_str + "_Fibo_" + (string)iTime(_Symbol, tf, high_idx) + "_" + (string)iTime(_Symbol, tf, low_idx);
    if(ObjectExistsInData(name)) return;
    for (int i = ArraySize(AllObjects) - 1; i >= 0; i--) if (AllObjects[i].type == "Fibonacci" && AllObjects[i].timeframe == tf_str) RemoveObjectByIndex(i);
    DataObject fibo;
    fibo.type = "Fibonacci";
    fibo.direction = (iTime(_Symbol, tf, high_idx) < iTime(_Symbol, tf, low_idx)) ? "bearish" : "bullish";
    fibo.status = "active";
    fibo.timeframe = tf_str;
    fibo.coordinates.start_time = (fibo.direction == "bearish") ? iTime(_Symbol, tf, high_idx) : iTime(_Symbol, tf, low_idx);
    fibo.coordinates.end_time = (fibo.direction == "bearish") ? iTime(_Symbol, tf, low_idx) : iTime(_Symbol, tf, high_idx);
    fibo.coordinates.top_price = iHigh(_Symbol, tf, high_idx);
    fibo.coordinates.bottom_price = iLow(_Symbol, tf, low_idx);
    fibo.color_val = fiboColor;
    fibo.label = tf_str + " Fibo";
    fibo.chart_object_name = name;
    if (ObjectCreate(0, name, OBJ_FIBO, 0, fibo.coordinates.start_time, (fibo.direction == "bearish" ? fibo.coordinates.top_price : fibo.coordinates.bottom_price), fibo.coordinates.end_time, (fibo.direction == "bearish" ? fibo.coordinates.bottom_price : fibo.coordinates.top_price))) {
        ObjectSetInteger(0, name, OBJPROP_COLOR, fibo.color_val);
        int new_size = ArraySize(AllObjects) + 1;
        ArrayResize(AllObjects, new_size);
        AllObjects[new_size - 1] = fibo;
    }
}

void HandleFVG(ENUM_TIMEFRAMES tf) {
    int rates_total_tf = iBars(_Symbol, tf);
    for (int i = 1; i <= fvgLookback && i + 2 < rates_total_tf; i++) {
        string name;
        string tf_str = PeriodToString(tf);
        if (iLow(_Symbol, tf, i) > iHigh(_Symbol, tf, i + 2)) {
            name = tf_str + "_FVG_Bull_" + (string)iTime(_Symbol, tf, i + 1);
            if (!ObjectExistsInData(name)) DrawFVG(name, "bullish", iHigh(_Symbol, tf, i + 2), iLow(_Symbol, tf, i), iTime(_Symbol, tf, i + 1), tf);
        }
        if (iHigh(_Symbol, tf, i) < iLow(_Symbol, tf, i + 2)) {
            name = tf_str + "_FVG_Bear_" + (string)iTime(_Symbol, tf, i + 1);
            if (!ObjectExistsInData(name)) DrawFVG(name, "bearish", iLow(_Symbol, tf, i + 2), iHigh(_Symbol, tf, i), iTime(_Symbol, tf, i + 1), tf);
        }
    }
}
void DrawFVG(string name, string dir, double p1, double p2, datetime time_val, ENUM_TIMEFRAMES tf) {
    DataObject fvg;
    fvg.type = "FVG"; fvg.direction = dir; fvg.status = "active"; fvg.timeframe = PeriodToString(tf);
    fvg.coordinates.start_time = time_val; fvg.coordinates.end_time = time_val + (int)ChartGetInteger(0, CHART_VISIBLE_BARS) * PeriodSeconds(tf);
    fvg.coordinates.top_price = MathMax(p1,p2); fvg.coordinates.bottom_price = MathMin(p1,p2);
    fvg.color_val = (dir == "bullish") ? bullishFVGColor : bearishFVGColor;
    fvg.label = fvg.timeframe + " " + (dir == "bullish" ? "+FVG" : "-FVG");
    fvg.chart_object_name = name;
    if(ObjectCreate(0, name, OBJ_RECTANGLE, 0, fvg.coordinates.start_time, fvg.coordinates.top_price, fvg.coordinates.end_time, fvg.coordinates.bottom_price)) {
        ObjectSetInteger(0, name, OBJPROP_COLOR, fvg.color_val); ObjectSetInteger(0, name, OBJPROP_STYLE, STYLE_DOT); ObjectSetInteger(0, name, OBJPROP_FILL, true); ObjectSetInteger(0, name, OBJPROP_BACK, true);
        int new_size = ArraySize(AllObjects) + 1; ArrayResize(AllObjects, new_size); AllObjects[new_size - 1] = fvg;
    }
}

void HandleLiquidity(ENUM_TIMEFRAMES tf) {
    if (swingPeriod <= 0) return;
    int rates_total_tf = iBars(_Symbol, tf);
    for (int i = swingPeriod; i < liquidityLookback && i + swingPeriod < rates_total_tf; i++) {
        string tf_str = PeriodToString(tf);
        if (iHigh(_Symbol, tf, i) == iHigh(_Symbol, tf, iHighest(_Symbol, tf, MODE_HIGH, swingPeriod * 2 + 1, i - swingPeriod))) {
            string name = tf_str + "_Liq_Buy_" + (string)iTime(_Symbol, tf, i);
            if (!ObjectExistsInData(name)) DrawLiquidity(name, "buyside", iHigh(_Symbol, tf, i), iTime(_Symbol, tf, i), tf);
        }
        if (iLow(_Symbol, tf, i) == iLow(_Symbol, tf, iLowest(_Symbol, tf, MODE_LOW, swingPeriod * 2 + 1, i - swingPeriod))) {
            string name = tf_str + "_Liq_Sell_" + (string)iTime(_Symbol, tf, i);
            if (!ObjectExistsInData(name)) DrawLiquidity(name, "sellside", iLow(_Symbol, tf, i), iTime(_Symbol, tf, i), tf);
        }
    }
}
void DrawLiquidity(string name, string dir, double price, datetime time_val, ENUM_TIMEFRAMES tf) {
    DataObject liq;
    liq.type = "Liquidity"; liq.direction = dir; liq.status = "active"; liq.timeframe = PeriodToString(tf);
    liq.coordinates.start_time = time_val; liq.coordinates.top_price = price; liq.coordinates.bottom_price = price;
    liq.color_val = (dir == "buyside") ? buysideColor : sellsideColor;
    liq.label = liq.timeframe + " $";
    liq.chart_object_name = name;
    double label_price = (dir == "buyside") ? price + SymbolInfoInteger(_Symbol, SYMBOL_SPREAD)*_Point*5 : price - SymbolInfoInteger(_Symbol, SYMBOL_SPREAD)*_Point*5;
    if(ObjectCreate(0, name, OBJ_TEXT, 0, time_val, label_price)) {
        ObjectSetString(0, name, OBJPROP_TEXT, liq.label); ObjectSetInteger(0, name, OBJPROP_COLOR, liq.color_val); ObjectSetInteger(0, name, OBJPROP_FONTSIZE, 8);
        ObjectSetInteger(0, name, OBJPROP_ANCHOR, (dir == "buyside") ? ANCHOR_LOWER : ANCHOR_UPPER);
        int new_size = ArraySize(AllObjects) + 1; ArrayResize(AllObjects, new_size); AllObjects[new_size - 1] = liq;
    }
}

void HandleInducement(ENUM_TIMEFRAMES tf) {
    if (inducementSwingPeriod <= 0) return;
    int rates_total_tf = iBars(_Symbol, tf);
    int high_idx = -1, low_idx = -1;
    for (int i = inducementSwingPeriod; i < 150 && i + inducementSwingPeriod < rates_total_tf; i++) {
        if (high_idx == -1 && iHigh(_Symbol, tf, i) == iHigh(_Symbol, tf, iHighest(_Symbol, tf, MODE_HIGH, inducementSwingPeriod * 2 + 1, i - inducementSwingPeriod))) high_idx = i;
        if (low_idx == -1 && iLow(_Symbol, tf, i) == iLow(_Symbol, tf, iLowest(_Symbol, tf, MODE_LOW, inducementSwingPeriod * 2 + 1, i - inducementSwingPeriod))) low_idx = i;
        if (high_idx != -1 && low_idx != -1) break;
    }
    string tf_str = PeriodToString(tf);
    string high_name = (high_idx != -1) ? tf_str + "_IDM_Buy_" + (string)iTime(_Symbol, tf, high_idx) : "";
    string low_name = (low_idx != -1) ? tf_str + "_IDM_Sell_" + (string)iTime(_Symbol, tf, low_idx) : "";
    for (int i = ArraySize(AllObjects) - 1; i >= 0; i--) if (AllObjects[i].type == "Inducement" && AllObjects[i].timeframe == tf_str && AllObjects[i].chart_object_name != high_name && AllObjects[i].chart_object_name != low_name) RemoveObjectByIndex(i);
    if (high_idx != -1 && !ObjectExistsInData(high_name)) DrawInducement(high_name, "buyside", iHigh(_Symbol, tf, high_idx), iTime(_Symbol, tf, high_idx), tf);
    if (low_idx != -1 && !ObjectExistsInData(low_name)) DrawInducement(low_name, "sellside", iLow(_Symbol, tf, low_idx), iTime(_Symbol, tf, low_idx), tf);
}
void DrawInducement(string name, string dir, double price, datetime time_val, ENUM_TIMEFRAMES tf) {
    DataObject idm;
    idm.type = "Inducement"; idm.direction = dir; idm.status = "active"; idm.timeframe = PeriodToString(tf);
    idm.coordinates.start_time = time_val; idm.coordinates.top_price = price; idm.coordinates.bottom_price = price;
    idm.color_val = inducementColor;
    idm.label = idm.timeframe + " IDM";
    idm.chart_object_name = name;
    double label_price = (dir == "buyside") ? price + SymbolInfoInteger(_Symbol, SYMBOL_SPREAD)*_Point*5 : price - SymbolInfoInteger(_Symbol, SYMBOL_SPREAD)*_Point*5;
    if(ObjectCreate(0, name, OBJ_TEXT, 0, time_val, label_price)) {
        ObjectSetString(0, name, OBJPROP_TEXT, idm.label); ObjectSetInteger(0, name, OBJPROP_COLOR, idm.color_val); ObjectSetInteger(0, name, OBJPROP_FONTSIZE, 9);
        ObjectSetInteger(0, name, OBJPROP_ANCHOR, (dir == "buyside") ? ANCHOR_LOWER : ANCHOR_UPPER);
        int new_size = ArraySize(AllObjects) + 1; ArrayResize(AllObjects, new_size); AllObjects[new_size - 1] = idm;
    }
}

//+------------------------------------------------------------------+
//| JSON Conversion and Export                                       |
//+------------------------------------------------------------------+
string ConvertAllObjectsToJson() {
    string json = "{\n  \"objects\": [\n";
    int array_size = ArraySize(AllObjects);
    for (int i = 0; i < array_size; i++) {
        DataObject obj = AllObjects[i];
        json += "    {\n";
        json += "      \"type\": \"" + obj.type + "\",\n";
        json += "      \"direction\": \"" + obj.direction + "\",\n";
        json += "      \"status\": \"" + obj.status + "\",\n";
        json += "      \"timeframe\": \"" + obj.timeframe + "\",\n";
        json += "      \"coordinates\": {\"start_time\": " + (string)obj.coordinates.start_time + ", \"end_time\": " + (string)obj.coordinates.end_time + ", \"top_price\": " + DoubleToString(obj.coordinates.top_price, _Digits) + ", \"bottom_price\": " + DoubleToString(obj.coordinates.bottom_price, _Digits) + "},\n";
        string color_str;
        ColorToString(obj.color_val, color_str);
        json += "      \"color\": \"#" + color_str + "\",\n";
        json += "      \"label\": \"" + StringSubstr(obj.label, 0, 100) + "\",\n";
        json += "      \"additional_info\": \"" + obj.additional_info + "\"\n";
        json += "    }";
        if (i < array_size - 1) json += ",\n";
    }
    json += "\n  ]\n}";
    return json;
}

void WriteJsonToFile() {
    if(!enableJsonExport) return;
    static datetime lastJsonWriteTime = 0;
    if(TimeCurrent() < lastJsonWriteTime + jsonUpdateInterval) return;
    lastJsonWriteTime = TimeCurrent();
    int file_handle = FileOpen(jsonFilename, FILE_WRITE|FILE_TXT|FILE_ANSI);
    if(file_handle != INVALID_HANDLE) {
        FileWrite(file_handle, ConvertAllObjectsToJson());
        FileClose(file_handle);
    } else {
        Print("Error writing to file " + jsonFilename + ", error code: ", GetLastError());
    }
}
//+------------------------------------------------------------------+
