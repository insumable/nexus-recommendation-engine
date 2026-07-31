# 🚀 Nexus Recommendation Engine

A high-throughput, sub-5ms latency recommendation engine processing **43.8M+ user interactions** across **1.4M+ catalog items**. 

Built with **Implicit ALS**, **DuckDB**, **Redis**, and **FastAPI**, fully containerized using **Docker Compose**.

---

## 📊 System & Data Specifications

| Metric | Detail / Value |
| :--- | :--- |
| **Total Review Interactions** | `43,800,000+` records |
| **Catalog Size (Items)** | `1,400,000+` unique products |
| **User Space Dimension** | `14,700,000` total user nodes |
| **Latent Dimensions** | `64` factors |
| **Pre-cached Users (Redis)** | `10,000` active user profiles |
| **Cache Hit Latency** | `< 5 ms` (Redis In-Memory) |
| **Fallback Inference Latency** | `< 50 ms` (Dynamic Matrix Vector Product) |

### 💾 File & Storage Footprint

| File / Asset | Description | Size (Approx.) |
| :--- | :--- | :--- |
| `nexus.duckdb` | Zero-copy analytical star-schema store | `~3.2 GB` |
| `als_factors.npz` | Compressed NumPy matrix (`user_factors` & `item_factors`) | `~420 MB` |
| `mappings.pkl` | Pickled dictionary mapping user/item UUIDs to matrix indices | `~180 MB` |
| **Total Memory (RAM)** | Estimated memory footprint upon FastAPI startup | `~2.1 GB` |

---

## 📈 Offline Evaluation Results (K=10)

Evaluated across implicit feedback test splits ($K=10$ recommendations per user):

| Metric | Score | Explanation |
| :--- | :--- | :--- |
| **Precision@10** | `0.0133` | Ratio of relevant recommended items in the top-10 list. |
| **MAP@10** | `0.0064` | Mean Average Precision reflecting hit rank ordering. |
| **NDCG@10** | `0.0099` | Normalized Discounted Cumulative Gain prioritizing top positions. |
| **AUC@10** | `0.5071` | Area Under the ROC Curve across candidate ranking. |

---

## 🏗️ System Architecture

The service adopts a **Two-Tier Cache-Aside Architecture** to balance extreme low latency with dynamic fallback capability:

```mermaid
flowchart TD
    subgraph Data & Pipeline Layer
        A[Amazon Interactions Log\n43.8M Records] -->|Columnar Ingestion| B[(DuckDB Store\nnexus.duckdb)]
        B -->|Sparse CSR Matrix| C[Implicit ALS Training\n64 Latent Factors]
        C -->|Export Vectors| D[als_factors.npz & mappings.pkl]
    end

    subgraph Serving Infrastructure
        D -->|Batch Precompute| E[(Redis Cache\nnexus-redis)]
        Client([REST Client / User]) <-->|GET /recommend/{user_id}| F[FastAPI Engine\nnexus-api]
        F <-->|Fast Path < 5ms| E
        F <-->|Fallback Path < 50ms| D
    end
Analytical Ingestion: DuckDB manages zero-copy querying over the massive review dataset to build compressed SciPy CSR matrices.Batch Pre-computation: Active user factors are dot-product multiplied against all item factors and pushed into Redis as JSON strings.Cache-Aside REST API:Fast Path: Serves pre-cached JSON recommendations directly from Redis ($<5\text{ms}$).Fallback Path: Computes dynamic matrix dot-product scores for non-cached active users on the fly ($<50\text{ms}$).📂 Repository StructurePlaintextnexus-recommendation-engine/
├── als_factors.npz           # Model weights (User & Item factor matrices)
├── mappings.pkl              # Index lookup mappings (User/Item string IDs)
├── nexus.duckdb              # DuckDB analytical database file
├── cache_recommendations.py  # Script to precompute & batch load Redis cache
├── main.py                   # FastAPI application & endpoint definitions
├── requirements.txt          # Python project dependencies
├── Dockerfile                # API container spec
├── docker-compose.yml        # Multi-container orchestration (FastAPI + Redis)
└── README.md                 # Project documentation
🔌 API Reference & Endpoints1. Health CheckEndpoint: GET /healthDescription: Verifies service uptime and Redis connection status.Response:JSON{
  "status": "online",
  "redis_connected": true
}
2. User RecommendationsEndpoint: GET /recommend/{user_id}Query Parameters:k (integer, optional, default=10, min=1, max=50): Number of items to return.Sample Request:GET /recommend/AFKZENTNBQ7A7V7UXW5JJI6UGRYQ?k=5Sample Response:JSON{
  "user_id": "AFKZENTNBQ7A7V7UXW5JJI6UGRYQ",
  "source": "redis_cache",
  "latency_ms": 2.14,
  "recommendations": [
    {
      "item_id": "B00000J0E8",
      "title": "Logitech MX Master Wireless Mouse",
      "price": 99.99
    },
    {
      "item_id": "B00336E356",
      "title": "SanDisk Ultra 64GB MicroSDXC",
      "price": 14.49
    }
  ]
}
