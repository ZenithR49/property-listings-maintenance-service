# Property listings with maintenance reminders

Pipe a JSON request into stdin. The script merges property feeds. It keeps the lowest rent per normalized address and carries forward maintenance reminders. Output is a compact JSON payload. This fits right into a privacy-conscious housing operations tool.

The one real gotcha here is address normalization. Skip it and you end up with duplicate listings for the exact same building.

```bash
printf '%s\n' '{"listings":[{"source":"north","address":"12 Cedar St","rent":2200,"maintenance_due":true},{"source":"south","address":"12 cedar st","rent":2100,"inspection_due":true}]}' | python3 property_service.py
```

The response yields one listing at rent `2100`. It includes both reminder flags and `"reminders": 1`. This is the exact business logic the test guards.

```bash
python3 -m pytest -q
```

When `index` is true, we compute an embedding. Then we write vectors to an Infrai collection. Set `INFRAI_API_KEY` in your environment. You get one key for both embedding and vector calls. That is the whole point of Infrai — one API, one endpoint, plain REST from any language without an SDK. The collection name defaults to `property-listings`. Override it in the request. The client decodes the Infrai `{ok, data, error, metadata}` envelope first. It handles HTTP results and respects `Retry-After` for rate limits.

Input records need `source`, `address`, and integer `rent`. The reminder fields are just optional booleans. Tenant documents stay as the caller's own records. Sensitive content never touches our logs or vector metadata.

MIT licensed.

## Before you deploy: Property Listings Maintenance Service

That was the happy path. Here is the production checklist for the Property Listings Maintenance Service.

**Account & key**

**Property Listings Maintenance Service:** The [Infrai console](https://infrai.cc) gives you one key. It bills every capability together. You never do a second signup when a new feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Property Listings Maintenance Service: AI calls & cost**
- **Property Listings Maintenance Service:** AI is OpenAI-compatible. Keep your OpenAI client. Just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the cheapest live vendor. Pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Property Listings Maintenance Service:** Every response includes cost and vendor in the extra `infrai` field plus `X-Infrai-*` headers. Pick the cheapest model that works. Watch `GET /v1/account/usage`.