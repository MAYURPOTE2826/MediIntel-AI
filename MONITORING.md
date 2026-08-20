# MediIntel AI Monitoring Setup

This document describes the monitoring stack used in MediIntel AI, which utilizes Prometheus for metrics collection and Grafana for visualization.

## Architecture

*   **Prometheus**: Scrapes metrics from the Flask backend via the `/metrics` endpoint.
*   **Grafana**: Connects to Prometheus as a data source to display real-time analytics.
*   **Alertmanager**: Triggers alerts based on Prometheus rules.

## Getting Started

To spin up the monitoring infrastructure:

1.  Navigate to the project root directory.
2.  Run the Docker Compose file:
    ```bash
    docker-compose up -d
    ```
3.  Access Grafana at `http://localhost:3000` (Default login: `admin` / `admin`).
4.  Access Prometheus directly at `http://localhost:9090` (useful for raw PromQL queries).
5.  Access Alertmanager at `http://localhost:9093`.

The Flask backend must be running locally on port 5000 for Prometheus to scrape it (`host.docker.internal:5000`). Make sure you have the python environment set up.

## Monitored Metrics

The dashboard tracks the following 7 key metrics:
1.  **API Response Times**: Target is <500ms.
2.  **OCR Accuracy Rate (%)**: Accuracy from the PaddleOCR confidence scores.
3.  **AI Confidence Distribution**: Confidence percentiles from the Image Classification models.
4.  **User Upload Volume**: Bytes uploaded, grouped by file type.
5.  **Error Rates by Module**: HTTP 5xx errors per endpoint path.
6.  **Database Query Performance**: Latency of SQLAlchemy database queries.
7.  **AI Model Inference Time**: Execution time for AI document classification.

## Configured Alerts

*   **LowOcrAccuracy**: Triggers if OCR accuracy drops below 85% for 1 minute.
*   **HighApiResponseTime**: Triggers if the average API response time exceeds 2 seconds.
*   **HighErrorRate**: Triggers if the 5xx error rate exceeds 1% of total requests.

## Safety & Compliance

*   **PII**: No Personally Identifiable Information (PII) is logged in Prometheus labels or metrics. We track aggregate statistics, module names, and error types, but never user IDs, names, or file contents.
*   **Audit Logging**: The backend's standard audit log still runs on all data access and file uploads, distinct from Prometheus metrics.
*   **API Key Rotation**:
    *   **Grafana**: You should manually rotate the Grafana Admin credentials and any Service Account API keys generated inside Grafana every 30 days.
    *   **MediIntel Backend**: Ensure any backend API tokens (e.g. JWT secrets, AWS Keys) are rotated monthly per company policy. The monitoring stack will not impact these keys.
