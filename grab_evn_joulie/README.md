# Import detailierter Daten von Joulie.at

## Was ist der EVN Joulie Optimierungsassistent?
Das zugrunde liegende Produkt ist von Tiko Energy. 
Die lokal für PV und Verbraucher erfassten Messwerte werden in ein Cloud Service übermittelt.
Die Auswertung erfolgt über ein App oder die Webanwendung. 
Darüber hinaus bietet der Optimierungsassistent Funktionen zur Lastverschiebung.

## Detaillierte Daten
Das Web Interface von optimierung.joulie.at exportiert Daten nicht unter der Auflösung eines Tages.
Um genauere Auswertunen zu erstellen, z.B. ein Lastprofil zu erstellen oder die Wirtschaftlichkeit eines Speichers zu berechnen,
benötigt die Daten in der Auflösung des Stromzählers, also z.B. 15 Minuten für ein Smart Meter.
Mit dem Skript grab_tiko_data.py man mit der API der Webapplikation die detaillierten Daten holen.

Ablauf:
Um die Daten in Viertelstundenwerten zu bekommen, müssen sie im 5-Minuten Intervallen abgefragt werden.
Die Aggregation auf 15 Minuten muss in der nachfolgenden Auswertung passieren.
Pro Abfrage können nur Werte für maximal einen Monat abgefragt werden.
Das Skript führt daher pro Monat im gewünschten Zeitraum eine Abfrage aus.  

## Konfiguration und Ausführung
Daten für einen Monat holen:
1. Kundenspezifische Abfrage-URL und OAuth2 Access Token aus der Webanwendung ermitteln
    1. Aufruf der Jahresstatistik im Web Browser  mit der Darstellung "Photovoltaik, Netzbezug / Netzeinspeisung"
    2. Mittels Developer Tools im Browser den letzten Aufruf auf https://optimierung.joulie.at/api/v3/properties/*/combined_devices/history/ suchen.
    3. Den Request Header "Authorization" kopieren
2. Optional den ermittelten GET Request testen:
   1. Mit curl oder Postman den Request nachbauen. Es muss der Authorization Header übernommen werden; Cookies sind nicht erforderlich.
   2. Den GET request testen - es sollten die Monatssummen als JSON zurückkommen
3. Umgebungsvariable setzen:
   1. ACCESSTOKEN auf den Wert des Authorization Headers
   2. BASE_URL auf den oben ermittelten Wert (enthält die Kundennummer) 
   3. START_DATE und END_DATE im Format YYYY-MM-DD 
4. Das Ergebins speichern und als Input für das Hauptprojekt verwenden


