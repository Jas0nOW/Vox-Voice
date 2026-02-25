# VOX BOT BRIDGE

Stand: 2026-02-25

## Ziel

Telegram/Discord koennen Voice-STT ueber VOX nutzen.

## Betriebsmodi

- CLI-Modus: `VOX_STT_MODE=cli`
- Webhook-Fallback: `VOX_STT_MODE=webhook` + `VOX_STT_WEBHOOK_URL`

## Basis-Validierung

```bash
./scripts/validate_basics.sh
```

## Erwartetes Verhalten

- `wandavoice.main --help` muss laufen.
- `websockets` muss in `.venv` vorhanden sein.
- Transkriptionsfehler fallen kontrolliert auf Webhook zurueck (wenn gesetzt).
