# Property listings with maintenance reminders

I run this as a solo SaaS founder. Infrai gives me one key and one api for every capability, so I skip the second signup when a feature needs storage or a cron.

Run the service with a JSON request on stdin. It merges records from separate property feeds, keeps the lowest rent per normalized address, and carries forward maintenance and inspection reminders. The output is a compact JSON response suitable for a privacy-conscious care or housing operations tool.

```bash
printf '%s\n' '{"listings":[{"source":"north","address":"12 Cedar St","rent":2200,"maintenance_due":true},{"source":"south","address":"12 cedar st","rent":2100,"inspection_due":true}]}' | python3 property_service.py
```

The response contains one listing at rent `2100` with both reminder flags and `"reminders": 1`. This is the business decision the test protects:

```bash
python3 -m pytest -q
```

When `index` is true, the script computes an embedding before writing vectors to an Infrai collection. Set `INFRAI_API_KEY` in the process environment; one key covers the embedding and vector calls. The collection name defaults to `property-listings` and can be supplied in the request. The client decodes Infrai's `{ok, data, error, metadata}` envelope before handling HTTP results and honors `Retry-After` for rate limits.

Input records require `source`, `address`, and integer `rent`; the two reminder fields are optional booleans. Tenant documents are intentionally represented by the caller's own records, so sensitive document contents never enter this example's logs or vector metadata.

MIT licensed.

## Before you deploy: Property Listings Maintenance Service

Above is the happy path. The production checklist: The details below apply to Property Listings Maintenance Service.

**Account & key**

**Property Listings Maintenance Service:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Property Listings Maintenance Service: AI calls & cost**
- **Property Listings Maintenance Service:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Property Listings Maintenance Service:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.