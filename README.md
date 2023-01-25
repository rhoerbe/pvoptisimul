# Import detailierter Daten von Joulie.at

Das Web Interface vom optimierung.joulie.at exportiert Daten nicht unter der Auflösung eines Tages.
Um sich ein Lastprofil zu erstellen, kann man mit der API die detaillierten Daten holen.

Ablauf:

Um die Daten im 5-Minuten Intervall zu bekommen, müssen sie pro Monat abgefragt werden, mehr geht nicht auf einmal.
Ein Aggregation auf 15min geht auch nicht.

Daten für einen Monat holen:
1. Aufruf der Jahresstatistik im Web Browser  mit der Darstellung "Photovoltaik, Netzbezug / Netzeinspeisung"
2. Mittels Developer Tools im Browser den letzten Aufruf auf https://optimierung.joulie.at/api/v3/properties/60001906/combined_devices/history/ suchen.
3. Mit curl oder Postman den Request nachbauen. Es muss der Authorization Header übernommen werden; Cookies sind nicht erforderlich.
4. Den GET request testen - da sollten die Monatssummen als JSON zurückkommen
5. Den Request ändern, indem den URL-Parameter resolution von "M" auf "5m" gesetzt wird.
6. Das Ergebins speichern und als Input für das main.py Script verwenden
7. main.py konvertiert die Daten nach Excel

Daten für einen größeren Zeitraum holen