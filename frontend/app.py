import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from typing import Dict, List, Any, Optional
import time

# Import custom modules
from config import (
    PAGE_TITLE, PAGE_ICON, LAYOUT, SAMPLE_QUESTIONS, SAMPLE_HTS_CODES,
    COMMON_COUNTRIES, DEFAULT_CALCULATION, LLM_PROVIDERS, DEFAULT_LLM_SETTINGS
)
from utils import (
    make_api_request, format_currency, format_percentage, format_weight,
    validate_hts_number, validate_country_code, display_api_status,
    create_calculation_summary_df, create_duty_breakdown_df,
    export_calculation_to_csv, get_country_name, truncate_text,
    display_error_message, display_success_message, calculate_cost_breakdown
)

# Configure page
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state="expanded"
)

# Custom CSS for modern UI
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 30px;
        color: white;
        text-align: center;
    }
    
    .agent-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .success-message {
        background: #dcfce7;
        border: 1px solid #16a34a;
        border-radius: 8px;
        padding: 12px;
        margin: 10px 0;
        color: #166534;
    }
    
    .error-message {
        background: #fef2f2;
        border: 1px solid #dc2626;
        border-radius: 8px;
        padding: 12px;
        margin: 10px 0;
        color: #991b1b;
    }
    
    .info-box {
        background: #eff6ff;
        border: 1px solid #3b82f6;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    
    .metric-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'calculation_history' not in st.session_state:
    st.session_state.calculation_history = []
if 'session_id' not in st.session_state:
    st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Helper functions are now imported from utils.py

# Main header
st.markdown("""
<div class="main-header">
    <h1>🚢 HTS AI Agent - TariffBot</h1>
    <p>Your intelligent assistant for U.S. International Trade Commission data and tariff calculations</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("🛠️ Navigation")
display_api_status()

# Main navigation
page = st.sidebar.radio(
    "Choose Your Tool:",
    ["🤖 RAG Question Answering", "📊 HTS Duty Calculator", "📈 Analytics Dashboard", "⚙️ System Status"],
    index=0
)

# RAG Question Answering Page
if page == "🤖 RAG Question Answering":
    st.header("🤖 Trade Policy & Agreement Assistant")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Chat interface
        question = st.text_area(
            "Enter your trade-related question:",
            height=100,
            placeholder="e.g., What is the United States-Israel Free Trade Agreement?"
        )
        
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
        
        with col_btn1:
            ask_button = st.button("Ask Question", type="primary")
        
        with col_btn2:
            clear_chat = st.button("Clear Chat")
        
        with col_btn3:
            clear_response = st.button("Clear Response")
        
        # Advanced settings
        with st.expander("⚙️ Advanced Settings"):
            llm_provider = st.selectbox("LLM Provider:", LLM_PROVIDERS)
            max_tokens = st.slider("Max Tokens:", 100, 4000, DEFAULT_LLM_SETTINGS["max_tokens"])
            temperature = st.slider("Temperature:", 0.0, 2.0, DEFAULT_LLM_SETTINGS["temperature"], 0.1)
        
        if clear_chat:
            st.session_state.chat_history = []
            if hasattr(st.session_state, 'latest_response'):
                del st.session_state.latest_response
            st.rerun()
        
        if clear_response:
            if hasattr(st.session_state, 'latest_response'):
                del st.session_state.latest_response
            st.rerun()
        
        if ask_button and question:
            with st.spinner("🤔 Analyzing your question..."):
                request_data = {
                    "message": question,
                    "llm_provider": llm_provider,
                    "session_id": st.session_state.session_id,
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }
                
                result = make_api_request("chat/ask", "POST", request_data)
                
                if result["success"]:
                    response_data = result["data"]
                    
                    # Store the latest response for immediate display
                    st.session_state.latest_response = {
                        "question": question,
                        "answer": response_data["response"],
                        "timestamp": datetime.now(),
                        "chunks": response_data.get("retrieved_chunks", [])
                    }
                    
                    # Add to chat history
                    st.session_state.chat_history.append(st.session_state.latest_response)
                    
                    st.rerun()
                else:
                    display_error_message(result['error'])
    
    with col2:
        st.subheader("📚 Sample Questions")
        
        for i, sample in enumerate(SAMPLE_QUESTIONS[:5]):  # Show first 5
            if st.button(f"💬 {truncate_text(sample, 50)}", key=f"sample_{i}"):
                st.session_state.temp_question = sample
                st.rerun()
        
        if hasattr(st.session_state, 'temp_question'):
            st.text_area("Selected Question:", value=st.session_state.temp_question, key="sample_display")
            del st.session_state.temp_question
    
    # Display latest response immediately
    if hasattr(st.session_state, 'latest_response'):
        latest = st.session_state.latest_response
        st.markdown("---")
        st.subheader("🤖 Latest Response")
        
        # Create a nice response card
        with st.container():
            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #0066cc; margin: 1rem 0;">
                <h4 style="color: #0066cc; margin-top: 0;">Question:</h4>
                <p style="font-size: 1.1rem; margin-bottom: 1rem;">{latest['question']}</p>
                <h4 style="color: #0066cc;">Answer:</h4>
                <div style="font-size: 1rem; line-height: 1.6;">{latest['answer']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Show source documents if available
        if latest.get('chunks'):
            with st.expander("📄 View Source Documents"):
                for j, chunk in enumerate(latest['chunks'][:3]):  # Show top 3 chunks
                    st.markdown(f"**Source {j+1}** (Similarity Score: {chunk.get('similarity_score', 'N/A')})")
                    st.text_area(
                        f"Content {j+1}:",
                        value=chunk['content'][:800] + "..." if len(chunk['content']) > 800 else chunk['content'],
                        height=100,
                        key=f"latest_chunk_{j}",
                        disabled=True
                    )
                    st.markdown("---")
    
    # Display chat history
    if st.session_state.chat_history:
        st.subheader("💬 Conversation History")
        
        for i, chat in enumerate(reversed(st.session_state.chat_history)):
            with st.expander(f"Q: {chat['question'][:60]}... ({chat['timestamp'].strftime('%H:%M:%S')})"):
                st.markdown(f"**Question:** {chat['question']}")
                st.markdown(f"**Answer:** {chat['answer']}")
                
                if chat.get('chunks'):
                    st.markdown("**📄 Source Documents:**")
                    for j, chunk in enumerate(chat['chunks'][:3]):  # Show top 3 chunks
                        with st.expander(f"Source {j+1} (Score: {chunk.get('similarity_score', 'N/A')})"):
                            st.text(chunk['content'][:500] + "..." if len(chunk['content']) > 500 else chunk['content'])

# HTS Duty Calculator Page
elif page == "📊 HTS Duty Calculator":
    st.header("📊 HTS Duty Calculator")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🔍 Product Information")
        
        # HTS Lookup section
        st.markdown("**HTS Code Lookup:**")
        search_col1, search_col2 = st.columns([3, 1])
        
        with search_col1:
            search_query = st.text_input("Search products:", placeholder="e.g., cattle, donkeys, livestock")
        
        with search_col2:
            search_button = st.button("🔍 Search")
        
        if search_button and search_query:
            with st.spinner("Searching HTS database..."):
                search_data = {"query": search_query, "limit": 10}
                result = make_api_request("tariff/search", "POST", search_data)
                
                if result["success"] and result["data"]["products"]:
                    st.markdown("**Search Results:**")
                    for product in result["data"]["products"]:
                        if st.button(f"{product['hts_number']} - {product['description'][:60]}...", key=f"hts_{product['id']}"):
                            st.session_state.selected_hts = product['hts_number']
                            st.rerun()
                else:
                    st.info("No products found. Try a different search term.")
        
        # Manual HTS input
        hts_number = st.text_input(
            "HTS Number:",
            value=st.session_state.get('selected_hts', ''),
            placeholder="e.g., 0101.30.00.00"
        )
        
        st.subheader("💰 Cost Information")
        
        col_cost1, col_cost2 = st.columns(2)
        with col_cost1:
            product_cost = st.number_input("Product Cost (USD):", min_value=0.01, value=DEFAULT_CALCULATION["product_cost"], step=100.00)
            freight = st.number_input("Freight Cost (USD):", min_value=0.0, value=DEFAULT_CALCULATION["freight"], step=50.00)
        
        with col_cost2:
            insurance = st.number_input("Insurance Cost (USD):", min_value=0.0, value=DEFAULT_CALCULATION["insurance"], step=10.00)
            # Country selector with full names
            country_options = ["Select a country..."] + [f"{code} - {name}" for code, name in COMMON_COUNTRIES.items()]
            selected_country = st.selectbox("Country of Origin:", options=country_options, index=4)  # Default to AU
            if selected_country != "Select a country...":
                country_code = selected_country.split(" - ")[0]
            else:
                country_code = st.text_input("Or enter country code:", value=DEFAULT_CALCULATION["country_code"], max_chars=3)
        
        st.subheader("📦 Quantity & Weight")
        
        col_qty1, col_qty2 = st.columns(2)
        with col_qty1:
            quantity = st.number_input("Quantity (units):", min_value=1, value=DEFAULT_CALCULATION["quantity"], step=1)
        
        with col_qty2:
            weight_kg = st.number_input("Total Weight (kg):", min_value=0.1, value=DEFAULT_CALCULATION["weight_kg"], step=10.0)
        
        # Validation and Calculate button
        col_validate, col_calculate = st.columns([1, 2])
        
        with col_validate:
            if hts_number:
                is_valid_hts, hts_error = validate_hts_number(hts_number)
                if is_valid_hts:
                    st.success("✅ Valid HTS format")
                else:
                    st.error(f"❌ {hts_error}")
        
        with col_calculate:
            if st.button("🧮 Calculate Duties", type="primary"):
                # Validate inputs
                is_valid_hts, hts_error = validate_hts_number(hts_number)
                is_valid_country, country_error = validate_country_code(country_code)
                
                if not is_valid_hts:
                    display_error_message(hts_error)
                elif not is_valid_country:
                    display_error_message(country_error)
                else:
                    with st.spinner("Calculating duties and landed costs..."):
                        calc_data = {
                            "hts_number": hts_number,
                            "product_cost": product_cost,
                            "freight": freight,
                            "insurance": insurance,
                            "quantity": quantity,
                            "weight_kg": weight_kg,
                            "country_code": country_code.upper(),
                            "session_id": st.session_state.session_id
                        }
                        
                        result = make_api_request("tariff/calculate", "POST", calc_data)
                        
                        if result["success"]:
                            st.session_state.last_calculation = result["data"]
                            st.session_state.calculation_history.append(result["data"])
                            display_success_message("Calculation completed successfully!")
                            st.rerun()
                        else:
                            display_error_message(f"Calculation Error: {result['error']}")
    
    with col2:
        st.subheader("📋 Calculation Results")
        
        if hasattr(st.session_state, 'last_calculation'):
            calc = st.session_state.last_calculation
            
            # Summary metrics
            st.markdown("### 💼 Cost Summary")
            
            metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
            
            with metrics_col1:
                st.metric(
                    "CIF Value",
                    format_currency(calc["summary"]["cif_value"]),
                    delta=None
                )
            
            with metrics_col2:
                st.metric(
                    "Total Duty",
                    format_currency(calc["summary"]["total_duty"]),
                    delta=None
                )
            
            with metrics_col3:
                st.metric(
                    "Landed Cost",
                    format_currency(calc["summary"]["landed_cost"]),
                    delta=format_currency(calc["summary"]["total_duty"])
                )
            
            # Duty breakdown
            st.markdown("### 📊 Duty Breakdown")
            
            duties_data = []
            for duty_type, duty_info in calc["duty_calculations"].items():
                if duty_info["applicable"]:
                    duties_data.append({
                        "Type": duty_type.replace('_', ' ').title(),
                        "Rate": duty_info["original_rate"],
                        "Amount": duty_info["total_amount"],
                        "Effective Rate": f"{duty_info['effective_rate']:.2f}%"
                    })
            
            if duties_data:
                df_duties = pd.DataFrame(duties_data)
                st.dataframe(df_duties, use_container_width=True)
                
                # Duty visualization
                fig = px.bar(
                    df_duties,
                    x="Type",
                    y="Amount",
                    title="Duty Breakdown by Type",
                    color="Type"
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            
            # Product details
            with st.expander("📦 Product Details"):
                st.write(f"**HTS Number:** {calc['hts_details']['number']}")
                st.write(f"**Description:** {calc['hts_details']['description']}")
                if calc['hts_details'].get('unit_of_measure'):
                    st.write(f"**Unit of Measure:** {calc['hts_details']['unit_of_measure']}")
            
            # Input values used
            with st.expander("📋 Calculation Inputs"):
                inputs = calc["input_values"]
                st.write(f"**Product Cost:** {format_currency(inputs['product_cost'])}")
                st.write(f"**Freight:** {format_currency(inputs['freight'])}")
                st.write(f"**Insurance:** {format_currency(inputs['insurance'])}")
                st.write(f"**Quantity:** {inputs['quantity']} units")
                st.write(f"**Weight:** {inputs['weight_kg']} kg")
                st.write(f"**Country:** {inputs['country_code']}")
        
        else:
            st.markdown("""
            <div class="info-box">
                <h4>📊 No calculations yet</h4>
                <p>Enter product details and click "Calculate Duties" to see results here.</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Sample calculations
        st.subheader("💡 Sample Calculations")
        
        for hts, desc in SAMPLE_HTS_CODES[:5]:  # Show first 5
            if st.button(f"🔢 {hts} - {truncate_text(desc, 40)}", key=f"sample_calc_{hts}"):
                st.session_state.selected_hts = hts
                st.rerun()
        
        # Export functionality
        if hasattr(st.session_state, 'last_calculation'):
            st.markdown("---")
            st.subheader("📄 Export Results")
            
            if st.button("📥 Download as CSV", key="export_csv"):
                csv_content = export_calculation_to_csv(st.session_state.last_calculation)
                st.download_button(
                    label="💾 Download CSV Report",
                    data=csv_content,
                    file_name=f"hts_calculation_{st.session_state.last_calculation['hts_details']['number'].replace('.', '_')}.csv",
                    mime="text/csv"
                )

# Analytics Dashboard
elif page == "📈 Analytics Dashboard":
    st.header("📈 Analytics Dashboard")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🔍 System Statistics")
        
        # Get system stats
        result = make_api_request("tariff/statistics", "GET")
        if result["success"]:
            stats = result["data"]
            
            metrics_row1 = st.columns(2)
            with metrics_row1[0]:
                st.metric("Total HTS Products", f"{stats['total_hts_products']:,}")
            with metrics_row1[1]:
                st.metric("Total Countries", stats['total_countries'])
            
            metrics_row2 = st.columns(2)
            with metrics_row2[0]:
                st.metric("Total Calculations", f"{stats['total_calculations']:,}")
            with metrics_row2[1]:
                st.metric("Recent Calculations", stats['recent_calculations'])
    
    with col2:
        st.subheader("📊 Calculation History")
        
        if st.session_state.calculation_history:
            # Create visualization of calculation history
            history_data = []
            for calc in st.session_state.calculation_history[-10:]:  # Last 10 calculations
                history_data.append({
                    "HTS Number": calc["hts_details"]["number"],
                    "CIF Value": calc["summary"]["cif_value"],
                    "Total Duty": calc["summary"]["total_duty"],
                    "Landed Cost": calc["summary"]["landed_cost"],
                    "Effective Rate": calc["summary"]["effective_duty_rate"]
                })
            
            if history_data:
                df_history = pd.DataFrame(history_data)
                
                # Bar chart of landed costs
                fig = px.bar(
                    df_history,
                    x="HTS Number",
                    y="Landed Cost",
                    title="Recent Calculation - Landed Costs",
                    text="Landed Cost"
                )
                fig.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
                
                # Table view
                st.dataframe(df_history, use_container_width=True)
        else:
            st.info("No calculations performed yet. Use the HTS Duty Calculator to generate data.")
    
    # Chat history analytics
    if st.session_state.chat_history:
        st.subheader("💬 Chat Analytics")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.metric("Total Questions Asked", len(st.session_state.chat_history))
            
            # Most recent questions
            st.markdown("**Recent Questions:**")
            for chat in st.session_state.chat_history[-5:]:
                st.write(f"• {chat['question'][:80]}...")
        
        with col2:
            # Question length distribution
            question_lengths = [len(chat['question']) for chat in st.session_state.chat_history]
            
            fig = px.histogram(
                x=question_lengths,
                title="Question Length Distribution",
                nbins=10,
                labels={'x': 'Question Length (characters)', 'y': 'Count'}
            )
            st.plotly_chart(fig, use_container_width=True)

# System Status Page
elif page == "⚙️ System Status":
    st.header("⚙️ System Status")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🔍 RAG Service Health")
        
        result = make_api_request("chat/health", "GET")
        if result["success"]:
            health_data = result["data"]
            
            if health_data["status"] == "healthy":
                st.success("✅ RAG Service is healthy")
            else:
                st.error("❌ RAG Service has issues")
            
            for service, status in health_data["services"].items():
                if status == "healthy":
                    st.success(f"✅ {service.replace('_', ' ').title()}")
                else:
                    st.error(f"❌ {service.replace('_', ' ').title()}: {status}")
        else:
            st.error(f"❌ Cannot connect to RAG service: {result['error']}")
        
        # Document processing status
        st.subheader("📄 Document Processing Status")
        
        result = make_api_request("chat/status", "GET")
        if result["success"]:
            status_data = result["data"]
            
            col_stat1, col_stat2 = st.columns(2)
            with col_stat1:
                st.metric("Documents Processed", status_data["documents_processed"])
                st.metric("Chunks Created", status_data["chunks_created"])
            
            with col_stat2:
                vector_status = "✅ Initialized" if status_data["vector_db_initialized"] else "❌ Not Initialized"
                st.write(f"**Vector DB:** {vector_status}")
                st.write(f"**Status:** {status_data['status']}")
    
    with col2:
        st.subheader("📊 Tariff Service Health")
        
        result = make_api_request("tariff/health", "GET")
        if result["success"]:
            health_data = result["data"]
            
            if health_data["status"] == "healthy":
                st.success("✅ Tariff Service is healthy")
            else:
                st.error("❌ Tariff Service has issues")
            
            if health_data["database_connected"]:
                st.success("✅ Database Connected")
            else:
                st.error("❌ Database Connection Failed")
            
            st.metric("HTS Products Loaded", f"{health_data['total_hts_products']:,}")
        else:
            st.error(f"❌ Cannot connect to Tariff service: {result['error']}")
        
        # System actions
        st.subheader("🔧 System Actions")
        
        col_action1, col_action2 = st.columns(2)
        
        with col_action1:
            if st.button("🔄 Reload Documents"):
                with st.spinner("Reloading documents..."):
                    result = make_api_request("chat/reload-documents", "POST")
                    if result["success"]:
                        st.success("✅ Documents reloaded successfully")
                    else:
                        st.error(f"❌ Error: {result['error']}")
        
        with col_action2:
            if st.button("🔄 Reload HTS Data"):
                with st.spinner("Reloading HTS data..."):
                    result = make_api_request("tariff/reload-data", "POST")
                    if result["success"]:
                        st.success("✅ HTS data reloaded successfully")
                    else:
                        st.error(f"❌ Error: {result['error']}")
    
    # Session information
    st.subheader("📱 Session Information")
    
    col_session1, col_session2, col_session3 = st.columns(3)
    
    with col_session1:
        st.write(f"**Session ID:** {st.session_state.session_id}")
    
    with col_session2:
        st.write(f"**Questions Asked:** {len(st.session_state.chat_history)}")
    
    with col_session3:
        st.write(f"**Calculations:** {len(st.session_state.calculation_history)}")
    
    # Clear session data
    if st.button("🗑️ Clear Session Data", type="secondary"):
        st.session_state.chat_history = []
        st.session_state.calculation_history = []
        st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        st.success("✅ Session data cleared")
        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6b7280; padding: 20px;">
    <p>🚢 TariffBot - Your intelligent assistant for U.S. International Trade Commission data</p>
    <p>Built with Streamlit • Powered by FastAPI • Enhanced with AI</p>
</div>
""", unsafe_allow_html=True) 