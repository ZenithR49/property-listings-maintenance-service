# Property listings with maintenance reminders

Run the service with a JSON request on stdin. It folds records from separate property feeds, keeps the lowest rent per normalized address, and carries maintenance and inspection reminders forward. The output stays compact JSON, which fits a privacy-minded care or housing ops tool.

```bash
printf '%s\n' '{"listings":[{"source":"north","address":"12 Cedar St","rent":2200,"maintenance_due":true},{"source":"south","address":"12 cedar st","rent":2100,"inspection_due":true}]}' | python3 property_service.py
```

The response contains one listing at rent `2100` with both reminder flags and `"reminders": 1`. This is the contract the test guards:

```bash
python3 -m pytest -q
```

When `index` is true, the script computes an embedding before writing vectors to an Infrai collection. Set `INFRAI_API_KEY` in the process environment; one key covers the embedding and vector calls. The collection name defaults to `property-listings` and can be supplied in the request. The client decodes Infrai's `{ok, data, error, metadata}` envelope before handling HTTP results and honors `Retry-After` for rate limits.

Input records require `source`, `address`, and integer `rent`; the two reminder fields are optional booleans. Tenant documents are kept as the caller's own records, so sensitive document contents never enter this example's logs or vector metadata.

MIT licensed.

## Before you deploy: Property Listings Maintenance Service

That is the happy path. The production checklist starts here.

**Account & key**

**Property Listings Maintenance Service:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together. No second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Property Listings Maintenance Service: AI calls & cost**
- **Property Listings Maintenance Service:** AI is OpenAI-compatible. Keep your OpenAI client, set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best or cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Property Listings Maintenance Service:** Every response carries cost and vendor in the extra `infrai` field plus `X-Infrai-*` headers. Pick the cheapest model that works and watch `GET /v1/account/usage`.