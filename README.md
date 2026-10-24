# TrendPulse

AI Operating Intelligence Platform for Small Clothing Brands.

## Current Development Phase

Phase 1 - Data Ingestion and Processing

## Team Structure

- Data Intelligence / MLF
- Backend / Database / INS
- DAVA / Frontend

## Core Pipeline

Business Data
    ?
File Upload
    ?
Data Processing
    ?
Validation
    ?
Normalization
    ?
Database
    ?
ML + DAVA + AI


## Data Intelligence V4

The data engine now uses a layered architecture:

Raw data -> semantic mapping -> cleaning/audit -> validation ->
ensemble anomaly detection -> profiling -> deterministic business insights ->
optional LLM reasoning -> backend-ready JSON.

The LLM layer is advisory only. It never directly mutates business data.
Set `OPENAI_API_KEY` to enable the optional OpenAI reasoning adapter; otherwise
the pipeline runs fully offline with deterministic fallback reasoning.
