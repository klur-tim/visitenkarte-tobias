#!/usr/bin/env bash
# Erzeugt kontakt.vcf (vCard 3.0, so wie iPhone und Android sie erwarten) mit eingebettetem Foto.
# Foto: vcard-foto.jpg (quadratisch, ca. 780 px). Aufruf aus dem Projektordner: bash werkzeuge/vcard.sh
set -euo pipefail
cd "$(dirname "$0")/.."
B64=$(base64 -i vcard-foto.jpg | tr -d '\n')
{
printf 'BEGIN:VCARD\r\nVERSION:3.0\r\n'
printf 'N:Klur;Tobias;;Dr.;M.Sc.\r\n'
printf 'FN:Dr. Tobias Klur\\, M.Sc.\r\n'
printf 'ORG:RANG + KLUR Kieferorthopädie\r\n'
printf 'TITLE:Fachzahnarzt für Kieferorthopädie\r\n'
printf 'item1.TEL;TYPE=WORK,VOICE:+49 2251 74728\r\nitem1.X-ABLabel:Praxis Euskirchen\r\n'
printf 'item2.TEL;TYPE=WORK,VOICE:+49 2443 9025593\r\nitem2.X-ABLabel:Praxis Mechernich\r\n'
printf 'EMAIL;TYPE=WORK,INTERNET:info@rangundklur.eu\r\n'
printf 'item3.ADR;TYPE=WORK:;;Mittelstraße 4;Euskirchen;;53879;Deutschland\r\nitem3.X-ABLabel:Praxis Euskirchen\r\n'
printf 'item4.ADR;TYPE=WORK:;;Gartenstraße 20;Mechernich;;53894;Deutschland\r\nitem4.X-ABLabel:Praxis Mechernich\r\n'
printf 'URL;TYPE=WORK:https://www.rangundklur-kfo.de\r\n'
printf 'item5.URL:https://rangundklur.medondo.app/de/appointment\r\nitem5.X-ABLabel:Online-Termin\r\n'
# Soziale Profile im Apple-Format: Benutzername steht in x-user, sonst bleibt das Feld auf dem iPhone leer
printf 'X-SOCIALPROFILE;type=instagram;x-user=kfo.euskirchen:https://www.instagram.com/kfo.euskirchen/\r\n'
printf 'X-SOCIALPROFILE;type=facebook;x-user=kfo.euskirchen:https://www.facebook.com/kfo.euskirchen/\r\n'
printf 'NOTE:Fachzahnarzt für Kieferorthopädie · M.Sc. Funktionsanalyse und -therapie · Zertifizierter Kieferorthopäde der DGZS · Spezialist für Funktionsdiagnostik und -therapie (DGFDT)\r\n'
L="PHOTO;ENCODING=b;TYPE=JPEG:$B64"
printf '%s\r\n' "${L:0:75}"; R="${L:75}"
while [ -n "$R" ]; do printf ' %s\r\n' "${R:0:74}"; R="${R:74}"; done
printf 'END:VCARD\r\n'
} > kontakt.vcf
echo "kontakt.vcf erzeugt ($(du -h kontakt.vcf | cut -f1))"
