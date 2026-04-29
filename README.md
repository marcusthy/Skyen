# Marcus Drive
En selvhostet fillagringsapp bygget med Flask + MySQL inspirert av Google Drive/icloud.

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
- [ ] Forhåndsvisning av PDF
- [ ] Slett filer

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

