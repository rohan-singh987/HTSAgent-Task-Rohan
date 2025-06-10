"""
Utility functions for the HTS AI Agent Frontend
"""
import requests
import streamlit as st
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from config import API_BASE_URL, API_TIMEOUT, COLORS

def make_api_request(endpoint: str, method: str = "GET", data: dict = None, timeout: int = API_TIMEOUT) -> Dict[str, Any]:
    """
    Make API request with comprehensive error handling
    
    Args:
        endpoint: API endpoint (without base URL)
        method: HTTP method (GET, POST, PUT, DELETE)
        data: Request payload for POST/PUT requests
        timeout: Request timeout in seconds
    
    Returns:
        Dictionary with success status and data/error
    """
    try:
        url = f"{API_BASE_URL}/{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=timeout)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=timeout)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=timeout)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers, timeout=timeout)
        else:
            return {"success": False, "error": f"Unsupported HTTP method: {method}"}
        
        response.raise_for_status()
        
        # Try to parse JSON response
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            response_data = {"message": "Success", "raw_response": response.text}
        
        return {"success": True, "data": response_data, "status_code": response.status_code}
        
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timeout - server is taking too long to respond"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Connection error - unable to reach the server"}
    except requests.exceptions.HTTPError as e:
        error_detail = f"HTTP {e.response.status_code}"
        try:
            error_json = e.response.json()
            if isinstance(error_json, dict) and "detail" in error_json:
                error_detail += f": {error_json['detail']}"
            elif isinstance(error_json, dict) and "error" in error_json:
                error_detail += f": {error_json['error']}"
        except:
            error_detail += f": {e.response.text[:200]}"
        
        return {"success": False, "error": error_detail, "status_code": e.response.status_code}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}


def format_currency(amount: float, currency: str = "USD") -> str:
    """Format currency with proper formatting"""
    if currency == "USD":
        return f"${amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"


def format_percentage(rate: float) -> str:
    """Format percentage with proper formatting"""
    return f"{rate:.2f}%"


def format_weight(weight: float, unit: str = "kg") -> str:
    """Format weight with proper unit"""
    return f"{weight:,.1f} {unit}"


def format_timestamp(timestamp: datetime) -> str:
    """Format timestamp for display"""
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")


def validate_hts_number(hts_number: str) -> Tuple[bool, str]:
    """
    Validate HTS number format
    
    Args:
        hts_number: HTS number to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not hts_number:
        return False, "HTS number cannot be empty"
    
    # Remove dots and spaces for validation
    clean_hts = hts_number.replace(".", "").replace(" ", "")
    
    # Basic length check (HTS numbers are typically 8-10 digits)
    if len(clean_hts) < 8:
        return False, "HTS number appears to be too short (minimum 8 digits)"
    
    if len(clean_hts) > 10:
        return False, "HTS number appears to be too long (maximum 10 digits)"
    
    # Check if it contains only digits and dots
    allowed_chars = set("0123456789.")
    if not all(c in allowed_chars for c in hts_number):
        return False, "HTS number should contain only digits and dots"
    
    return True, ""


def validate_country_code(country_code: str) -> Tuple[bool, str]:
    """
    Validate country code format
    
    Args:
        country_code: Country code to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not country_code:
        return False, "Country code cannot be empty"
    
    country_code = country_code.strip().upper()
    
    if len(country_code) < 2 or len(country_code) > 3:
        return False, "Country code should be 2-3 characters"
    
    if not country_code.isalpha():
        return False, "Country code should contain only letters"
    
    return True, ""


def display_api_status() -> None:
    """Display API connection status in sidebar"""
    try:
        # Check main API health
        response = requests.get(f"{API_BASE_URL.replace('/api/v1', '')}/health", timeout=5)
        if response.status_code == 200:
            st.sidebar.success("🟢 Backend Connected")
            
            # Check individual services
            health_data = response.json()
            if "services" in health_data:
                for service in health_data["services"]:
                    st.sidebar.text(f"  ✓ {service.upper()}")
        else:
            st.sidebar.warning("🟡 Backend Partial")
    except requests.exceptions.ConnectionError:
        st.sidebar.error("🔴 Backend Offline")
    except Exception:
        st.sidebar.warning("🟡 Backend Status Unknown")


def create_calculation_summary_df(calculation_data: Dict[str, Any]) -> pd.DataFrame:
    """
    Create a DataFrame from calculation data for display
    
    Args:
        calculation_data: Calculation result from API
    
    Returns:
        DataFrame with formatted calculation summary
    """
    summary_data = []
    
    # Add basic info
    summary_data.append({
        "Component": "Product Cost",
        "Value": format_currency(calculation_data["input_values"]["product_cost"]),
        "Type": "Input"
    })
    
    summary_data.append({
        "Component": "Freight",
        "Value": format_currency(calculation_data["input_values"]["freight"]),
        "Type": "Input"
    })
    
    summary_data.append({
        "Component": "Insurance",
        "Value": format_currency(calculation_data["input_values"]["insurance"]),
        "Type": "Input"
    })
    
    summary_data.append({
        "Component": "CIF Value",
        "Value": format_currency(calculation_data["summary"]["cif_value"]),
        "Type": "Calculated"
    })
    
    summary_data.append({
        "Component": "Total Duty",
        "Value": format_currency(calculation_data["summary"]["total_duty"]),
        "Type": "Calculated"
    })
    
    summary_data.append({
        "Component": "Landed Cost",
        "Value": format_currency(calculation_data["summary"]["landed_cost"]),
        "Type": "Final"
    })
    
    return pd.DataFrame(summary_data)


def create_duty_breakdown_df(duty_calculations: Dict[str, Any]) -> pd.DataFrame:
    """
    Create a DataFrame from duty calculations for display
    
    Args:
        duty_calculations: Duty calculations from API response
    
    Returns:
        DataFrame with duty breakdown
    """
    duty_data = []
    
    for duty_type, duty_info in duty_calculations.items():
        duty_data.append({
            "Duty Type": duty_type.replace('_', ' ').title(),
            "Original Rate": duty_info["original_rate"],
            "Amount": format_currency(duty_info["total_amount"]),
            "Effective Rate": format_percentage(duty_info["effective_rate"]),
            "Applicable": "✅" if duty_info["applicable"] else "❌",
            "Raw Amount": duty_info["total_amount"]  # For sorting/calculations
        })
    
    return pd.DataFrame(duty_data)


def export_calculation_to_csv(calculation_data: Dict[str, Any], filename: str = None) -> str:
    """
    Export calculation data to CSV format
    
    Args:
        calculation_data: Calculation result from API
        filename: Optional filename, generates timestamp-based name if not provided
    
    Returns:
        CSV content as string
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hts_number = calculation_data["hts_details"]["number"].replace(".", "_")
        filename = f"hts_calculation_{hts_number}_{timestamp}.csv"
    
    # Create comprehensive export data
    export_data = []
    
    # Basic information
    export_data.append(["HTS Calculation Report", ""])
    export_data.append(["Generated", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    export_data.append(["", ""])
    
    # Product details
    export_data.append(["Product Information", ""])
    export_data.append(["HTS Number", calculation_data["hts_details"]["number"]])
    export_data.append(["Description", calculation_data["hts_details"]["description"]])
    if calculation_data["hts_details"].get("unit_of_measure"):
        export_data.append(["Unit of Measure", calculation_data["hts_details"]["unit_of_measure"]])
    export_data.append(["", ""])
    
    # Input values
    export_data.append(["Input Values", ""])
    inputs = calculation_data["input_values"]
    export_data.append(["Product Cost", f"${inputs['product_cost']:,.2f}"])
    export_data.append(["Freight", f"${inputs['freight']:,.2f}"])
    export_data.append(["Insurance", f"${inputs['insurance']:,.2f}"])
    export_data.append(["Quantity", f"{inputs['quantity']} units"])
    export_data.append(["Weight", f"{inputs['weight_kg']} kg"])
    export_data.append(["Country of Origin", inputs['country_code']])
    export_data.append(["CIF Value", f"${inputs['cif_value']:,.2f}"])
    export_data.append(["", ""])
    
    # Duty calculations
    export_data.append(["Duty Calculations", ""])
    export_data.append(["Type", "Original Rate", "Amount", "Effective Rate", "Applicable"])
    
    for duty_type, duty_info in calculation_data["duty_calculations"].items():
        export_data.append([
            duty_type.replace('_', ' ').title(),
            duty_info["original_rate"],
            f"${duty_info['total_amount']:,.2f}",
            f"{duty_info['effective_rate']:.2f}%",
            "Yes" if duty_info["applicable"] else "No"
        ])
    
    export_data.append(["", ""])
    
    # Summary
    export_data.append(["Summary", ""])
    summary = calculation_data["summary"]
    export_data.append(["CIF Value", f"${summary['cif_value']:,.2f}"])
    export_data.append(["Total Duty", f"${summary['total_duty']:,.2f}"])
    export_data.append(["Landed Cost", f"${summary['landed_cost']:,.2f}"])
    export_data.append(["Effective Duty Rate", f"{summary['effective_duty_rate']:.2f}%"])
    
    # Convert to CSV string
    import io
    import csv
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(export_data)
    
    return output.getvalue()


def get_country_name(country_code: str, countries_dict: Dict[str, str]) -> str:
    """
    Get full country name from country code
    
    Args:
        country_code: Two or three letter country code
        countries_dict: Dictionary mapping codes to names
    
    Returns:
        Full country name or original code if not found
    """
    return countries_dict.get(country_code.upper(), country_code)


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to specified length with ellipsis
    
    Args:
        text: Text to truncate
        max_length: Maximum length before truncation
    
    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def display_error_message(error: str, error_type: str = "error") -> None:
    """
    Display formatted error message
    
    Args:
        error: Error message
        error_type: Type of error (error, warning, info)
    """
    if error_type == "error":
        st.error(f"❌ {error}")
    elif error_type == "warning":
        st.warning(f"⚠️ {error}")
    elif error_type == "info":
        st.info(f"ℹ️ {error}")


def display_success_message(message: str) -> None:
    """Display formatted success message"""
    st.success(f"✅ {message}")


def calculate_cost_breakdown(product_cost: float, freight: float, insurance: float, 
                           duty: float) -> Dict[str, float]:
    """
    Calculate cost breakdown percentages
    
    Args:
        product_cost: Product cost
        freight: Freight cost
        insurance: Insurance cost
        duty: Duty amount
    
    Returns:
        Dictionary with percentage breakdown
    """
    total_cost = product_cost + freight + insurance + duty
    
    if total_cost == 0:
        return {"product": 0, "freight": 0, "insurance": 0, "duty": 0}
    
    return {
        "product": (product_cost / total_cost) * 100,
        "freight": (freight / total_cost) * 100,
        "insurance": (insurance / total_cost) * 100,
        "duty": (duty / total_cost) * 100
    } 