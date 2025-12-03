#!/usr/bin/env python3
"""
One-time fix script to correct asset_type categories in the database.
This ensures Stock is classified as Equity, not Multi-Asset.
"""

import sys
from database import DatabaseManager
import config

def fix_asset_types():
    """Fix incorrect asset type categories in the database."""
    db = DatabaseManager(config.DB_CONFIG)

    print("Checking asset_types for issues...")

    # Check current Stock classification
    query = "SELECT * FROM asset_types WHERE asset_type_name = 'Stock'"
    result = db.execute_query(query, fetch=True)

    if result and result[0]['asset_category'] != 'Equity':
        print(f"Found issue: Stock is classified as '{result[0]['asset_category']}' instead of 'Equity'")
        print("Fixing...")

        # Use get_or_create_asset_type which has ON CONFLICT UPDATE logic
        asset_type_id = db.get_or_create_asset_type('Stock', 'Equity')
        print(f"✓ Updated Stock (ID: {asset_type_id}) to Equity category")

        # Verify the fix
        result = db.execute_query(query, fetch=True)
        if result[0]['asset_category'] == 'Equity':
            print("✓ Verification successful - Stock is now Equity")
        else:
            print("✗ Verification failed - Stock is still", result[0]['asset_category'])
            return False
    else:
        print("✓ Stock is already correctly classified as Equity")

    print("\nAsset type check complete!")
    db.close_all_connections()
    return True

if __name__ == '__main__':
    try:
        success = fix_asset_types()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
