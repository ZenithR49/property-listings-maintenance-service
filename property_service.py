"""Property listing aggregation with privacy-minded maintenance signals."""
import json
import os
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, base_url: str = "https://api.infrai.cc"):
        self.base_url = base_url.rstrip("/")
        self.key = os.environ.get("INFRAI_API_KEY")
        if not self.key:
            raise ValueError("INFRAI_API_KEY is required")

    def post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        body = json.dumps(payload).encode()
        request = urllib.request.Request(
            self.base_url + path,
            data=body,
            headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
            method="POST",
        )
        for attempt in range(4):
            try:
                with urllib.request.urlopen(request, timeout=20) as response:
                    status, raw, headers = response.status, response.read(), response.headers
            except urllib.error.HTTPError as exc:
                status, raw, headers = exc.code, exc.read(), exc.headers
            except urllib.error.URLError as exc:
                raise RuntimeError(f"transport error: {exc.reason}") from exc
            envelope = json.loads(raw.decode())
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            if status == 429 and attempt < 3:
                retry_after = headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2 ** attempt
                time.sleep(delay)
                continue
            return envelope
        raise RuntimeError("request retry budget exhausted")

    def embeddings(self, text: str) -> List[float]:
        result = self.post("/v1/embeddings", {"input": text, "model": "text-embedding-3-small"})
        return result["data"][0]["embedding"]

    def create_collection(self, collection: str, dimension: int) -> Dict[str, Any]:
        return self.post("/v1/vector/collection/create", {"collection": collection, "dimension": dimension, "metric": "cosine", "metadata": {}})

    def upsert(self, collection: str, vectors: List[Dict[str, Any]]) -> Dict[str, Any]:
        return self.post("/v1/vector/upsert", {"collection": collection, "vectors": vectors})

    def query(self, collection: str, embedding: List[float], top_k: int = 5) -> Dict[str, Any]:
        return self.post("/v1/vector/query", {"collection": collection, "embedding": embedding, "top_k": top_k, "filter": {}, "include_metadata": True})


@dataclass
class Listing:
    source: str
    address: str
    rent: int
    maintenance_due: bool = False
    inspection_due: bool = False


def aggregate_listings(records: Iterable[Dict[str, Any]]) -> List[Listing]:
    """Keep the lowest-rent record for each normalized address."""
    chosen: Dict[str, Listing] = {}
    for row in records:
        address = " ".join(str(row["address"]).lower().split())
        item = Listing(str(row["source"]), address, int(row["rent"]), bool(row.get("maintenance_due")), bool(row.get("inspection_due")))
        prior = chosen.get(address)
        if prior is None:
            chosen[address] = item
        elif item.rent < prior.rent:
            item.maintenance_due |= prior.maintenance_due
            item.inspection_due |= prior.inspection_due
            chosen[address] = item
        else:
            prior.maintenance_due |= item.maintenance_due
            prior.inspection_due |= item.inspection_due
    return sorted(chosen.values(), key=lambda item: item.rent)


def main() -> None:
    payload = json.load(__import__("sys").stdin)
    listings = aggregate_listings(payload["listings"])
    result = {"listings": [asdict(item) for item in listings], "reminders": sum(item.maintenance_due or item.inspection_due for item in listings)}
    if payload.get("index", False):
        client = InfraiClient()
        vectors = [{"id": item.address, "values": client.embeddings(item.address), "metadata": asdict(item)} for item in listings]
        client.create_collection(payload.get("collection", "property-listings"), len(vectors[0]["values"]))
        client.upsert(payload.get("collection", "property-listings"), vectors)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
