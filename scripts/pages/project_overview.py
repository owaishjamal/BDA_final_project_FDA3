"""
Project Overview Page - Comprehensive project description and deliverables
"""
import streamlit as st

def show():
    st.title("📖 FDA-3-Stream: Project Overview")
    st.markdown("---")
    
    # Header
    st.markdown("""
    ## Real-Time Quantitative Analysis of Revenue Recognition Practices
    **Group 16** | Kafka × River × CapyMOA
    
    ---
    """)
    
    # Overall Objective
    st.header("🎯 Overall Objective")
    st.markdown("""
    To develop a real-time streaming system that analyzes revenue recognition disclosures and financial metrics 
    from SEC 10-K filings to detect aggressive accounting or inconsistent revenue practices. The system integrates:
    - **Apache Kafka** for continuous data ingestion
    - **River (Python)** for online classification and regression
    - **CapyMOA** for drift-aware adaptive pattern detection
    """)
    
    # System Architecture
    st.header("🏗️ System Architecture Overview")
    st.markdown("""
    The architecture involves three core layers:
    1. **Data Ingestion** using Kafka
    2. **Real-time Model Updates** using River and CapyMOA
    3. **Explainable Dashboards** for visualization
    
    Producers stream textual and numeric data to Kafka, consumers process features in real time, and models adapt 
    dynamically to changes in revenue recognition styles.
    """)
    
    # Architecture Diagram
    st.subheader("Architecture Flow")
    st.code("""
    Data Source (CSV/EDGAR)
         ↓
    Kafka Producer (Module 1)
         ↓
    ┌────────────┴────────────┐
    ↓                         ↓
    Text Stream          Numeric Stream
         ↓                         ↓
    River Consumers      CapyMOA Drift
    (Module 2)           (Module 3)
         ↓                         ↓
    └────────────┬────────────┘
                 ↓
         Fusion Consumer (Module 4)
                 ↓
         Alert Topic
                 ↓
         Dashboard (Module 6)
    """, language="text")
    
    # Modules
    st.header("📦 Integrated Functional Modules")
    
    modules = [
        {
            "title": "Module 1 — Streaming Extraction & Feature Generation",
            "description": "Extract 'Revenue Recognition' text from accounting policies of 10-K filings. Compute numeric ratios such as Revenue-to-CashFlow alignment ratio, Deferred Revenue/Total Revenue, and YoY Growth Rate variance. Stream these data points to Kafka topics.",
            "delivered": "✅ Kafka Producer (`kafka_producer.py`) streams revenue data with computed ratios to Kafka topics"
        },
        {
            "title": "Module 2 — Real-Time Text Classification (River)",
            "description": "Train incremental classifiers (MultinomialNB, LogisticRegression, HoeffdingTreeClassifier) using River for adaptive revenue policy classification (Aggressive, Conservative, Neutral).",
            "delivered": "✅ Enhanced Consumer implements all three classifiers with ensemble prediction and real-time metrics"
        },
        {
            "title": "Module 3 — Numeric Stream Regression & Drift Detection",
            "description": "Use River's AdaptiveRandomForestRegressor for financial ratio prediction and ADWIN for drift detection; apply CapyMOA DDM and EDDM to confirm anomalies.",
            "delivered": "✅ Regression with AdaptiveRandomForest, 5 drift detectors (ADWIN, DDM, EDDM, KSWIN, PageHinkley)"
        },
        {
            "title": "Module 4 — Cross-Platform Anomaly Fusion",
            "description": "Fuse River and CapyMOA outputs in Kafka 'revenue_alerts' topic. Flag 'High-Risk Revenue Recognition' when both detectors signal drift within one quarter.",
            "delivered": "✅ Fusion consumer combines multiple detector outputs and generates high-risk alerts"
        },
        {
            "title": "Module 5 — Explainable Streaming Analytics",
            "description": "Implement feature importance tracking with River (incremental SHAP) and CapyMOA's InformationGain evaluators to reveal linguistic or ratio-based anomaly drivers.",
            "delivered": "✅ Feature importance tracking for text and numeric features, displayed on shutdown"
        },
        {
            "title": "Module 6 — Automated Revenue Recognition Monitoring Pipeline",
            "description": "Establish continuous EDGAR → Kafka → River + CapyMOA → Dashboard pipeline with automatic retraining on drift events and periodic compliance reporting.",
            "delivered": "✅ Complete end-to-end pipeline with real-time dashboard visualization"
        }
    ]
    
    for i, module in enumerate(modules, 1):
        with st.expander(f"{module['title']}", expanded=(i <= 2)):
            st.markdown(f"**Description:** {module['description']}")
            st.markdown(f"**✅ Delivered:** {module['delivered']}")
    
    # Evaluation Metrics
    st.header("📊 Evaluation Metrics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Text Classification")
        st.markdown("""
        - **Accuracy**: ✅ Tracked in real-time
        - **F1-Score**: ✅ Tracked in real-time
        - **Confusion Matrix**: ✅ Maintained
        """)
        
        st.subheader("Regression / Ratio Analysis")
        st.markdown("""
        - **MAE (Mean Absolute Error)**: ✅ Tracked
        - **RMSE (Root Mean Squared Error)**: ✅ Tracked
        - **R² (Coefficient of Determination)**: ✅ Tracked
        """)
    
    with col2:
        st.subheader("Drift Detection")
        st.markdown("""
        - **Detection Delay**: ✅ Tracked via timestamps
        - **Frequency**: ✅ Number of detections per detector
        """)
        
        st.subheader("Streaming Efficiency")
        st.markdown("""
        - **Throughput (msg/s)**: ✅ Calculable from message counts
        - **Latency**: ✅ Tracked via timestamps
        """)
    
    st.subheader("Cross-Model Agreement")
    st.markdown("""
    - **Consensus Rate (%)**: ✅ Calculated in fusion consumer when multiple detectors agree
    """)
    
    st.subheader("Explainability")
    st.markdown("""
    - **Top-N Keyword Importance**: ✅ Tracked for text features
    - **Feature Importance**: ✅ Tracked for numeric features (rev_to_cash, deferred_ratio)
    """)
    
    # Deliverables
    st.header("✅ Deliverables Checklist")
    
    deliverables = [
        "✅ Kafka × River × CapyMOA integrated streaming pipeline (Producer → Consumer → Model → Dashboard)",
        "✅ Python Jupyter Notebooks for text extraction, preprocessing, and model training",
        "✅ CapyMOA scripts for drift-aware financial stream analysis",
        "✅ Combined dataset (revenue_patterns.csv) linking recognition methods to ratios",
        "✅ Dashboard for real-time anomaly visualization",
        "✅ Complete documentation and architecture diagrams"
    ]
    
    for item in deliverables:
        st.markdown(f"- {item}")
    
    # Technical Stack
    st.header("🛠️ Technical Stack")
    
    tech_cols = st.columns(3)
    
    with tech_cols[0]:
        st.markdown("""
        **Data Streaming:**
        - Apache Kafka
        - Kafka-Python
        """)
    
    with tech_cols[1]:
        st.markdown("""
        **Machine Learning:**
        - River (Online ML)
        - Scikit-learn
        """)
    
    with tech_cols[2]:
        st.markdown("""
        **Visualization:**
        - Streamlit
        - Pandas
        - Matplotlib
        """)
    
    # How to Run
    st.header("🚀 How to Run")
    
    st.markdown("""
    ### Prerequisites
    1. Kafka installed and running
    2. Python 3.9+ with virtual environment
    3. All dependencies installed (`pip install -r requirements.txt`)
    
    ### Quick Start
    ```bash
    # Terminal 1: Drift Detector
    python3 scripts/capy_drift.py
    
    # Terminal 2: Enhanced Consumers
    python3 scripts/kafka_consumer_river_enhanced.py
    
    # Terminal 3: Producer
    python3 scripts/kafka_producer.py --csv datasets/revenue_patterns_sample.csv --interval 1.0
    
    # Terminal 4: Dashboard
    streamlit run scripts/dashboard_app.py
    ```
    """)
    
    # Key Features
    st.header("🌟 Key Features")
    
    features = [
        "🔄 Real-time streaming processing with Kafka",
        "🤖 Multiple ML models (3 text classifiers, 2 regression models)",
        "📈 5 different drift detectors (ADWIN, DDM, EDDM, KSWIN, PageHinkley)",
        "🔗 Cross-platform fusion combining River and CapyMOA outputs",
        "📊 Feature importance tracking for explainability",
        "📉 Comprehensive evaluation metrics in real-time",
        "🎨 Interactive real-time dashboard",
        "📚 Incremental online learning"
    ]
    
    for feature in features:
        st.markdown(f"- {feature}")
    
    # Footer
    st.markdown("---")
    st.markdown("**Group 16 - FDA-3-Stream Project** | Big Data Analytics Assignment")

