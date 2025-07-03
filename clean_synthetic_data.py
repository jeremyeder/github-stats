#!/usr/bin/env python3
"""
Remove synthetic timestamp data and keep only interactions with real GitHub timestamps.
Convert stars to summary counters instead of individual interactions.
"""

from datetime import datetime
from dateutil import parser as date_parser

from github_stats.utils.database import get_db
from github_stats.models.interactions import Interaction, InteractionType


def has_real_timestamp(interaction):
    """Check if an interaction has a real GitHub timestamp in extra_data."""
    if not interaction.extra_data:
        return False
    
    # Check for various timestamp fields from GitHub API
    timestamp_fields = [
        'created_at', 'updated_at', 'starred_at', 'committed_date',
        'authored_date', 'pushed_at', 'published_at'
    ]
    
    for field in timestamp_fields:
        if field in interaction.extra_data and interaction.extra_data[field]:
            try:
                date_parser.parse(interaction.extra_data[field])
                return True
            except (ValueError, TypeError):
                continue
    
    return False


def apply_real_timestamp(interaction):
    """Apply the real GitHub timestamp from extra_data if available."""
    if not interaction.extra_data:
        return False
    
    # Priority order for timestamp fields
    timestamp_fields = [
        'created_at', 'committed_date', 'authored_date', 
        'starred_at', 'updated_at', 'pushed_at', 'published_at'
    ]
    
    for field in timestamp_fields:
        if field in interaction.extra_data and interaction.extra_data[field]:
            try:
                real_timestamp = date_parser.parse(interaction.extra_data[field])
                interaction.timestamp = real_timestamp
                return True
            except (ValueError, TypeError):
                continue
    
    return False


def clean_synthetic_data():
    """Remove all synthetic data and keep only real GitHub timestamps."""
    with get_db() as session:
        print("🔍 Analyzing interaction data...")
        
        all_interactions = session.query(Interaction).all()
        print(f"Found {len(all_interactions)} total interactions")
        
        # Categorize interactions
        real_timestamp_interactions = []
        synthetic_interactions = []
        
        for interaction in all_interactions:
            if has_real_timestamp(interaction):
                if apply_real_timestamp(interaction):
                    real_timestamp_interactions.append(interaction)
                else:
                    synthetic_interactions.append(interaction)
            else:
                synthetic_interactions.append(interaction)
        
        print(f"📊 Analysis complete:")
        print(f"  - Real timestamps: {len(real_timestamp_interactions)}")
        print(f"  - Synthetic/missing timestamps: {len(synthetic_interactions)}")
        
        # Show breakdown by type
        print(f"\n📋 Breakdown by interaction type:")
        
        real_by_type = {}
        synthetic_by_type = {}
        
        for interaction in real_timestamp_interactions:
            itype = interaction.type.value
            real_by_type[itype] = real_by_type.get(itype, 0) + 1
        
        for interaction in synthetic_interactions:
            itype = interaction.type.value
            synthetic_by_type[itype] = synthetic_by_type.get(itype, 0) + 1
        
        all_types = set(real_by_type.keys()) | set(synthetic_by_type.keys())
        
        for itype in sorted(all_types):
            real_count = real_by_type.get(itype, 0)
            synthetic_count = synthetic_by_type.get(itype, 0)
            total = real_count + synthetic_count
            print(f"  {itype}: {real_count} real, {synthetic_count} synthetic (total: {total})")
        
        # Delete synthetic interactions
        if synthetic_interactions:
            print(f"\n🗑️  Removing {len(synthetic_interactions)} synthetic interactions...")
            
            for interaction in synthetic_interactions:
                session.delete(interaction)
            
            session.commit()
            print("✅ Synthetic interactions removed")
        else:
            print("\n✅ No synthetic interactions found")
        
        # Save real timestamp changes
        if real_timestamp_interactions:
            session.commit()
            print(f"✅ Applied real timestamps to {len(real_timestamp_interactions)} interactions")
        
        return len(real_timestamp_interactions), len(synthetic_interactions)


def create_star_summary():
    """Create a summary of star counts instead of individual interactions."""
    with get_db() as session:
        from sqlalchemy import func
        from github_stats.models.interactions import Repository
        
        # Get star counts by repository (if any stars remain)
        star_counts = session.query(
            Repository.full_name,
            func.count(Interaction.id).label('star_count')
        ).join(
            Interaction, Repository.id == Interaction.repository_id
        ).filter(
            Interaction.type == InteractionType.STAR
        ).group_by(Repository.id, Repository.full_name).all()
        
        if star_counts:
            print(f"\n⭐ Star summary by repository:")
            total_stars = 0
            for repo_name, count in star_counts:
                print(f"  {repo_name}: {count} stars")
                total_stars += count
            print(f"  Total stars: {total_stars}")
        else:
            print(f"\n⭐ No star interactions found")


def show_final_data_summary():
    """Show the final data summary after cleanup."""
    with get_db() as session:
        from sqlalchemy import func
        
        # Total interactions by type
        type_counts = session.query(
            Interaction.type,
            func.count(Interaction.id).label('count')
        ).group_by(Interaction.type).order_by(func.count(Interaction.id).desc()).all()
        
        print(f"\n📈 Final data summary:")
        total_interactions = 0
        for itype, count in type_counts:
            print(f"  {itype.value}: {count}")
            total_interactions += count
        
        print(f"  Total: {total_interactions} interactions with real timestamps")
        
        # Date range
        if total_interactions > 0:
            date_range = session.query(
                func.min(Interaction.timestamp).label('earliest'),
                func.max(Interaction.timestamp).label('latest')
            ).first()
            
            print(f"\n📅 Date range: {date_range.earliest} to {date_range.latest}")
            
            # Sample daily distribution
            daily_counts = session.query(
                func.date(Interaction.timestamp).label('date'),
                func.count(Interaction.id).label('count')
            ).group_by(func.date(Interaction.timestamp)).order_by(func.date(Interaction.timestamp).desc()).limit(10).all()
            
            if daily_counts:
                print(f"\n📊 Recent daily activity (last 10 days with data):")
                for date, count in daily_counts:
                    print(f"  {date}: {count} interactions")


def main():
    """Main function to clean synthetic data."""
    print("🧹 Starting synthetic data cleanup...")
    print("=" * 60)
    
    # Clean synthetic data
    real_count, synthetic_count = clean_synthetic_data()
    
    # Create star summary
    create_star_summary()
    
    # Show final summary
    show_final_data_summary()
    
    print("=" * 60)
    
    if synthetic_count > 0:
        print(f"✅ Cleanup complete!")
        print(f"   - Removed {synthetic_count} synthetic interactions")
        print(f"   - Kept {real_count} interactions with real GitHub timestamps")
        print(f"\n💡 Your data now contains only real GitHub interaction timestamps.")
        print(f"   Visualizations will show actual activity patterns, not synthetic data.")
    else:
        print(f"✅ No synthetic data found - your data is already clean!")
    
    print(f"\n🔄 Restart your Streamlit app to see the cleaned data.")


if __name__ == "__main__":
    main()