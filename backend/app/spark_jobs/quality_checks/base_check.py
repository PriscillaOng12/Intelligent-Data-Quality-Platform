from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from app.utils.spark_utils import SparkManager
from app.schemas.quality import QualityCheck, QualityCheckType

logger = logging.getLogger(__name__)


class BaseQualityCheck(ABC):
    """Abstract base class for all quality checks"""
    
    def __init__(self, spark_manager: SparkManager):
        self.spark_manager = spark_manager
        self.spark = spark_manager.spark
    
    @abstractmethod
    async def execute(self, check: QualityCheck) -> Dict[str, Any]:
        """Execute the quality check and return results"""
        pass
    
    @abstractmethod
    def get_check_type(self) -> QualityCheckType:
        """Return the type of quality check"""
        pass
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate check parameters"""
        return True


class CompletenessCheck(BaseQualityCheck):
    """Check for data completeness (null values)"""
    
    def get_check_type(self) -> QualityCheckType:
        return QualityCheckType.COMPLETENESS
    
    async def execute(self, check: QualityCheck) -> Dict[str, Any]:
        """Execute completeness check"""
        try:
            # Load dataset
            df = await self.spark_manager.load_dataset(check.dataset_id)
            
            # Get parameters
            threshold = check.parameters.get('threshold', 0.95)
            columns = check.parameters.get('columns', df.columns)
            
            total_rows = df.count()
            results = {}
            
            for column in columns:
                null_count = df.filter(df[column].isNull()).count()
                completeness = (total_rows - null_count) / total_rows if total_rows > 0 else 0
                
                results[column] = {
                    'completeness': completeness,
                    'null_count': null_count,
                    'total_rows': total_rows,
                    'passed': completeness >= threshold
                }
            
            # Overall result
            overall_completeness = sum(r['completeness'] for r in results.values()) / len(results)
            passed = all(r['passed'] for r in results.values())
            
            return {
                'passed': passed,
                'score': overall_completeness,
                'metrics': {
                    'overall_completeness': overall_completeness,
                    'threshold': threshold,
                    'column_results': results,
                    'total_rows': total_rows
                },
                'row_count': total_rows
            }
            
        except Exception as e:
            logger.error(f"Completeness check failed: {e}")
            return {
                'passed': False,
                'score': 0.0,
                'metrics': {},
                'errors': [str(e)]
            }


class UniquenessCheck(BaseQualityCheck):
    """Check for data uniqueness (duplicate values)"""
    
    def get_check_type(self) -> QualityCheckType:
        return QualityCheckType.UNIQUENESS
    
    async def execute(self, check: QualityCheck) -> Dict[str, Any]:
        """Execute uniqueness check"""
        try:
            df = await self.spark_manager.load_dataset(check.dataset_id)
            
            threshold = check.parameters.get('threshold', 1.0)
            columns = check.parameters.get('columns', [])
            
            if not columns:
                # Check entire row uniqueness
                total_rows = df.count()
                distinct_rows = df.distinct().count()
                uniqueness = distinct_rows / total_rows if total_rows > 0 else 0
                duplicate_count = total_rows - distinct_rows
                
                results = {
                    'uniqueness': uniqueness,
                    'duplicate_count': duplicate_count,
                    'total_rows': total_rows,
                    'distinct_rows': distinct_rows,
                    'passed': uniqueness >= threshold
                }
            else:
                # Check specific columns
                results = {}
                for column in columns:
                    total_count = df.select(column).count()
                    distinct_count = df.select(column).distinct().count()
                    uniqueness = distinct_count / total_count if total_count > 0 else 0
                    
                    results[column] = {
                        'uniqueness': uniqueness,
                        'duplicate_count': total_count - distinct_count,
                        'total_count': total_count,
                        'distinct_count': distinct_count,
                        'passed': uniqueness >= threshold
                    }
            
            overall_uniqueness = results.get('uniqueness', 
                sum(r['uniqueness'] for r in results.values()) / len(results) if results else 0)
            passed = results.get('passed', all(r['passed'] for r in results.values()))
            
            return {
                'passed': passed,
                'score': overall_uniqueness,
                'metrics': {
                    'overall_uniqueness': overall_uniqueness,
                    'threshold': threshold,
                    'results': results
                },
                'row_count': df.count()
            }
            
        except Exception as e:
            logger.error(f"Uniqueness check failed: {e}")
            return {
                'passed': False,
                'score': 0.0,
                'metrics': {},
                'errors': [str(e)]
            }


class ValidityCheck(BaseQualityCheck):
    """Check for data validity (format, pattern, range)"""
    
    def get_check_type(self) -> QualityCheckType:
        return QualityCheckType.VALIDITY
    
    async def execute(self, check: QualityCheck) -> Dict[str, Any]:
        """Execute validity check"""
        try:
            df = await self.spark_manager.load_dataset(check.dataset_id)
            
            threshold = check.parameters.get('threshold', 0.95)
            rules = check.parameters.get('rules', [])
            
            results = {}
            
            for rule in rules:
                column = rule['column']
                rule_type = rule['type']
                rule_params = rule.get('params', {})
                
                if rule_type == 'range':
                    min_val = rule_params.get('min')
                    max_val = rule_params.get('max')
                    
                    total_count = df.select(column).count()
                    valid_count = df.filter(
                        (df[column] >= min_val) & (df[column] <= max_val)
                    ).count()
                    
                    validity = valid_count / total_count if total_count > 0 else 0
                    
                elif rule_type == 'regex':
                    pattern = rule_params.get('pattern')
                    
                    total_count = df.select(column).count()
                    valid_count = df.filter(
                        df[column].rlike(pattern)
                    ).count()
                    
                    validity = valid_count / total_count if total_count > 0 else 0
                
                elif rule_type == 'length':
                    min_length = rule_params.get('min_length', 0)
                    max_length = rule_params.get('max_length', float('inf'))
                    
                    from pyspark.sql.functions import length
                    
                    total_count = df.select(column).count()
                    valid_count = df.filter(
                        (length(df[column]) >= min_length) & 
                        (length(df[column]) <= max_length)
                    ).count()
                    
                    validity = valid_count / total_count if total_count > 0 else 0
                
                else:
                    validity = 0.0
                
                results[f"{column}_{rule_type}"] = {
                    'validity': validity,
                    'passed': validity >= threshold,
                    'rule': rule
                }
            
            overall_validity = sum(r['validity'] for r in results.values()) / len(results) if results else 0
            passed = all(r['passed'] for r in results.values())
            
            return {
                'passed': passed,
                'score': overall_validity,
                'metrics': {
                    'overall_validity': overall_validity,
                    'threshold': threshold,
                    'rule_results': results
                },
                'row_count': df.count()
            }
            
        except Exception as e:
            logger.error(f"Validity check failed: {e}")
            return {
                'passed': False,
                'score': 0.0,
                'metrics': {},
                'errors': [str(e)]
            }


class QualityCheckExecutor:
    """Executor for running quality checks"""
    
    def __init__(self):
        self.spark_manager = SparkManager()
        self.check_registry = {
            QualityCheckType.COMPLETENESS: CompletenessCheck(self.spark_manager),
            QualityCheckType.UNIQUENESS: UniquenessCheck(self.spark_manager),
            QualityCheckType.VALIDITY: ValidityCheck(self.spark_manager),
            # Add more check types as needed
        }
    
    async def execute_check(self, check: QualityCheck) -> Dict[str, Any]:
        """Execute a quality check"""
        try:
            check_executor = self.check_registry.get(check.check_type)
            if not check_executor:
                raise ValueError(f"Unsupported check type: {check.check_type}")
            
            logger.info(f"Executing {check.check_type} check for dataset {check.dataset_id}")
            
            result = await check_executor.execute(check)
            
            logger.info(f"Check completed: {check.check_type}, passed: {result.get('passed', False)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute quality check: {e}")
            return {
                'passed': False,
                'score': 0.0,
                'metrics': {},
                'errors': [str(e)]
            }
    
    def get_supported_check_types(self) -> List[QualityCheckType]:
        """Get list of supported quality check types"""
        return list(self.check_registry.keys())
    
    def register_check(self, check_type: QualityCheckType, check_class: BaseQualityCheck):
        """Register a new quality check type"""
        self.check_registry[check_type] = check_class
