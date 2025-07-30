import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from typing import List, Dict, Any, Tuple, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class EnsembleAnomalyDetector:
    """
    Advanced ensemble anomaly detector combining multiple ML algorithms
    for comprehensive data quality anomaly detection
    """
    
    def __init__(self, contamination: float = 0.1, random_state: int = 42):
        self.contamination = contamination
        self.random_state = random_state
        
        # Initialize detectors
        self.isolation_forest = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_estimators=100
        )
        
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=0.95)  # Keep 95% of variance
        
        self._is_fitted = False
        
    async def detect_anomalies(self, dataset: Any) -> List[Dict[str, Any]]:
        """
        Detect anomalies in a dataset using ensemble methods
        
        Args:
            dataset: Spark DataFrame or Pandas DataFrame
            
        Returns:
            List of anomaly detection results
        """
        try:
            # Convert Spark DataFrame to Pandas if needed
            if hasattr(dataset, 'toPandas'):
                df = dataset.toPandas()
            else:
                df = dataset
            
            anomalies = []
            
            # 1. Statistical Anomalies
            statistical_anomalies = await self._detect_statistical_anomalies(df)
            anomalies.extend(statistical_anomalies)
            
            # 2. ML-based Anomalies
            ml_anomalies = await self._detect_ml_anomalies(df)
            anomalies.extend(ml_anomalies)
            
            # 3. Pattern-based Anomalies
            pattern_anomalies = await self._detect_pattern_anomalies(df)
            anomalies.extend(pattern_anomalies)
            
            # 4. Schema-based Anomalies
            schema_anomalies = await self._detect_schema_anomalies(df)
            anomalies.extend(schema_anomalies)
            
            # Sort by confidence score (descending)
            anomalies.sort(key=lambda x: x['confidence'], reverse=True)
            
            logger.info(f"Detected {len(anomalies)} anomalies")
            return anomalies
            
        except Exception as e:
            logger.error(f"Failed to detect anomalies: {e}")
            raise
    
    async def _detect_statistical_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect statistical anomalies using traditional methods"""
        anomalies = []
        
        try:
            for column in df.select_dtypes(include=[np.number]).columns:
                series = df[column].dropna()
                if len(series) < 10:  # Skip columns with too few values
                    continue
                
                # IQR-based outliers
                Q1 = series.quantile(0.25)
                Q3 = series.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outliers = series[(series < lower_bound) | (series > upper_bound)]
                
                if len(outliers) > 0:
                    outlier_percentage = len(outliers) / len(series)
                    
                    # Determine severity based on outlier percentage
                    if outlier_percentage > 0.1:
                        severity = "high"
                    elif outlier_percentage > 0.05:
                        severity = "medium"
                    else:
                        severity = "low"
                    
                    anomalies.append({
                        "type": "statistical_outlier",
                        "column_name": column,
                        "severity": severity,
                        "confidence": min(0.9, outlier_percentage * 10),
                        "description": f"Found {len(outliers)} statistical outliers in column {column}",
                        "metadata": {
                            "outlier_count": len(outliers),
                            "outlier_percentage": outlier_percentage,
                            "lower_bound": lower_bound,
                            "upper_bound": upper_bound,
                            "method": "IQR"
                        }
                    })
                
                # Z-score based outliers
                z_scores = np.abs((series - series.mean()) / series.std())
                z_outliers = series[z_scores > 3]
                
                if len(z_outliers) > 0:
                    z_outlier_percentage = len(z_outliers) / len(series)
                    
                    anomalies.append({
                        "type": "z_score_outlier",
                        "column_name": column,
                        "severity": "medium" if z_outlier_percentage > 0.01 else "low",
                        "confidence": min(0.85, z_outlier_percentage * 100),
                        "description": f"Found {len(z_outliers)} z-score outliers in column {column}",
                        "metadata": {
                            "outlier_count": len(z_outliers),
                            "outlier_percentage": z_outlier_percentage,
                            "threshold": 3,
                            "method": "z_score"
                        }
                    })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Failed to detect statistical anomalies: {e}")
            return []
    
    async def _detect_ml_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect anomalies using machine learning algorithms"""
        anomalies = []
        
        try:
            # Prepare numerical data
            numeric_df = df.select_dtypes(include=[np.number]).dropna()
            if numeric_df.empty or len(numeric_df.columns) == 0:
                return anomalies
            
            # Scale the data
            scaled_data = self.scaler.fit_transform(numeric_df)
            
            # Apply PCA if we have many features
            if len(numeric_df.columns) > 10:
                scaled_data = self.pca.fit_transform(scaled_data)
            
            # Isolation Forest detection
            if_predictions = self.isolation_forest.fit_predict(scaled_data)
            if_scores = self.isolation_forest.decision_function(scaled_data)
            
            # Find anomalies
            anomaly_indices = np.where(if_predictions == -1)[0]
            
            if len(anomaly_indices) > 0:
                # Calculate confidence scores
                anomaly_scores = if_scores[anomaly_indices]
                normalized_scores = (anomaly_scores - anomaly_scores.min()) / (anomaly_scores.max() - anomaly_scores.min() + 1e-8)
                
                anomaly_percentage = len(anomaly_indices) / len(numeric_df)
                
                # Determine severity
                if anomaly_percentage > 0.1:
                    severity = "critical"
                elif anomaly_percentage > 0.05:
                    severity = "high"
                elif anomaly_percentage > 0.02:
                    severity = "medium"
                else:
                    severity = "low"
                
                anomalies.append({
                    "type": "isolation_forest_anomaly",
                    "column_name": None,  # Multi-dimensional anomaly
                    "severity": severity,
                    "confidence": 0.8,  # Base confidence for ML methods
                    "description": f"Isolation Forest detected {len(anomaly_indices)} anomalous records",
                    "metadata": {
                        "anomaly_count": len(anomaly_indices),
                        "anomaly_percentage": anomaly_percentage,
                        "contamination": self.contamination,
                        "method": "isolation_forest",
                        "features_used": list(numeric_df.columns),
                        "anomaly_indices": anomaly_indices.tolist()[:100]  # Limit to first 100
                    }
                })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Failed to detect ML anomalies: {e}")
            return []
    
    async def _detect_pattern_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect pattern-based anomalies"""
        anomalies = []
        
        try:
            # Check for duplicate patterns
            duplicate_rows = df.duplicated().sum()
            if duplicate_rows > 0:
                duplicate_percentage = duplicate_rows / len(df)
                
                if duplicate_percentage > 0.1:
                    severity = "high"
                elif duplicate_percentage > 0.05:
                    severity = "medium"
                else:
                    severity = "low"
                
                anomalies.append({
                    "type": "duplicate_pattern",
                    "column_name": None,
                    "severity": severity,
                    "confidence": 0.9,
                    "description": f"Found {duplicate_rows} duplicate rows ({duplicate_percentage:.2%})",
                    "metadata": {
                        "duplicate_count": duplicate_rows,
                        "duplicate_percentage": duplicate_percentage,
                        "method": "exact_match"
                    }
                })
            
            # Check for unusual value patterns in text columns
            for column in df.select_dtypes(include=['object']).columns:
                series = df[column].dropna().astype(str)
                if len(series) == 0:
                    continue
                
                # Check for unusual length patterns
                lengths = series.str.len()
                length_outliers = self._find_length_outliers(lengths)
                
                if len(length_outliers) > 0:
                    anomalies.append({
                        "type": "length_pattern_anomaly",
                        "column_name": column,
                        "severity": "medium",
                        "confidence": 0.7,
                        "description": f"Found {len(length_outliers)} values with unusual lengths in {column}",
                        "metadata": {
                            "outlier_count": len(length_outliers),
                            "method": "length_analysis",
                            "mean_length": lengths.mean(),
                            "std_length": lengths.std()
                        }
                    })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Failed to detect pattern anomalies: {e}")
            return []
    
    async def _detect_schema_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect schema-related anomalies"""
        anomalies = []
        
        try:
            # Check for unexpected data types
            for column in df.columns:
                series = df[column].dropna()
                if len(series) == 0:
                    continue
                
                # Check for mixed types in object columns
                if series.dtype == 'object':
                    # Try to identify if column should be numeric
                    numeric_count = 0
                    for value in series.head(100):  # Sample first 100 values
                        try:
                            float(value)
                            numeric_count += 1
                        except (ValueError, TypeError):
                            pass
                    
                    numeric_percentage = numeric_count / len(series.head(100))
                    
                    if 0.3 < numeric_percentage < 0.9:  # Mixed numeric/text
                        anomalies.append({
                            "type": "mixed_type_anomaly",
                            "column_name": column,
                            "severity": "medium",
                            "confidence": 0.75,
                            "description": f"Column {column} contains mixed numeric and text values",
                            "metadata": {
                                "numeric_percentage": numeric_percentage,
                                "method": "type_analysis"
                            }
                        })
                
                # Check for extreme null percentages
                null_percentage = df[column].isnull().sum() / len(df)
                if null_percentage > 0.8:
                    anomalies.append({
                        "type": "high_null_percentage",
                        "column_name": column,
                        "severity": "high",
                        "confidence": 0.9,
                        "description": f"Column {column} has {null_percentage:.1%} null values",
                        "metadata": {
                            "null_percentage": null_percentage,
                            "method": "completeness_analysis"
                        }
                    })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Failed to detect schema anomalies: {e}")
            return []
    
    def _find_length_outliers(self, lengths: pd.Series) -> List[int]:
        """Find outliers in string lengths"""
        if len(lengths) < 10:
            return []
        
        Q1 = lengths.quantile(0.25)
        Q3 = lengths.quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 2 * IQR  # More lenient for lengths
        upper_bound = Q3 + 2 * IQR
        
        outliers = lengths[(lengths < lower_bound) | (lengths > upper_bound)]
        return outliers.index.tolist()
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the ensemble detector"""
        return {
            "contamination": self.contamination,
            "random_state": self.random_state,
            "algorithms": [
                "isolation_forest",
                "statistical_outliers",
                "pattern_analysis",
                "schema_validation"
            ],
            "is_fitted": self._is_fitted,
            "version": "1.0.0"
        }
