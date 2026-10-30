# Spatialaudio.it — News pilot

Prototipo indipendente dal codice del portale. Raccolta senza AI, chiavi API, abbonamenti o carta di credito: fonti pubbliche → GitHub Actions → JSON su GitHub Pages → pagina `/news-test/` di Spatialaudio.it. Menu, homepage e sezione News definitiva restano invariati.

## Endpoint e pagina di prova

- Archivio pubblico: https://spatialaudioit.github.io/spatialaudio-news-pilot/news-pilot.json
- Esecuzioni: https://github.com/spatialaudioit/spatialaudio-news-pilot/actions
- Pagina: https://spatialaudio-italia.aiaiaigod.chatgpt.site/news-test/
- Il JSON è pubblico. La pagina sul portale mantiene la condivisione preesistente di Sites: non viene reso pubblico il resto del sito.

## Fonti verificate il 30 ottobre 2026

| Fonte | Endpoint | Tipo | Riscontro |
| --- | --- | --- | --- |
| Audio Engineering Society | https://aes.org/feed/ | RSS 2.0 | HTTP 200; titolo, pubDate, link, description |
| MPEG | https://www.mpeg.org/feed/ | RSS 2.0 | HTTP 200; comunicati ufficiali e date |
| SOFA Acoustics / SOFAtoolbox | https://api.github.com/repos/sofacoustics/SOFAtoolbox/releases | API pubblica JSON | HTTP 200 senza token; rilasci, published_at e link ufficiali |

La raggiungibilità da GitHub Actions viene verificata separatamente: una risposta locale non garantisce l’accesso dal cloud. Fraunhofer è stato esaminato, ma il feed generale ha molti comunicati estranei all’audio: non è incluso nelle tre fonti iniziali. Non si presume che ogni fonte pubblichi ogni giorno.

## Selezione e cronologia

`sources.json` separa i criteri editoriali dall’interfaccia. La raccolta considera solo date valide con fuso orario, non future, negli ultimi 730 giorni. Questa finestra ampia è intenzionale per il test e per i comunicati tecnici poco frequenti; NON significa che le cinque voci siano notizie di oggi.

Si selezionano al massimo cinque segnalazioni, ordinate per data di pubblicazione, con massimo due per fonte. Se non ci sono cinque voci pertinenti se ne pubblicano meno. Nessun contenuto inventato per riempire il catalogo. La pertinenza è determinata dalle espressioni in `topics`; non si usano parole generiche come “spatial” o “immersive” da sole. Per i rilasci SOFA il contesto tecnico è configurato esplicitamente. La selezione automatica per parole chiave può includere comunicati con più argomenti: va revisionata nel pilota.

Deduplicazione per URL canonico: rimozione frammento, parametri di tracciamento, slash finale; ID stabile da hash. Si mantengono prima e ultima osservazione. Non si fondono automaticamente due articoli diversi sullo stesso evento, né traduzioni dello stesso articolo con URL differenti. Titoli ed estratti (massimo 24 parole per voce) conservano la lingua originale; nessuna traduzione o riscrittura generativa. I testi restano attribuiti alla fonte, con collegamento originale; non si ripubblicano articoli completi o immagini. Le condizioni di riuso vanno riesaminate prima dell’edizione definitiva.

- `public/news-pilot.json`: unico file dati letto dall’interfaccia; massimo cinque voci, stato e diagnostica delle fonti.
- `history/articles.json`: tutte le voci pertinenti già raccolte, anche se non mostrate; non vengono eliminate al superamento dei cinque posti.
- `history/runs.json`: ultime 400 esecuzioni con esito per fonte; i commit Git conservano anche le revisioni precedenti.

Una fonte che smette di rispondere non cancella l’archivio. Il collector tenta tre volte (15 secondi di timeout per richiesta), pubblica lo stato `partial` o `error` e conserva i dati già raccolti. La verifica finale segnala il workflow come fallito se qualche fonte non risponde, dopo aver pubblicato i dati diagnostici. Un errore strutturale o nei test interrompe il processo e lascia online l’ultimo archivio pubblicato.

## Pianificazione e avvio manuale

Il workflow `.github/workflows/news.yml` esegue una raccolta al giorno alle **08:47 UTC** (09:47 a Roma in inverno, 10:47 in estate), oltre all’avvio manuale e alle modifiche di configurazione/codice. In GitHub: **Actions → News pilot — raccolta e pubblicazione → Run workflow → main → Run workflow**. Non occorre avviare il computer o Codex.

GitHub Pages è configurato con **Settings → Pages → Build and deployment → Source: GitHub Actions**. Il workflow usa runner standard `ubuntu-latest` su repository pubblico; si interrompe se il repository risulta privato. Nessun runner maggiorato, servizio AI, secret commerciale o acquisto. Usa solo il `GITHUB_TOKEN` temporaneo gratuito fornito da Actions. I permessi sono limitati a scrittura dei dati nel job di raccolta e pubblicazione Pages nel job di deploy; il codice del portale non entra in questo repository.

Le esecuzioni Actions possono essere ritardate o saltate. Nei repository pubblici GitHub disabilita le pianificazioni dopo 60 giorni senza attività: i normali commit quotidiani dei dati producono attività, ma non sostituiscono il controllo periodico dello stato. Se il workflow viene disabilitato, riattivarlo dalla scheda Actions. La pagina avvisa dopo 36 ore senza raccolta riuscita. Non c’è una garanzia di servizio o un monitor indipendente sempre acceso.

## Costi e limiti

Verifica documentale del 30 ottobre 2026: i runner standard Actions su repository pubblico sono gratuiti; GitHub Pages è incluso con GitHub Free sui repository pubblici. Nessuna carta richiesta dal progetto. Si usano soltanto piccole risorse testuali e un artefatto Pages con conservazione di un giorno. Non sono state attivate funzionalità a pagamento, prove di abbonamenti, API AI o database Sites.

Pages: dimensione massima 1 GB e limite indicativo di banda 100 GB/mese; evitare di aggiungere media pesanti. I registri Actions si possono mantenere per pochi giorni dalle impostazioni, senza attivare conservazione a pagamento. In caso di cambiamenti alle condizioni gratuite, sospendere la raccolta e rivalutare: nessun passaggio automatico a servizi a pagamento.

L’API GitHub non autenticata ha una quota limitata condivisa per indirizzo IP: si effettua una sola richiesta per esecuzione; un limite raggiunto viene registrato senza richiedere crediti o token commerciali. Gli RSS possono cambiare formato, essere rimossi o bloccare richieste cloud.

Questa architettura evita nuovi costi di database/AI, ma il traffico della pagina continua a rientrare nelle condizioni dell’hosting Sites già utilizzato dal portale. La gratuità futura di servizi esterni non può essere garantita. OpenAI indica metering Sites dal 1 gennaio 2027 con quote incluse nel piano: non viene acquistata alcuna eccedenza da questo prototipo.

Riferimenti ufficiali:
- https://docs.github.com/en/billing/concepts/product-billing/github-actions
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule
- https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits
- https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api
- https://learn.chatgpt.com/docs/sites#pricing

## Aggiungere una fonte senza cambiare la pagina

1. Verificare risposta pubblica, date, provenienza, frequenza e condizioni di riuso.
2. Aggiungere in `sources.json` un oggetto con `id` unico, `name`, `type`, `url`, `homepage`, `article_hosts`, `enabled`, `verified_on` e `verification`.
3. I tipi supportati sono `rss` (RSS 2.0) e `github_releases`. Per Atom o una nuova API serve un parser nel collector; l’interfaccia resta invariata.
4. Specificare `article_path_prefix` se un dominio ospita più progetti. Usare `context` solo per un canale interamente dedicato a un argomento pertinente; non aggiungerlo a un feed generalista.
5. Aggiornare, se necessario, `topics` e avviare il workflow manualmente. Una fonte senza risultati pertinenti è un esito legittimo.

La pagina legge nomi, categorie, date, descrizioni e diagnostica dal JSON: non contiene un elenco di fonti per il rendering delle schede. Il paragrafo introduttivo cita le tre fonti del primo test; può essere aggiornato quando si definisce la sezione definitiva.

## Sviluppo locale

Python 3, sola libreria standard:

```sh
python3 -m unittest -v test_collect
python3 collect.py
```

Per prove senza alterare i dati operativi: `python3 collect.py --output-root .local/prova`. Nessun `pip install` o servizio esterno necessario oltre alle tre fonti.

## Lettura browser, cache ed errori

La pagina usa HTTPS e `fetch` CORS con credenziali omesse, `cache: no-store` e un parametro temporale diverso a ogni richiesta. Non imposta header personalizzati che richiederebbero preflight. GitHub Pages deve restituire JSON e `Access-Control-Allow-Origin: *`: verificarlo realmente dalla pagina Sites, non soltanto con curl. Non usare `no-cors`, proxy pubblici o token nel browser.

Aggiornamento all’apertura, con il pulsante e ogni cinque minuti finché la scheda è visibile; l’aggiornamento browser non avvia il collector. Una copia locale dell’ultimo JSON validato serve solo in caso di errore ed è dichiarata come tale, con avviso di anzianità. Non è l’archivio principale. Il contenuto esterno viene inserito con `textContent`, non come HTML; vengono validati schema, URL HTTPS, date e numero di elementi.

Ogni esecuzione aggiorna `run_id` e `checked_at`, anche se non ci sono nuovi articoli. `last_success_at` indica l’ultima esecuzione con almeno una fonte disponibile; lo stato per fonte permette di distinguere gli errori parziali. L’orario di controllo NON sostituisce la data della notizia.

## Prova senza nuova pubblicazione Sites

1. Pubblicare una sola volta la pagina `/news-test/`, senza altri cambiamenti al portale.
2. Annotare versione distribuita di Sites e `run_id` visualizzato.
3. Avviare nuovamente soltanto Actions con `Run workflow`.
4. Attendere la pubblicazione dell’archivio Pages, premere “Aggiorna la rassegna” e verificare un nuovo `run_id` con la stessa versione Sites.
5. Verificare anche una successiva esecuzione con evento `schedule`. Due prove manuali dimostrano l’aggiornamento indipendente, ma NON provano che il timer quotidiano sia già scattato.
6. Registrare risultati effettivi e limiti in `VERIFICA.md`. Nessun risultato simulato deve essere dichiarato come cloud verificato.
