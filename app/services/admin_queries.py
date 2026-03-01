"""
GraphQL query definitions for the admin service.

Each function returns a ready-to-POST request body dict: {"query": "..."}.
"""

from datetime import datetime, timezone, timedelta


def get_asset_transactions(asset_version_id: str, days: int = 30) -> dict:
    """Build the getAssetTransactionDetails query body."""
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)

    query = """
    query {
      getAssetTransactionDetails(
        asset_version_id: "%s"
        dateFilter: {
          start_date: "%s",
          end_date: "%s"
        }
        pagination: { page: 1, limit: 50 }
        transactionFilters: {
          commonFilters: { status: [], created_by: [] },
          getCurrentUserTransactions: true,
          searchFilter: ""
        }
      ) {
        meta {
          itemCount
          totalItems
          itemsPerPage
          totalPages
          currentPage
        }
        items {
          transaction_id
          initiated_by
          total_documents
          status
          total_pages
          total_pages_processed
          duration {
            days
            hours
            minutes
            seconds
            milliseconds
          }
          start_time
          error_code
          error_description
        }
      }
    }
    """ % (
        asset_version_id,
        start.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        now.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
    )

    return {"query": query}
