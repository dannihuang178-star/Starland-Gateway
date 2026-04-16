# Starland Gateway

A custom multi-provider LLM gateway built to support persona-aware conversation workflows, long-context management, and memory-oriented orchestration across different front ends.

## Overview

Starland Gateway is a personal infrastructure project designed to sit between user-facing applications and multiple language model providers.  
It was built to solve a practical problem: how to maintain continuity, control, and long-horizon conversational quality across interfaces, providers, and context limits.

Instead of sending raw requests directly from the front end to a model API, the gateway adds a structured orchestration layer for routing, prompt injection, context compression, streaming, and memory-aware processing.

This public repository is a project showcase rather than the full production codebase.  
Some implementation details remain private because they include personal workflow logic, deployment-specific configuration, and private memory architecture.

## Core Goals

- Route requests across multiple LLM providers through a unified interface
- Support persona/system prompt injection outside the frontend layer
- Manage long conversations through summarization and context budgeting
- Preserve recent conversational continuity while compressing older history
- Enable memory-aware workflows without exposing private user data
- Stream responses efficiently to the client layer

## Key Features

### 1. Multi-provider model routing
The gateway separates provider selection from application logic, making it possible to work with different model backends through a single service layer.

### 2. Persona-aware prompt orchestration
System-level instructions and persona logic can be injected centrally, rather than being tied to a single frontend.

### 3. Context budgeting and compression
To handle long conversations, the gateway applies context limits, keeps recent turns intact, and compresses older exchanges into summaries.

### 4. Layered summarization
The system is designed to support short-term, recent, and longer-horizon summary layers, helping preserve continuity without sending the entire conversation history upstream.

### 5. Streaming response support
The gateway supports streaming responses to improve responsiveness and create a smoother user experience.

### 6. Memory-oriented architecture
The broader design includes structured hooks for long-term memory workflows, summary storage, and retrieval-aware response generation.

## Why I Built It

Most chat interfaces treat model calls as isolated requests.  
That works for simple prompting, but it breaks down when the goal is continuity across long conversations, multiple providers, and persistent interaction styles.

I built Starland Gateway to explore a different approach: treating the model layer as part of a larger conversational system rather than a stateless API call.

This project reflects my interest in:
- LLM application architecture
- context management
- memory systems
- prompt orchestration
- practical infrastructure for human-centered AI interaction

## High-Level Architecture

```text
Frontend / Client
        ↓
   Starland Gateway
        ↓
 ┌───────────────────────┐
 │ Request preprocessing │
 │ - prompt injection    │
 │ - context budgeting   │
 │ - summary insertion   │
 └───────────────────────┘
        ↓
 ┌───────────────────────┐
 │ Model routing layer   │
 │ - provider selection  │
 │ - model normalization │
 └───────────────────────┘
        ↓
   LLM Provider APIs
        ↓
 ┌───────────────────────┐
 │ Post-processing layer │
 │ - streaming           │
 │ - logging             │
 │ - memory hooks        │
 └───────────────────────┘
        ↓
Frontend / Storage / Memory Services
