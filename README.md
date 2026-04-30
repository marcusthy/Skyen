# SKYEN
En selvhostet fillagringsapp bygget med Flask + MySQL inspirert av Google Drive/icloud.

## Oversikt

SKYEN er en personlig "sky" der du kan lagre dine egne filer på din egen
server. Du oppretter en bruker, logger inn, og får din egen private side der
du kan laste opp, se og laste ned filene dine.

Hovedfunksjoner:
- **Egen bruker** med innlogging – ingen andre ser filene dine.
- **Last opp filer** ved å klikke eller dra-og-slippe (flere filer samtidig).
- **Min side** viser en liste over alt du har lastet opp.
- **Galleri** for bilder og videoer, automatisk gruppert etter måned basert
  på når bildet/videoen ble tatt.
- **Forhåndsvisning** av bilder, videoer og PDF rett i nettleseren.
- **Last ned** eller **slett** filer når du vil.

Tanken er å ha noe som ligner Google Drive eller iCloud, men der filene
faktisk ligger på din egen maskin.

## Hvordan filprosessen fungerer

Når du laster opp en fil i SKYEN skjer dette:

1. **Du velger en fil** i nettleseren enten ved å klikke på opplastingsfeltet
   eller ved å dra og slippe filen.
2. **Filen sendes til serveren** når du trykker "Last opp".
3. **Serveren sjekker filtypen** og avviser filer som ikke er tillatt.
4. **Filen lagres på disk** med et tilfeldig navn, slik at to filer med samme
   navn ikke kolliderer. Originalnavnet beholdes så du ser det igjen i listen.
5. **Metadata leses ut:** for bilder hentes datoen bildet ble tatt (EXIF), og
   for videoer hentes opptaksdatoen. Slik kan galleriet sortere etter når
   bildet faktisk ble tatt ikke bare når det ble lastet opp.
6. **Info om filen lagres i databasen** (eier, navn, type, størrelse, dato).
7. **Filen dukker opp** i listen din på "Min side" og i galleriet hvis det er
   bilde eller video.

Når du senere laster ned, viser eller sletter en fil, sjekker serveren alltid
at filen tilhører deg før den gjør noe.

## TODO liste

### Bruker & Autentisering
- [x] Brukerregistrering
- [x] Innlogging / utlogging

### Filopplasting
- [x] Last opp filer fra nettleser
- [x] Lagre filer på server
- [x] Lagre filnavn, størrelse, type og eier i database
- [ ] Begrens filstørrelse og tillatte filtyper
- [x] Les metadata fra filer og bilder (EXIF via Pillow, creation_time for video via ffprobe)
- [x] Sorter filer automatisk etter dato fra metadata (f.eks. bildet tatt 12. mars → plasseres under mars)

### Filvisning
- [x] Vis liste over egne filer
- [x] Last ned filer
- [x] Forhåndsvisning av bilder og videoer (lightbox + videomodal i galleri)
- [x] Forhåndsvisning av PDF
- [x] Slett filer

### Deling
- [ ] Generer delbar lenke per fil
- [ ] Sett utløpsdato på delingslenker
- [ ] Del med spesifikke brukere

### Mapper
- [ ] Opprett mapper
- [ ] Flytt filer mellom mapper
- [ ] Undermapper

### Grensesnitt
- [x] Moderne og responsivt design
- [x] Dra og slipp opplasting
- [ ] Søk i filer

### Sikkerhet
- [x] Filer skal kun være tilgjengelig for eieren
- [ ] Hastighetsbegrensning på opplasting

