"""
Pydantic models for structured data extracted from documents.
"""
from typing import List, Optional, Union
from pydantic import BaseModel, Field

class EmiratesIDData(BaseModel):
    """Data extracted from Emirates ID."""
    emirates_id: Optional[str] = Field(None, description="The Emirates ID number (format: 784-YYYY-NNNNNNN-C)")
    full_name: Optional[str] = Field(None, description="The full name of the ID holder")
    first_name: Optional[str] = Field(None, description="The first name")
    last_name: Optional[str] = Field(None, description="The last name")
    middle_name: Optional[str] = Field(None, description="The middle name if present")
    nationality: Optional[str] = Field(None, description="The nationality of the ID holder")
    date_of_birth: Optional[str] = Field(None, description="The date of birth in DD-MM-YYYY format if possible")
    gender: Optional[str] = Field(None, description="The gender/sex of the ID holder")

class BankStatementAccountInfo(BaseModel):
    """Account information from bank statements."""
    account_name: Optional[str] = Field(None, description="The name of the account holder")
    street_address: Optional[str] = Field(None, description="Address of the account holder")

class BankStatementSummary(BaseModel):
    """Summary information from bank statements."""
    opening_balance: Optional[str] = Field(None, description="The opening balance for the statement period")
    closing_balance: Optional[str] = Field(None, description="The closing balance for the statement period")
    statement_period: Optional[str] = Field(None, description="The date range for the statement")

class BankStatementTransaction(BaseModel):
    """Transaction information from bank statements."""
    date: Optional[str] = Field(None, description="Transaction date")
    description: Optional[str] = Field(None, description="Transaction description")
    amount: Optional[str] = Field(None, description="Transaction amount")
    type: Optional[str] = Field(None, description="Type of transaction: 'credit' or 'debit'")

class BankStatement(BaseModel):
    """Bank statement data."""
    account_info: Optional[BankStatementAccountInfo] = Field(None, description="Information about the account holder")
    summary: Optional[BankStatementSummary] = Field(None, description="Summary information about the statement")
    transactions: Optional[List[BankStatementTransaction]] = Field(None, description="List of transactions in the statement")

class CreditReportAccount(BaseModel):
    """Account information from credit reports."""
    account_number: Optional[str] = Field(None, description="Account identifier (may be masked)")
    account_type: Optional[str] = Field(None, description="Type of account (credit card, loan, etc.)")
    institution: Optional[str] = Field(None, description="Financial institution name")
    balance: Optional[str] = Field(None, description="Current balance")
    status: Optional[str] = Field(None, description="Account status (open, closed, etc.)")

class CreditReport(BaseModel):
    """Credit report data."""
    credit_score: Optional[int] = Field(None, description="The credit score as a number")
    accounts: Optional[List[CreditReportAccount]] = Field(None, description="Array of accounts")
    inquiries: Optional[List[str]] = Field(None, description="Array of recent credit inquiries")
    payment_history: Optional[str] = Field(None, description="Information about payment history")
    adverse_items: Optional[List[str]] = Field(None, description="Any adverse items or delinquencies")

class ResumeInfoPersonalInfo(BaseModel):
    """Personal information from resumes."""
    name: Optional[str] = Field(None, description="The full name of the individual")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    address: Optional[str] = Field(None, description="Physical address if present")

class ResumeInfoEducation(BaseModel):
    """Education information from resumes."""
    degree: Optional[str] = Field(None, description="Degree or certification")
    institution: Optional[str] = Field(None, description="School or university name")
    year: Optional[str] = Field(None, description="Year of graduation or date range")

class ResumeInfoExperience(BaseModel):
    """Work experience information from resumes."""
    title: Optional[str] = Field(None, description="Job title")
    company: Optional[str] = Field(None, description="Company name")
    duration: Optional[str] = Field(None, description="Employment period")
    description: Optional[str] = Field(None, description="Brief description of responsibilities")

class ResumeInfo(BaseModel):
    """Resume data."""
    personal_info: ResumeInfoPersonalInfo
    education: List[ResumeInfoEducation] = []
    experience: List[ResumeInfoExperience] = []
    skills: List[str] = []

class AssetLiabilityExtractionAsset(BaseModel):
    """Asset information from asset/liability statements."""
    description: str = Field(description="Description or name of the asset")
    value: float = Field(description="Monetary value of the asset")
    type: Optional[str] = Field(description="Type of asset (real estate, investment, etc.)")

class AssetLiabilityExtractionLiability(BaseModel):
    """Liability information from asset/liability statements."""
    description: str = Field(description="Description or name of the liability")
    amount: float = Field(description="Amount of the liability")
    type: Optional[str] = Field(description="Type of liability (mortgage, loan, credit card, etc.)")

class AssetLiabilityExtractionSummary(BaseModel):
    """Summary information from asset/liability statements."""
    total_assets: float = Field(description="Sum of all asset values")
    total_liabilities: float = Field(description="Sum of all liability amounts")
    net_worth: float = Field(description="Total assets minus total liabilities")

class AssetLiabilityExtraction(BaseModel):
    """Asset and liability data."""
    assets: List[AssetLiabilityExtractionAsset] = Field(description="Array of assets")
    liabilities: List[AssetLiabilityExtractionLiability] = Field(description="Array of liabilities")
    summary: AssetLiabilityExtractionSummary = Field(description="Summary of financial information")

class ValidationResultFieldValidation(BaseModel):
    """Field validation results."""
    field: str = Field(description="Name of the field being validated")
    is_valid: bool = Field(description="Whether the field's values are valid and consistent")
    source_documents: List[str] = Field(description="List of documents where the field was found")
    values_found: List[Union[str, int, float]] = Field(description="Values found across different documents")
    inconsistency_details: Optional[str] = Field(None, description="Details of any inconsistency found")
    suggested_correction: Optional[str] = Field(None, description="Suggested correction if applicable")

class ValidationResultSummary(BaseModel):
    """Validation summary."""
    overall_validation_score: float = Field(description="[score between 0-1]. Only greater than 0 when there are matches found for fields across documents. ")
    validation_summary: str = Field(description="Validation Summary")

class ValidationResult(BaseModel):
    """Validation results."""
    document_extracts_validations: List[ValidationResultFieldValidation] = Field(
        description="Validation details for each field found in the documents"
    )
    document_extracts_missing_required_fields: List[str] = Field(
        description="List of required fields that are missing from the input"
    )
    document_extracts_overall_validation: ValidationResultSummary = Field(
        description="Overall validation score and summary"
    )

class Supervisor(BaseModel):
    """Supervisor model for workflow routing."""
    next: str = Field(
        description="Next step in the workflow."
    )
    reason: str = Field(
        description="Detailed justification for the routing decision, explaining the rationale behind selecting the particular specialist and how this advances the task toward completion."
    )