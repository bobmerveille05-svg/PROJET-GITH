//+------------------------------------------------------------------+
//|                                     Boa_ZigZag_Arrows_Duplex.mq5 |
//|                        Copyright © 2005, MetaQuotes Software Corp. |
//|                                              mandorr@gmail.com |
//+------------------------------------------------------------------+
//---- авторство индикатора
#property copyright "Copyright © 2005, MetaQuotes Software Corp."
//---- ссылка на сайт автора
#property link      "mandorr@gmail.com"
//---- номер версии индикатора
#property version   "2.00 PRO"
#property description "Дв разнопериодных казахских удава + MTF, Alerts, Reversal Zones, Hooks"
//---- отрисовка индикатора в основном окне
#property indicator_chart_window
//---- количество индикаторных буферов 8 (4 originaux + 4 backup pour détection alertes)
#property indicator_buffers 8
//---- использовано всего четыре графических построения (les 4 originaux)
#property indicator_plots   4

//+----------------------------------------------+
//| Параметры отрисовки индикатора               |
//+----------------------------------------------+
//---- отрисовка индикатора в виде значка
#property indicator_type1   DRAW_ARROW
//---- в качестве окраски индикатора использован
#property indicator_color1  clrDodgerBlue
//---- толщина линии индикатора равна 5
#property indicator_width1  5
//---- отображение метки сигнальной линии
#property indicator_label1  "Slow Boa_ZigZag Dn"

//+----------------------------------------------+
//| Параметры отрисовки индикатора               |
//+----------------------------------------------+
//---- отрисовка индикатора в виде значка
#property indicator_type2   DRAW_ARROW
//---- в качестве окраски индикатора использован
#property indicator_color2  clrDeepPink
//---- толщина линии индикатора равна 5
#property indicator_width2  5
//---- отображение метки сигнальной линии
#property indicator_label2  "Slow Boa_ZigZag Up"

//+----------------------------------------------+
//| Параметры отрисовки бычьего индикатора       |
//+----------------------------------------------+
//---- отрисовка индикатора 3 в виде значка
#property indicator_type3   DRAW_ARROW
//---- в качестве цвета бычей линии индикатора использован
#property indicator_color3  clrAqua
//---- толщина линии индикатора 3 равна 5
#property indicator_width3  5
//---- отображение бычьей метки индикатора
#property indicator_label3  "Fast Boa_ZigZag Dn"

//+----------------------------------------------+
//| Параметры отрисовки медвежьего индикатора    |
//+----------------------------------------------+
//---- отрисовка индикатора 4 в виде значка
#property indicator_type4   DRAW_ARROW
//---- в качестве цвета медвежьей линии индикатора использован
#property indicator_color4  clrOrange
//---- толщина линии индикатора 2 равна 5
#property indicator_width4  5
//---- отображение медвежьей метки индикатора
#property indicator_label4  "Fast Boa_ZigZag Up"

//==== INPUTS GROUPÉS ET COMMENTÉS PAR USAGE ====

//---- входные параметры оригинальные
input uint SlowLength=42; // период медленного зигзага
input uint FastLength=6;  // период быстрого зигзага

//---- входные параметры MTF (Multitimeframe)
input bool EnableMTF = true;                              // Activer la gestion multitemporelle
input ENUM_TIMEFRAMES MTF_TF1 = PERIOD_H1;                 // Premier timeframe additionnel
input ENUM_TIMEFRAMES MTF_TF2 = PERIOD_M15;                // Deuxième timeframe additionnel
input bool MTF_SyncOnCurrent = true;                       // Synchroniser les signaux MTF sur le timeframe courant
input int MTF_MaxLookback = 10;                            // Nombre max de barres à analyser en MTF

//---- входные параметры Alertes
input bool EnableVisualAlerts = true;  // Activer les alertes visuelles (flèches/bulles)
input bool EnableSoundAlerts = true;   // Activer les alertes sonores (Alert())
input bool EnablePushAlerts = true;    // Activer les notifications push (mobile)
input bool EnableEmailAlerts = false;  // Activer les notifications email
input string EmailSubject = "ZigZag Signal"; // Sujet de l'email
input string EmailTo = "";             // Adresse email destinataire (laisser vide pour compte MT5)

//---- входные параметры Zones de Reversal
input bool EnableReversalZones = true;      // Activer les zones de forte probabilité de reversal
input int ReversalZoneLookback = 5;         // Nombre de points de reversal à considérer
input color ReversalZoneColor = clrYellow;  // Couleur de la zone
input int ReversalZoneAlpha = 80;           // Transparence (0-255)
input int ReversalZoneMinutes = 60;         // Durée d'affichage en minutes

//---- entrées techniques internes (ne pas modifier)
int min_rates_total;
string IndicatorShortName;

//==== BUFFERS DÉCLARÉS ====
//---- buffers originaux (affichés)
double ZigzagLawnBuffer1[],ZigzagPeakBuffer1[];
double ZigzagLawnBuffer2[],ZigzagPeakBuffer2[];
//---- buffers backup (non affichés, pour détection de nouveauté)
double ZigzagLawnBuffer1_Prev[],ZigzagPeakBuffer1_Prev[];
double ZigzagLawnBuffer2_Prev[],ZigzagPeakBuffer2_Prev[];

//==== VARIABLES GLOBALES POUR MTF, ALERTES ET PERFORMANCE ====
int handle_MTF1_slow_dn, handle_MTF1_slow_up, handle_MTF1_fast_dn, handle_MTF1_fast_up;
int handle_MTF2_slow_dn, handle_MTF2_slow_up, handle_MTF2_fast_dn, handle_MTF2_fast_up;
datetime last_alert_time = 0;
int reversal_zone_counter = 0;
datetime last_bar_time = 0; // Pour l'optimisation OnCalculate

//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
void OnInit()
{
//---- initialisation des variables de base
   min_rates_total=int(MathMax(SlowLength,FastLength))+1;
   IndicatorShortName=StringFormat("Boa_ZigZag_Arrows_Duplex(%d,%d)",SlowLength,FastLength);
   IndicatorSetString(INDICATOR_SHORTNAME,IndicatorShortName);
   IndicatorSetInteger(INDICATOR_DIGITS,_Digits);

//==== INITIALISATION DES BUFFERS PRINCIPAUX ====
   SetIndexBuffer(0,ZigzagLawnBuffer1,INDICATOR_DATA);
   PlotIndexSetInteger(0,PLOT_DRAW_BEGIN,min_rates_total);
   PlotIndexSetDouble(0,PLOT_EMPTY_VALUE,NULL);
   ArraySetAsSeries(ZigzagLawnBuffer1,true);
   PlotIndexSetInteger(0,PLOT_ARROW,162);

   SetIndexBuffer(1,ZigzagPeakBuffer1,INDICATOR_DATA);
   PlotIndexSetInteger(1,PLOT_DRAW_BEGIN,min_rates_total);
   PlotIndexSetDouble(1,PLOT_EMPTY_VALUE,NULL);
   ArraySetAsSeries(ZigzagPeakBuffer1,true);
   PlotIndexSetInteger(1,PLOT_ARROW,162);

   SetIndexBuffer(2,ZigzagLawnBuffer2,INDICATOR_DATA);
   PlotIndexSetInteger(2,PLOT_DRAW_BEGIN,min_rates_total);
   PlotIndexSetDouble(2,PLOT_EMPTY_VALUE,NULL);
   ArraySetAsSeries(ZigzagLawnBuffer2,true);
   PlotIndexSetInteger(2,PLOT_ARROW,159);

   SetIndexBuffer(3,ZigzagPeakBuffer2,INDICATOR_DATA);
   PlotIndexSetInteger(3,PLOT_DRAW_BEGIN,min_rates_total);
   PlotIndexSetDouble(3,PLOT_EMPTY_VALUE,NULL);
   ArraySetAsSeries(ZigzagPeakBuffer2,true);
   PlotIndexSetInteger(3,PLOT_ARROW,159);

//==== INITIALISATION DES BUFFERS BACKUP (pour détection d'alertes) ====
   SetIndexBuffer(4,ZigzagLawnBuffer1_Prev,INDICATOR_CALCULATIONS);
   ArraySetAsSeries(ZigzagLawnBuffer1_Prev,true);
   SetIndexBuffer(5,ZigzagPeakBuffer1_Prev,INDICATOR_CALCULATIONS);
   ArraySetAsSeries(ZigzagPeakBuffer1_Prev,true);
   SetIndexBuffer(6,ZigzagLawnBuffer2_Prev,INDICATOR_CALCULATIONS);
   ArraySetAsSeries(ZigzagLawnBuffer2_Prev,true);
   SetIndexBuffer(7,ZigzagPeakBuffer2_Prev,INDICATOR_CALCULATIONS);
   ArraySetAsSeries(ZigzagPeakBuffer2_Prev,true);

//==== INITIALISATION MTF HANDLES (si activé) ====
   if(EnableMTF)
     {
      string path = "::Boa_ZigZag_Arrows_Duplex";
      if(MTF_TF1 != PERIOD_CURRENT)
        {
         handle_MTF1_slow_dn = iCustom(NULL, MTF_TF1, path, SlowLength, FastLength, 0);
         handle_MTF1_slow_up = iCustom(NULL, MTF_TF1, path, SlowLength, FastLength, 1);
         handle_MTF1_fast_dn = iCustom(NULL, MTF_TF1, path, SlowLength, FastLength, 2);
         handle_MTF1_fast_up = iCustom(NULL, MTF_TF1, path, SlowLength, FastLength, 3);
        }
      if(MTF_TF2 != PERIOD_CURRENT && MTF_TF2 != MTF_TF1)
        {
         handle_MTF2_slow_dn = iCustom(NULL, MTF_TF2, path, SlowLength, FastLength, 0);
         handle_MTF2_slow_up = iCustom(NULL, MTF_TF2, path, SlowLength, FastLength, 1);
         handle_MTF2_fast_dn = iCustom(NULL, MTF_TF2, path, SlowLength, FastLength, 2);
         handle_MTF2_fast_up = iCustom(NULL, MTF_TF2, path, SlowLength, FastLength, 3);
        }
     }

//==== NETTOYAGE INITIAL DES OBJETS GRAPHIQUES ====
   ObjectsDeleteAll(0, "ReversalZone_");
}

//+------------------------------------------------------------------+
//| Fonction utilitaire pour la détection de nouvelle bougie         |
//+------------------------------------------------------------------+
bool IsNewBar(const datetime &time[])
{
//--- si le temps de la bougie actuelle est différent du temps stocké, c'est une nouvelle bougie
   if(last_bar_time != time[0])
     {
      last_bar_time = time[0]; // Mettre à jour le temps de la dernière bougie
      return(true);
     }
   return(false);
}

//+------------------------------------------------------------------+
//| Custom indicator iteration function                              |
//+------------------------------------------------------------------+
int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &time[],
                const double &open[],
                const double& high[],
                const double& low[],
                const double &close[],
                const long &tick_volume[],
                const long &volume[],
                const int &spread[])
{
//---- vérification minimale
   if(rates_total < min_rates_total)
      return(0);

//==== CALCUL DU ZIGZAG ORIGINAL (inchangé) ====
   CalculateZigZag(rates_total, high, low, SlowLength, ZigzagLawnBuffer1, ZigzagPeakBuffer1);
   CalculateZigZag(rates_total, high, low, FastLength, ZigzagLawnBuffer2, ZigzagPeakBuffer2);

//==== DÉTECTION DE NOUVEAUX SIGNAUX ET DÉCLENCHEMENT D'ALERTES (à chaque tick pour réactivité) ====
   DetectAndTriggerAlerts(rates_total, time);

//==== OPÉRATIONS COÛTEUSES (exécutées seulement sur nouvelle bougie pour la performance) ====
   if(IsNewBar(time))
     {
      //---- DESSIN DES ZONES DE REVERSAL (si activé)
      if(EnableReversalZones)
         DrawReversalZones(rates_total, time);

      //---- TRAITEMENT MULTITEMPOREL (si activé)
      if(EnableMTF)
         ProcessMTF(rates_total, time);
     }

//==== SAUVEGARDE DES BUFFERS COURANTS POUR COMPARAISON PROCHAINE ====
   BackupCurrentBuffers(rates_total);

//---- retourne le nombre de barres traitées
   return(rates_total);
}

//==== FONCTION UTILITAIRE : CALCUL ZIGZAG (logique inchangée) ====
void CalculateZigZag(int rates_total, const double &high[], const double &low[], uint length, double &lawnBuffer[], double &peakBuffer[])
{
   int limit = rates_total - min_rates_total;
   int climit=limit;
   double HH,LL,BH,BL;
   int zu=limit,zd=limit;
   int Swing=0,Swing_n=0;

   ArraySetAsSeries(high,true);
   ArraySetAsSeries(low,true);
   BH=high[limit];
   BL=low[limit];

   for(int bar=limit; bar>=0 && !IsStopped(); bar--)
     {
      lawnBuffer[bar]=NULL;
      peakBuffer[bar]=NULL;

      HH=high[ArrayMaximum(high,bar+1,length)];
      LL=low[ArrayMinimum(low,bar+1,length)];

      if(low[bar]<LL && high[bar]>HH)
        {
         Swing=2;
         if(Swing_n==1)
            zu=bar+1;
         if(Swing_n==-1)
            zd=bar+1;
        }
      else
        {
         if(low[bar]<LL)
            Swing=-1;
         if(high[bar]>HH)
            Swing=1;
        }

      if(Swing!=Swing_n && Swing_n!=0)
        {
         if(Swing==2)
           {
            Swing=-Swing_n;
            BH=high[bar];
            BL=low[bar];
           }
         if(Swing==1)
           {
            if(BL==low[zd])
               lawnBuffer[zd]=BL;
            else
               lawnBuffer[zd-1]=BL;
           }
         if(Swing==-1)
           {
            if(BH==high[zu])
               peakBuffer[zu]=BH;
            else
               peakBuffer[zu-1]=BH;
           }
         BH=high[bar];
         BL=low[bar];
        }

      if(Swing==1)
        {
         if(high[bar]>=BH)
           {
            BH=high[bar];
            zu=bar;
           }
        }
      if(Swing==-1)
        {
         if(low[bar]<=BL)
           {
            BL=low[bar];
            zd=bar;
           }
        }
      Swing_n=Swing;
     }

}

//==== FONCTION UTILITAIRE : SAUVEGARDE BUFFERS POUR COMPARAISON ====
void BackupCurrentBuffers(int rates_total)
{
   int limit = rates_total - min_rates_total;
   for(int i = 0; i <= limit; i++)
     {
      ZigzagLawnBuffer1_Prev[i] = ZigzagLawnBuffer1[i];
      ZigzagPeakBuffer1_Prev[i] = ZigzagPeakBuffer1[i];
      ZigzagLawnBuffer2_Prev[i] = ZigzagLawnBuffer2[i];
      ZigzagPeakBuffer2_Prev[i] = ZigzagPeakBuffer2[i];
     }
}

//==== FONCTION UTILITAIRE : DÉTECTION ET DÉCLENCHEMENT D'ALERTES ====
void DetectAndTriggerAlerts(int rates_total, const datetime &time[])
{
   int limit = rates_total - min_rates_total;
   for(int i = 0; i <= limit; i++)
     {
      // Slow Down
      if(ZigzagLawnBuffer1[i] != NULL && ZigzagLawnBuffer1_Prev[i] == NULL)
         TriggerAlerts("SLOW", "DOWN", ZigzagLawnBuffer1[i], time[i], "Slow Boa_ZigZag Down @ ");
      // Slow Up
      if(ZigzagPeakBuffer1[i] != NULL && ZigzagPeakBuffer1_Prev[i] == NULL)
         TriggerAlerts("SLOW", "UP", ZigzagPeakBuffer1[i], time[i], "Slow Boa_ZigZag Up @ ");
      // Fast Down
      if(ZigzagLawnBuffer2[i] != NULL && ZigzagLawnBuffer2_Prev[i] == NULL)
         TriggerAlerts("FAST", "DOWN", ZigzagLawnBuffer2[i], time[i], "Fast Boa_ZigZag Down @ ");
      // Fast Up
      if(ZigzagPeakBuffer2[i] != NULL && ZigzagPeakBuffer2_Prev[i] == NULL)
         TriggerAlerts("FAST", "UP", ZigzagPeakBuffer2[i], time[i], "Fast Boa_ZigZag Up @ ");
     }
}

//==== FONCTION UTILITAIRE : DÉCLENCHEMENT DES ALERTES (visuelles, sonores, notifications) ====
void TriggerAlerts(string tf, string dir, double price, datetime t, string prefix)
{
//--- Prévention du spam d'alertes sonores (une alerte par seconde maximum)
   if(EnableSoundAlerts)
     {
      if(TimeCurrent() - last_alert_time < 1)
         return;
      last_alert_time = TimeCurrent();
     }

   string msg = StringFormat("%s %s %s %.5f", prefix, tf, dir, price);
   string tf_str = (tf=="SLOW") ? "Slow" : "Fast";

// Visuelle : déjà gérée par les flèches, on peut ajouter une bulle si désiré
   if(EnableVisualAlerts)
     {
      // Option : ajouter une bulle ou texte sur le graphique
      // ObjectCreate(0, "Alert_"+TimeToString(t), OBJ_TEXT, 0, t, price);
      // ObjectSetString(0, "Alert_"+TimeToString(t), OBJPROP_TEXT, msg);
     }

// Sonore
   if(EnableSoundAlerts)
      Alert(msg);

// Notification Push
   if(EnablePushAlerts)
      SendNotification(msg);

// Email
   if(EnableEmailAlerts && EmailTo != "")
      SendMail(EmailSubject, msg + " | Time: " + TimeToString(t) + " | Symbol: " + _Symbol);

//==== Hook OnSignal ==== (pour intégration EA, logs, etc.)
// Exemple d'utilisation dans un EA :
// EventChartCustom(0, 1001, (long)price, 0, StringFormat("%s|%s|%.5f", tf_str, dir, price));
// EventSetTimer(1); // pour rafraîchir si nécessaire
}

//==== FONCTION UTILITAIRE : DESSIN DES ZONES DE REVERSAL ====
void DrawReversalZones(int rates_total, const datetime &time[])
{
// Nettoyer les anciennes zones
   ObjectsDeleteAll(0, "ReversalZone_");

// Collecter les derniers points de reversal
   double levels[];
   datetime times[];
   ArrayResize(levels, 0);
   ArrayResize(times, 0);

   int limit = rates_total - min_rates_total;
   int count = 0;

   for(int i = 0; i <= limit && count < ReversalZoneLookback; i++)
     {
      if(ZigzagLawnBuffer1[i] != NULL)
        {
         ArrayResize(levels, count+1);
         ArrayResize(times, count+1);
         levels[count] = ZigzagLawnBuffer1[i];
         times[count] = time[i];
         count++;
        }
      if(ZigzagPeakBuffer1[i] != NULL && count < ReversalZoneLookback)
        {
         ArrayResize(levels, count+1);
         ArrayResize(times, count+1);
         levels[count] = ZigzagPeakBuffer1[i];
         times[count] = time[i];
         count++;
        }
      if(ZigzagLawnBuffer2[i] != NULL && count < ReversalZoneLookback)
        {
         ArrayResize(levels, count+1);
         ArrayResize(times, count+1);
         levels[count] = ZigzagLawnBuffer2[i];
         times[count] = time[i];
         count++;
        }
      if(ZigzagPeakBuffer2[i] != NULL && count < ReversalZoneLookback)
        {
         ArrayResize(levels, count+1);
         ArrayResize(times, count+1);
         levels[count] = ZigzagPeakBuffer2[i];
         times[count] = time[i];
         count++;
        }
     }

// Dessiner les zones
   for(int i = 0; i < count; i++)
     {
      string name = "ReversalZone_" + string(i);
      datetime end_time = times[i] + ReversalZoneMinutes * 60;
      ObjectCreate(0, name, OBJ_RECTANGLE, 0, times[i], levels[i] * 0.999, end_time, levels[i] * 1.001);
      ObjectSetInteger(0, name, OBJPROP_COLOR, ReversalZoneColor);
      ObjectSetInteger(0, name, OBJPROP_STYLE, STYLE_SOLID);
      ObjectSetInteger(0, name, OBJPROP_WIDTH, 1);
      ObjectSetInteger(0, name, OBJPROP_FILL, true);
      ObjectSetInteger(0, name, OBJPROP_BACK, true);
      ObjectSetInteger(0, name, OBJPROP_COLOR, ColorToARGB(ReversalZoneColor, ReversalZoneAlpha));
     }
}

//==== FONCTION UTILITAIRE : TRAITEMENT MULTITEMPOREL ====
void ProcessMTF(int rates_total, const datetime &time[])
{
   if(!EnableMTF)
      return;

// Traiter MTF_TF1
   if(MTF_TF1 != PERIOD_CURRENT && handle_MTF1_slow_dn != INVALID_HANDLE)
     {
      ProcessMTFTimeframe(MTF_TF1, handle_MTF1_slow_dn, handle_MTF1_slow_up, handle_MTF1_fast_dn, handle_MTF1_fast_up, rates_total, time);
     }

// Traiter MTF_TF2
   if(MTF_TF2 != PERIOD_CURRENT && MTF_TF2 != MTF_TF1 && handle_MTF2_slow_dn != INVALID_HANDLE)
     {
      ProcessMTFTimeframe(MTF_TF2, handle_MTF2_slow_dn, handle_MTF2_slow_up, handle_MTF2_fast_dn, handle_MTF2_fast_up, rates_total, time);
     }
}

//==== FONCTION UTILITAIRE : TRAITEMENT D'UN TIMEFRAME MTF SPÉCIFIQUE ====
void ProcessMTFTimeframe(ENUM_TIMEFRAMES tf, int h_slow_dn, int h_slow_up, int h_fast_dn, int h_fast_up, int rates_total, const datetime &time[])
{
   int limit = MathMin(MTF_MaxLookback, rates_total - min_rates_total);
   if(limit <= 0)
      return;

   double slow_dn[], slow_up[], fast_dn[], fast_up[];
   int copied;

// Copier les buffers du timeframe cible
   copied = CopyBuffer(h_slow_dn, 0, 0, limit, slow_dn);
   if(copied <= 0)
      return;
   copied = CopyBuffer(h_slow_up, 0, 0, limit, slow_up);
   if(copied <= 0)
      return;
   copied = CopyBuffer(h_fast_dn, 0, 0, limit, fast_dn);
   if(copied <= 0)
      return;
   copied = CopyBuffer(h_fast_up, 0, 0, limit, fast_up);
   if(copied <= 0)
      return;

// Pour chaque signal détecté sur le TF cible, déclencher une alerte si synchronisé
   for(int i = 0; i < limit; i++)
     {
      datetime tf_time = iTime(NULL, tf, i);
      if(tf_time == 0)
         continue;

      int current_bar_index = iBarShift(NULL, 0, tf_time, false);
      if(current_bar_index == -1 || current_bar_index > rates_total - min_rates_total)
         continue;

      if(slow_dn[i] != NULL)
         TriggerAlerts("SLOW_MTF_"+EnumToString(tf), "DOWN", slow_dn[i], tf_time, "MTF Slow Down @ ");
      if(slow_up[i] != NULL)
         TriggerAlerts("SLOW_MTF_"+EnumToString(tf), "UP",   slow_up[i], tf_time, "MTF Slow Up @ ");
      if(fast_dn[i] != NULL)
         TriggerAlerts("FAST_MTF_"+EnumToString(tf), "DOWN", fast_dn[i], tf_time, "MTF Fast Down @ ");
      if(fast_up[i] != NULL)
         TriggerAlerts("FAST_MTF_"+EnumToString(tf), "UP",   fast_up[i], tf_time, "MTF Fast Up @ ");
     }

}

//+------------------------------------------------------------------+
//| Fonction de nettoyage (appelée à la désinstallation)             |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   ObjectsDeleteAll(0, "ReversalZone_");
   if(EnableMTF)
     {
      if(handle_MTF1_slow_dn != INVALID_HANDLE)
         IndicatorRelease(handle_MTF1_slow_dn);
      if(handle_MTF1_slow_up != INVALID_HANDLE)
         IndicatorRelease(handle_MTF1_slow_up);
      if(handle_MTF1_fast_dn != INVALID_HANDLE)
         IndicatorRelease(handle_MTF1_fast_dn);
      if(handle_MTF1_fast_up != INVALID_HANDLE)
         IndicatorRelease(handle_MTF1_fast_up);
      if(handle_MTF2_slow_dn != INVALID_HANDLE)
         IndicatorRelease(handle_MTF2_slow_dn);
      if(handle_MTF2_slow_up != INVALID_HANDLE)
         IndicatorRelease(handle_MTF2_slow_up);
      if(handle_MTF2_fast_dn != INVALID_HANDLE)
         IndicatorRelease(handle_MTF2_fast_dn);
      if(handle_MTF2_fast_up != INVALID_HANDLE)
         IndicatorRelease(handle_MTF2_fast_up);
     }
}
