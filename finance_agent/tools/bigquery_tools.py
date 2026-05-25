from __future__ import annotations

import os
from typing import Any, Optional

from google.cloud import bigquery


PROJECT_ID = os.getenv("BQ_PROJECT_ID", "YOUR_PROJECT_ID")
DATASET_ID = os.getenv("BQ_DATASET_ID", "finance_analytics")
TABLE_ID = os.getenv("BQ_TABLE_ID", "finance_variance_fact")

FULL_TABLE_NAME = f"`{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`"


def _get_bq_client() -> bigquery.Client:
    return bigquery.Client(project=PROJECT_ID)


def _validate_period_inputs(
    fiscal_year: int,
    fiscal_period: int,
    limit: int,
) -> Optional[dict[str, Any]]:
    if fiscal_year < 2000 or fiscal_year > 2100:
        return {
            "error": True,
            "message": "fiscal_year must be between 2000 and 2100.",
        }

    if fiscal_period < 1 or fiscal_period > 12:
        return {
            "error": True,
            "message": "fiscal_period must be between 1 and 12.",
        }

    if limit < 1 or limit > 100:
        return {
            "error": True,
            "message": "limit must be between 1 and 100.",
        }

    return None


def _validate_trend_inputs(
    fiscal_year: int,
    fiscal_period: int,
    lookback_periods: int,
    limit: int,
) -> Optional[dict[str, Any]]:
    if fiscal_year < 2000 or fiscal_year > 2100:
        return {
            "error": True,
            "message": "fiscal_year must be between 2000 and 2100.",
        }

    if fiscal_period < 1 or fiscal_period > 12:
        return {
            "error": True,
            "message": "fiscal_period must be between 1 and 12.",
        }

    if lookback_periods < 1 or lookback_periods > 12:
        return {
            "error": True,
            "message": "lookback_periods must be between 1 and 12.",
        }

    if limit < 1 or limit > 100:
        return {
            "error": True,
            "message": "limit must be between 1 and 100.",
        }

    return None


def _build_common_filters(
    department_name: Optional[str] = None,
    cost_center_name: Optional[str] = None,
    pnl_category: Optional[str] = None,
) -> tuple[list[str], list[bigquery.ScalarQueryParameter]]:
    where_clauses: list[str] = []
    query_params: list[bigquery.ScalarQueryParameter] = []

    if department_name:
        where_clauses.append("department_name = @department_name")
        query_params.append(
            bigquery.ScalarQueryParameter("department_name", "STRING", department_name)
        )

    if cost_center_name:
        where_clauses.append("cost_center_name = @cost_center_name")
        query_params.append(
            bigquery.ScalarQueryParameter("cost_center_name", "STRING", cost_center_name)
        )

    if pnl_category:
        where_clauses.append("pnl_category = @pnl_category")
        query_params.append(
            bigquery.ScalarQueryParameter("pnl_category", "STRING", pnl_category)
        )

    return where_clauses, query_params


def get_biggest_overspends(
    fiscal_year: int,
    fiscal_period: int,
    limit: int = 5,
    department_name: Optional[str] = None,
    cost_center_name: Optional[str] = None,
    pnl_category: Optional[str] = None,
) -> dict[str, Any]:
    """
    Returns top unfavorable variances for a fiscal period using deterministic BigQuery logic.
    """

    validation_error = _validate_period_inputs(
        fiscal_year=fiscal_year,
        fiscal_period=fiscal_period,
        limit=limit,
    )
    if validation_error:
        return validation_error

    client = _get_bq_client()

    extra_filters, extra_params = _build_common_filters(
        department_name=department_name,
        cost_center_name=cost_center_name,
        pnl_category=pnl_category,
    )

    where_clauses = [
        "fiscal_year = @fiscal_year",
        "fiscal_period = @fiscal_period",
        "variance_direction = @variance_direction",
    ] + extra_filters

    query_params: list[bigquery.ScalarQueryParameter] = [
        bigquery.ScalarQueryParameter("fiscal_year", "INT64", fiscal_year),
        bigquery.ScalarQueryParameter("fiscal_period", "INT64", fiscal_period),
        bigquery.ScalarQueryParameter("variance_direction", "STRING", "Unfavorable"),
        bigquery.ScalarQueryParameter("limit", "INT64", limit),
    ] + extra_params

    sql = f"""
    SELECT
      fiscal_year,
      fiscal_period,
      fiscal_month_start_date,
      budget_version,
      gl_account_id,
      gl_account_name,
      pnl_category,
      account_rollup_l1,
      cost_center_id,
      cost_center_name,
      department_name,
      region,
      actual_amount,
      budget_amount,
      txn_count,
      variance_amount,
      variance_direction,
      variance_pct,
      is_material,
      risk_classification
    FROM {FULL_TABLE_NAME}
    WHERE {" AND ".join(where_clauses)}
    ORDER BY variance_amount DESC, gl_account_name ASC
    LIMIT @limit
    """

    job_config = bigquery.QueryJobConfig(query_parameters=query_params)

    try:
        query_job = client.query(sql, job_config=job_config)
        rows_iter = query_job.result()

        rows: list[dict[str, Any]] = []
        for row in rows_iter:
            fiscal_month_start_date = row.get("fiscal_month_start_date")

            rows.append(
                {
                    "fiscal_year": row.get("fiscal_year"),
                    "fiscal_period": row.get("fiscal_period"),
                    "fiscal_month_start_date": (
                        fiscal_month_start_date.isoformat()
                        if fiscal_month_start_date
                        else None
                    ),
                    "budget_version": row.get("budget_version"),
                    "gl_account_id": row.get("gl_account_id"),
                    "gl_account_name": row.get("gl_account_name"),
                    "pnl_category": row.get("pnl_category"),
                    "account_rollup_l1": row.get("account_rollup_l1"),
                    "cost_center_id": row.get("cost_center_id"),
                    "cost_center_name": row.get("cost_center_name"),
                    "department_name": row.get("department_name"),
                    "region": row.get("region"),
                    "actual_amount": row.get("actual_amount"),
                    "budget_amount": row.get("budget_amount"),
                    "txn_count": row.get("txn_count"),
                    "variance_amount": row.get("variance_amount"),
                    "variance_direction": row.get("variance_direction"),
                    "variance_pct": row.get("variance_pct"),
                    "is_material": row.get("is_material"),
                    "risk_classification": row.get("risk_classification"),
                }
            )

        return {
            "error": False,
            "metric": "top_overspends",
            "source_table": f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}",
            "fiscal_year": fiscal_year,
            "fiscal_period": fiscal_period,
            "filters": {
                "department_name": department_name,
                "cost_center_name": cost_center_name,
                "pnl_category": pnl_category,
            },
            "row_count": len(rows),
            "rows": rows,
        }

    except Exception as exc:
        return {
            "error": True,
            "message": f"BigQuery query failed: {str(exc)}",
        }


def get_top_drivers(
    fiscal_year: int,
    fiscal_period: int,
    limit: int = 5,
    department_name: Optional[str] = None,
    cost_center_name: Optional[str] = None,
    pnl_category: Optional[str] = None,
) -> dict[str, Any]:
    """
    Returns the top contributors to unfavorable variance for a fiscal period.

    In v1, "drivers" means the largest unfavorable contributors ranked by variance_amount.
    This is a deterministic contributor-ranking tool, not a causal inference tool.
    """

    validation_error = _validate_period_inputs(
        fiscal_year=fiscal_year,
        fiscal_period=fiscal_period,
        limit=limit,
    )
    if validation_error:
        return validation_error

    client = _get_bq_client()

    extra_filters, extra_params = _build_common_filters(
        department_name=department_name,
        cost_center_name=cost_center_name,
        pnl_category=pnl_category,
    )

    where_clauses = [
        "fiscal_year = @fiscal_year",
        "fiscal_period = @fiscal_period",
        "variance_direction = @variance_direction",
    ] + extra_filters

    query_params: list[bigquery.ScalarQueryParameter] = [
        bigquery.ScalarQueryParameter("fiscal_year", "INT64", fiscal_year),
        bigquery.ScalarQueryParameter("fiscal_period", "INT64", fiscal_period),
        bigquery.ScalarQueryParameter("variance_direction", "STRING", "Unfavorable"),
        bigquery.ScalarQueryParameter("limit", "INT64", limit),
    ] + extra_params

    sql = f"""
    SELECT
      fiscal_year,
      fiscal_period,
      fiscal_month_start_date,
      budget_version,
      gl_account_id,
      gl_account_name,
      pnl_category,
      account_rollup_l1,
      cost_center_id,
      cost_center_name,
      department_name,
      region,
      actual_amount,
      budget_amount,
      txn_count,
      variance_amount,
      variance_direction,
      variance_pct,
      is_material,
      risk_classification
    FROM {FULL_TABLE_NAME}
    WHERE {" AND ".join(where_clauses)}
    ORDER BY variance_amount DESC, gl_account_name ASC
    LIMIT @limit
    """

    job_config = bigquery.QueryJobConfig(query_parameters=query_params)

    try:
        query_job = client.query(sql, job_config=job_config)
        rows_iter = query_job.result()

        rows: list[dict[str, Any]] = []
        for row in rows_iter:
            fiscal_month_start_date = row.get("fiscal_month_start_date")

            rows.append(
                {
                    "driver_type": "gl_account_cost_center",
                    "fiscal_year": row.get("fiscal_year"),
                    "fiscal_period": row.get("fiscal_period"),
                    "fiscal_month_start_date": (
                        fiscal_month_start_date.isoformat()
                        if fiscal_month_start_date
                        else None
                    ),
                    "budget_version": row.get("budget_version"),
                    "gl_account_id": row.get("gl_account_id"),
                    "gl_account_name": row.get("gl_account_name"),
                    "pnl_category": row.get("pnl_category"),
                    "account_rollup_l1": row.get("account_rollup_l1"),
                    "cost_center_id": row.get("cost_center_id"),
                    "cost_center_name": row.get("cost_center_name"),
                    "department_name": row.get("department_name"),
                    "region": row.get("region"),
                    "actual_amount": row.get("actual_amount"),
                    "budget_amount": row.get("budget_amount"),
                    "txn_count": row.get("txn_count"),
                    "variance_amount": row.get("variance_amount"),
                    "variance_direction": row.get("variance_direction"),
                    "variance_pct": row.get("variance_pct"),
                    "is_material": row.get("is_material"),
                    "risk_classification": row.get("risk_classification"),
                }
            )

        return {
            "error": False,
            "metric": "top_drivers",
            "source_table": f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}",
            "driver_definition": "largest unfavorable contributors ranked by variance_amount",
            "fiscal_year": fiscal_year,
            "fiscal_period": fiscal_period,
            "filters": {
                "department_name": department_name,
                "cost_center_name": cost_center_name,
                "pnl_category": pnl_category,
            },
            "row_count": len(rows),
            "rows": rows,
        }

    except Exception as exc:
        return {
            "error": True,
            "message": f"BigQuery query failed: {str(exc)}",
        }


def get_trend_analysis(
    fiscal_year: int,
    fiscal_period: int,
    lookback_periods: int = 1,
    limit: int = 5,
    department_name: Optional[str] = None,
    cost_center_name: Optional[str] = None,
    pnl_category: Optional[str] = None,
) -> dict[str, Any]:
    """
    Returns the largest unfavorable variance changes versus a prior fiscal period.

    v1 scope:
    - same fiscal year only
    - compares requested fiscal_period to prior period within the same year
    - supports lookback_periods, but only if the prior period remains >= 1
    - "trend shift" is represented as the largest increase in unfavorable variance_amount
      versus the selected prior period

    This is deterministic period-over-period comparison, not statistical anomaly detection.
    """

    validation_error = _validate_trend_inputs(
        fiscal_year=fiscal_year,
        fiscal_period=fiscal_period,
        lookback_periods=lookback_periods,
        limit=limit,
    )
    if validation_error:
        return validation_error

    prior_period = fiscal_period - lookback_periods
    if prior_period < 1:
        return {
            "error": True,
            "message": "lookback_periods results in a prior period earlier than 1 for the same fiscal year. Use a smaller lookback_periods value.",
        }

    client = _get_bq_client()

    extra_filters, extra_params = _build_common_filters(
        department_name=department_name,
        cost_center_name=cost_center_name,
        pnl_category=pnl_category,
    )

    current_filters = [
        "curr.fiscal_year = @fiscal_year",
        "curr.fiscal_period = @fiscal_period",
    ] + [
        f"curr.{clause}" for clause in extra_filters
    ]

    query_params: list[bigquery.ScalarQueryParameter] = [
        bigquery.ScalarQueryParameter("fiscal_year", "INT64", fiscal_year),
        bigquery.ScalarQueryParameter("fiscal_period", "INT64", fiscal_period),
        bigquery.ScalarQueryParameter("prior_period", "INT64", prior_period),
        bigquery.ScalarQueryParameter("limit", "INT64", limit),
    ] + extra_params

    sql = f"""
    WITH current_period AS (
      SELECT
        fiscal_year,
        fiscal_period,
        gl_account_id,
        gl_account_name,
        cost_center_id,
        cost_center_name,
        department_name,
        pnl_category,
        account_rollup_l1,
        region,
        variance_amount,
        variance_direction,
        variance_pct,
        actual_amount,
        budget_amount,
        txn_count,
        is_material,
        risk_classification
      FROM {FULL_TABLE_NAME} curr
      WHERE {" AND ".join(current_filters)}
    ),
    prior_period AS (
      SELECT
        fiscal_year,
        fiscal_period,
        gl_account_id,
        cost_center_id,
        variance_amount
      FROM {FULL_TABLE_NAME}
      WHERE fiscal_year = @fiscal_year
        AND fiscal_period = @prior_period
    )
    SELECT
      curr.fiscal_year,
      curr.fiscal_period,
      @prior_period AS prior_fiscal_period,
      curr.gl_account_id,
      curr.gl_account_name,
      curr.cost_center_id,
      curr.cost_center_name,
      curr.department_name,
      curr.pnl_category,
      curr.account_rollup_l1,
      curr.region,
      curr.actual_amount,
      curr.budget_amount,
      curr.txn_count,
      curr.variance_amount AS current_variance_amount,
      curr.variance_direction AS current_variance_direction,
      curr.variance_pct AS current_variance_pct,
      curr.is_material,
      curr.risk_classification,
      prior.variance_amount AS prior_variance_amount,
      (curr.variance_amount - COALESCE(prior.variance_amount, 0)) AS variance_delta_vs_prior
    FROM current_period curr
    LEFT JOIN prior_period prior
      ON curr.gl_account_id = prior.gl_account_id
     AND curr.cost_center_id = prior.cost_center_id
    WHERE curr.variance_direction = 'Unfavorable'
    ORDER BY variance_delta_vs_prior DESC, curr.gl_account_name ASC
    LIMIT @limit
    """

    job_config = bigquery.QueryJobConfig(query_parameters=query_params)

    try:
        query_job = client.query(sql, job_config=job_config)
        rows_iter = query_job.result()

        rows: list[dict[str, Any]] = []
        for row in rows_iter:
            rows.append(
                {
                    "fiscal_year": row.get("fiscal_year"),
                    "fiscal_period": row.get("fiscal_period"),
                    "prior_fiscal_period": row.get("prior_fiscal_period"),
                    "gl_account_id": row.get("gl_account_id"),
                    "gl_account_name": row.get("gl_account_name"),
                    "cost_center_id": row.get("cost_center_id"),
                    "cost_center_name": row.get("cost_center_name"),
                    "department_name": row.get("department_name"),
                    "pnl_category": row.get("pnl_category"),
                    "account_rollup_l1": row.get("account_rollup_l1"),
                    "region": row.get("region"),
                    "actual_amount": row.get("actual_amount"),
                    "budget_amount": row.get("budget_amount"),
                    "txn_count": row.get("txn_count"),
                    "current_variance_amount": row.get("current_variance_amount"),
                    "prior_variance_amount": row.get("prior_variance_amount"),
                    "variance_delta_vs_prior": row.get("variance_delta_vs_prior"),
                    "current_variance_direction": row.get("current_variance_direction"),
                    "current_variance_pct": row.get("current_variance_pct"),
                    "is_material": row.get("is_material"),
                    "risk_classification": row.get("risk_classification"),
                }
            )

        return {
            "error": False,
            "metric": "trend_analysis",
            "source_table": f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}",
            "trend_definition": "largest increase in unfavorable variance_amount versus prior fiscal period within the same fiscal year",
            "fiscal_year": fiscal_year,
            "fiscal_period": fiscal_period,
            "prior_fiscal_period": prior_period,
            "lookback_periods": lookback_periods,
            "filters": {
                "department_name": department_name,
                "cost_center_name": cost_center_name,
                "pnl_category": pnl_category,
            },
            "row_count": len(rows),
            "rows": rows,
        }

    except Exception as exc:
        return {
            "error": True,
            "message": f"BigQuery query failed: {str(exc)}",
        }