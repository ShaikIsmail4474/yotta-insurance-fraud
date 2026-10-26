# AI Prompt History

## Purpose

This document records the main topics and representative examples of AI assistance used while developing the Insurance Fraud Detection and Investigation project for the YottaFlex challenge.

This is a summary, not a complete verbatim transcript of all prompts and AI responses. The examples below describe the types of assistance used and are not presented as an exhaustive conversation history.

## AI Assistance and Representative Prompt Examples

### 1. Project Planning and Architecture

**Purpose:** Understand the challenge requirements and organize the implementation into manageable components.

**Representative prompt:**
> Help me plan an end-to-end synthetic insurance fraud detection and investigation pipeline based on the challenge requirements. Identify the main entities, workflow, validation requirements, outputs, and limitations.

### 2. Synthetic Data Generation

**Purpose:** Design reproducible synthetic insurance records and relationships.

**Representative prompt:**
> Help me design a Python data generator for claimants, policies, incidents, providers, claims, invoices, payments, and relationship edges. Use deterministic identifiers, a fixed random seed, and controlled suspicious patterns.

### 3. Data Validation and Database Design

**Purpose:** Check data consistency and build a relational SQLite database.

**Representative prompt:**
> Help me validate primary-key uniqueness, foreign-key references, relationship types, date ordering, financial amounts, and consistency between claims, invoices, and payments. Help me design a SQLite schema with appropriate constraints and indexes.

### 4. Data Export and Reproducibility

**Purpose:** Export generated records and verify repeatability.

**Representative prompt:**
> Help me export the generated datasets to CSV and JSON and create a reproducibility check that compares row counts and checksums across runs using the same random seed.

### 5. Explainable Fraud-Risk Scoring

**Purpose:** Build a transparent baseline detector using operational data.

**Representative prompt:**
> Help me implement explainable rule-based claim risk scoring using observable indicators such as shared contact details, provider activity, and recorded relationships. Keep ground-truth labels separate from the detector's input features and provide evidence for each risk score.

### 6. Evaluation and Negative Scenarios

**Purpose:** Test data integrity and measure performance against synthetic ground truth.

**Representative prompt:**
> Help me write tests for invalid policy references, payments exceeding approved amounts, duplicate invoices across claimants, missing relationship edges, and benign shared addresses. Help me evaluate predictions using confusion-matrix counts, precision, recall, and F1 score.

### 7. Investigation Reporting

**Purpose:** Make risk results useful for manual investigation.

**Representative prompt:**
> Help me create an investigation report that combines risk scores with relevant claim, claimant, provider, invoice, payment, and relationship evidence. Clearly distinguish investigation indicators from proof of fraud.

### 8. Documentation and Submission Preparation

**Purpose:** Document the implementation, setup instructions, limitations, and verification process.

**Representative prompt:**
> Review the project README, data model, data dictionary, SQL schema, test instructions, and limitations for consistency with the implementation. Help me prepare the repository for a reproducible public GitHub submission.

## Verification and Limitations

AI assistance was used for project planning, coding guidance, debugging, testing, evaluation, and documentation. The project code and outputs should be reviewed and verified by the project owner.

The representative prompts in this document summarize the types of assistance used. They are not claimed to be exact quotations from the original conversations. This file is not a complete export of all prompts or AI responses.

The project owner is responsible for understanding the implementation, explaining design decisions, verifying results, and acknowledging limitations. The current detector is a synthetic-data baseline and has not been validated on real-world insurance fraud data.
