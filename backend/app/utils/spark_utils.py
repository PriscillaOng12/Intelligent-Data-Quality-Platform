from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType
from pyspark.sql.functions import col, count, isnan, isnull, when, sum as spark_sum
from delta.tables import DeltaTable
import logging
from typing import Dict, Any, Optional, List
import os

from app.core.config import settings

logger = logging.getLogger(__name__)


class SparkManager:
    """Manages Spark session and operations for data quality platform"""
    
    def __init__(self):
        self._spark = None
        self._initialize_spark()
    
    def _initialize_spark(self):
        """Initialize Spark session with optimal configurations"""
        try:
            self._spark = SparkSession.builder \
                .appName(settings.SPARK_APP_NAME) \
                .master(settings.SPARK_MASTER) \
                .config("spark.sql.adaptive.enabled", "true") \
                .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
                .config("spark.sql.adaptive.skewJoin.enabled", "true") \
                .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
                .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
                .config("spark.sql.warehouse.dir", settings.SPARK_SQL_WAREHOUSE_DIR) \
                .config("spark.databricks.delta.retentionDurationCheck.enabled", "false") \
                .config("spark.sql.streaming.checkpointLocation", "/tmp/checkpoints") \
                .getOrCreate()
            
            # Set log level to reduce noise
            self._spark.sparkContext.setLogLevel("WARN")
            
            logger.info(f"Initialized Spark session: {self._spark.version}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Spark session: {e}")
            raise
    
    @property
    def spark(self) -> SparkSession:
        """Get Spark session"""
        if self._spark is None:
            self._initialize_spark()
        return self._spark
    
    async def load_dataset(self, dataset_id: str, format: str = "delta") -> Any:
        """Load dataset from storage"""
        try:
            if format == "delta":
                dataset_path = f"{settings.DELTA_LAKE_PATH}/{dataset_id}"
                df = self.spark.read.format("delta").load(dataset_path)
            elif format == "parquet":
                dataset_path = f"{settings.DATA_STORAGE_PATH}/{dataset_id}.parquet"
                df = self.spark.read.parquet(dataset_path)
            elif format == "csv":
                dataset_path = f"{settings.DATA_STORAGE_PATH}/{dataset_id}.csv"
                df = self.spark.read.option("header", "true").option("inferSchema", "true").csv(dataset_path)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            logger.info(f"Loaded dataset {dataset_id} with {df.count()} rows")
            return df
            
        except Exception as e:
            logger.error(f"Failed to load dataset {dataset_id}: {e}")
            raise
    
    async def save_dataset(self, df: Any, dataset_id: str, format: str = "delta", mode: str = "overwrite"):
        """Save dataset to storage"""
        try:
            if format == "delta":
                dataset_path = f"{settings.DELTA_LAKE_PATH}/{dataset_id}"
                df.write.format("delta").mode(mode).save(dataset_path)
            elif format == "parquet":
                dataset_path = f"{settings.DATA_STORAGE_PATH}/{dataset_id}.parquet"
                df.write.mode(mode).parquet(dataset_path)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            logger.info(f"Saved dataset {dataset_id} in {format} format")
            
        except Exception as e:
            logger.error(f"Failed to save dataset {dataset_id}: {e}")
            raise
    
    def calculate_basic_stats(self, df: Any) -> Dict[str, Any]:
        """Calculate basic statistics for a DataFrame"""
        try:
            stats = {
                "row_count": df.count(),
                "column_count": len(df.columns),
                "columns": []
            }
            
            for column in df.columns:
                col_stats = {
                    "name": column,
                    "data_type": str(df.schema[column].dataType),
                    "null_count": df.filter(col(column).isNull()).count(),
                    "distinct_count": df.select(column).distinct().count()
                }
                
                # Add numerical statistics for numeric columns
                if df.schema[column].dataType in [IntegerType(), DoubleType()]:
                    numeric_stats = df.select(column).describe().collect()
                    for stat in numeric_stats:
                        if stat['summary'] in ['mean', 'stddev', 'min', 'max']:
                            col_stats[stat['summary']] = float(stat[column]) if stat[column] else None
                
                stats["columns"].append(col_stats)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to calculate basic stats: {e}")
            raise
    
    def detect_data_quality_issues(self, df: Any) -> Dict[str, Any]:
        """Detect common data quality issues"""
        try:
            issues = {
                "completeness_issues": [],
                "uniqueness_issues": [],
                "validity_issues": []
            }
            
            total_rows = df.count()
            
            for column in df.columns:
                # Completeness issues
                null_count = df.filter(col(column).isNull()).count()
                null_percentage = null_count / total_rows if total_rows > 0 else 0
                
                if null_percentage > 0.1:  # More than 10% nulls
                    issues["completeness_issues"].append({
                        "column": column,
                        "null_percentage": null_percentage,
                        "severity": "high" if null_percentage > 0.5 else "medium"
                    })
                
                # Uniqueness issues (for ID-like columns)
                if "id" in column.lower():
                    distinct_count = df.select(column).distinct().count()
                    if distinct_count < total_rows:
                        duplicate_percentage = (total_rows - distinct_count) / total_rows
                        issues["uniqueness_issues"].append({
                            "column": column,
                            "duplicate_percentage": duplicate_percentage,
                            "severity": "critical"
                        })
            
            return issues
            
        except Exception as e:
            logger.error(f"Failed to detect data quality issues: {e}")
            raise
    
    def optimize_dataframe(self, df: Any) -> Any:
        """Optimize DataFrame for better performance"""
        try:
            # Cache if dataset is small to medium
            if df.count() < 1000000:  # Less than 1M rows
                df = df.cache()
            
            # Repartition based on size
            row_count = df.count()
            if row_count > 10000000:  # More than 10M rows
                optimal_partitions = min(200, max(1, row_count // 100000))
                df = df.repartition(optimal_partitions)
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to optimize DataFrame: {e}")
            return df
    
    def create_delta_table(self, df: Any, table_path: str, table_name: str = None):
        """Create Delta table from DataFrame"""
        try:
            writer = df.write.format("delta").mode("overwrite")
            
            if table_name:
                writer = writer.option("path", table_path).saveAsTable(table_name)
            else:
                writer.save(table_path)
            
            logger.info(f"Created Delta table at {table_path}")
            
        except Exception as e:
            logger.error(f"Failed to create Delta table: {e}")
            raise
    
    def merge_delta_table(self, source_df: Any, target_path: str, merge_condition: str):
        """Perform Delta table merge operation"""
        try:
            delta_table = DeltaTable.forPath(self.spark, target_path)
            
            delta_table.alias("target").merge(
                source_df.alias("source"),
                merge_condition
            ).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
            
            logger.info(f"Merged data into Delta table at {target_path}")
            
        except Exception as e:
            logger.error(f"Failed to merge Delta table: {e}")
            raise
    
    def cleanup(self):
        """Clean up Spark resources"""
        if self._spark:
            self._spark.stop()
            self._spark = None
            logger.info("Spark session stopped")


# Global Spark manager instance
spark_manager = SparkManager()
