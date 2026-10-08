from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
import statistics

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

DATA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "q-vercel-latency.json"
)

with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)


class AnalyticsRequest(BaseModel):
    regions: list[str]
    threshold_ms: float


@app.post("/")
def analytics(request: AnalyticsRequest):
    results = []

    for region in request.regions:
        rows = [
            row for row in data
            if row["region"] == region
        ]

        latencies = sorted(
            row["latency_ms"] for row in rows
        )

        uptimes = [
            row["uptime_pct"] for row in rows
        ]

        n = len(latencies)

        # 95th percentile using linear interpolation
        position = (n - 1) * 0.95
        lower = int(position)
        upper = min(lower + 1, n - 1)
        fraction = position - lower

        p95 = (
            latencies[lower]
            + fraction * (latencies[upper] - latencies[lower])
        )

        results.append({
            "region": region,
            "avg_latency": statistics.mean(latencies),
            "p95_latency": p95,
            "avg_uptime": statistics.mean(uptimes),
            "breaches": sum(
                latency > request.threshold_ms
                for latency in latencies
            )
        })

    return results
