# IT System Outage Procedure

**Document ID:** OPS-IT-001
**Version:** 1.0
**Department:** IT Operations and Control Room Support
**Document Type:** Outage Procedure
**Effective Date:** 2026-01-01
**Classification:** Synthetic demo document

## 1. Purpose

This procedure defines how operations and IT teams must respond when a critical monitoring, reporting or control support system becomes unavailable. The objective is to maintain continuity, activate manual fallback, communicate clearly and validate recovery.

## 2. Monitoring System Outage

A monitoring system outage occurs when operators cannot access real-time dashboards, alarms, trends, reports or asset status information. Examples include dashboard unavailable, alarm history not loading, real-time values frozen, remote assets not updating, authentication failure, reporting database unavailable or network connectivity failure.

When an outage is detected, the operator must confirm whether one or multiple users are affected, check whether local control panels remain available, notify the shift supervisor, contact IT support, record detection time, identify affected assets and activate manual fallback if required. If safety-critical monitoring is affected, the operations manager must be notified immediately.

## 3. Manual Fallback Process

Manual fallback must be activated when the monitoring system is unavailable and operations cannot rely on automatic visibility. The shift supervisor must assign personnel to collect operational status using local panel readings, field inspections, radio communication, phone confirmation, manual log sheets, backup dashboard, direct equipment inspection or local alarm indicators.

During manual fallback, operators must record time of each check, asset checked, observed status, name of person reporting, abnormal conditions and follow-up action. For critical assets, status must be checked at least every 30 minutes until the monitoring system is restored.

## 4. Communication Protocol

The shift supervisor must send an initial outage notification within 15 minutes of confirming a multi-user or operationally relevant system outage. The notification must include affected system, time detected, operational impact, whether manual fallback is active, IT ticket number and next update time.

IT support must provide updates at least every 30 minutes for high-impact outages. If the outage affects external reporting or customer-facing service, the operations manager must approve external communication. Communication must avoid speculation about root cause until confirmed by IT support.

## 5. Recovery Validation

The system must not be declared recovered only because the login page is available. Recovery validation must confirm that users can log in, real-time values are updating, alarm data is visible, historical trends are accessible, reports can be generated, remote asset communication is restored, data gaps are classified and operators confirm usability.

The shift supervisor must compare system data with at least one independent field or local panel reading before closing manual fallback. If data is missing during the outage, the gap must be documented. The outage can be closed only when the shift supervisor and IT support both confirm recovery.
